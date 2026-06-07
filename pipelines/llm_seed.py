"""Utilities for generating enzyme seed annotations with a local LLaMA model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from llama_cpp import Llama

from .manual_seeds import ManualEnzymeEntry, VALID_ACTIVITY_SEVERITIES
from .enzyme_annotations import KNOWN_ENZYMES

PROMPT_TEMPLATE = """
You are an expert clinical pharmacology assistant. Given a drug name and optional
context, produce a JSON object describing its cytochrome P450 metabolism profile.

The JSON MUST follow this structure:
{
  "compound_name": str,
  "synonyms": [str, ...],
  "identifiers": {"chembl_id": str | null},
  "enzyme_data": {
      "substrate": {
          "<enzyme>": {
              "is_substrate": true,
              "fm": float 0-1 or null,
              "source": "LLM",
              "evidence": "one sentence",
              "references": ["PMID:xxxxx" or "N/A"]
          }
      },
      "inhibition": {
          "<enzyme>": {
              "is_inhibitor": true,
              "inhibition_type": "weak|moderate|strong",
              "source": "LLM",
              "evidence": "one sentence",
              "references": ["PMID:xxxxx" or "N/A"]
          }
      },
      "induction": { ... analogous to inhibition ... }
  }
}
- Only include enzymes from this list: {enzymes}.
- Use "N/A" if you cannot find a citation.
- If unsure about fm, set it to null.
- Keep evidence sentences concise (<= 200 characters).
- Return ONLY JSON. Do not add explanations.

Drug name: {drug_name}
Context:
{context}
"""


@dataclass
class LLMSeedConfig:
    model_path: Path
    temperature: float = 0.2
    max_tokens: int = 1024
    top_p: float = 0.9
    system_prompt: str = (
        "You are a meticulous pharmacology assistant who cites evidence and respects JSON schemas."
    )


class LLMSeedGenerator:
    """Thin wrapper around llama-cpp for structured seed generation."""

    def __init__(self, config: LLMSeedConfig):
        self.config = config
        if not config.model_path.exists():
            raise FileNotFoundError(f"Model not found at {config.model_path}")
        self._client = Llama(
            model_path=str(config.model_path),
            n_ctx=4096,
            logits_all=False,
            embedding=False,
        )

    def _build_prompt(self, drug_name: str, context: str | None = None) -> str:
        rendered = PROMPT_TEMPLATE.format(
            drug_name=drug_name,
            context=context or "(no additional context)",
            enzymes=", ".join(KNOWN_ENZYMES),
        )
        return rendered

    def generate_seed_entry(self, drug_name: str, context: str | None = None) -> ManualEnzymeEntry:
        prompt = self._build_prompt(drug_name, context)
        response = self._client.create_chat_completion(
            messages=
            [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            max_tokens=self.config.max_tokens,
        )
        content = response["choices"][0]["message"]["content"].strip()
        return self._normalize_response(content, drug_name)

    def _normalize_response(self, content: str, fallback_name: str) -> ManualEnzymeEntry:
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("LLM response was not a JSON object")
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError(f"Failed to parse LLM response as JSON: {exc}\nRaw: {content[:500]}")

        data.setdefault("compound_name", fallback_name)
        data.setdefault("synonyms", [fallback_name])
        data.setdefault("identifiers", {})
        data.setdefault(
            "enzyme_data",
            {"substrate": {}, "inhibition": {}, "induction": {}},
        )

        for category in ("substrate", "inhibition", "induction"):
            enzymes = data["enzyme_data"].setdefault(category, {}) or {}
            invalid = [name for name in list(enzymes.keys()) if name not in KNOWN_ENZYMES]
            for enzyme in invalid:
                enzymes.pop(enzyme, None)

            for payload in enzymes.values():
                payload.setdefault("source", "LLM")
                payload.setdefault("references", ["N/A"])
                if category == "substrate":
                    payload["is_substrate"] = True
                    fm = payload.get("fm")
                    if fm is not None:
                        try:
                            payload["fm"] = max(0.0, min(1.0, float(fm)))
                        except Exception:
                            payload["fm"] = None
                if category == "inhibition":
                    payload["is_inhibitor"] = True
                    ity = (payload.get("inhibition_type") or "").lower()
                    if ity and ity not in VALID_ACTIVITY_SEVERITIES:
                        payload["inhibition_type"] = "moderate"
                if category == "induction":
                    payload["is_inducer"] = True
                    ity = (payload.get("induction_type") or "").lower()
                    if ity and ity not in VALID_ACTIVITY_SEVERITIES:
                        payload["induction_type"] = "moderate"

        return data  # type: ignore[return-value]
