"""Pydantic schemas shared across DDI services."""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class EnzymeData(BaseModel):
    is_substrate: bool = False
    km_um: Optional[float] = None
    vmax: Optional[float] = None
    clint: Optional[float] = None
    fm: Optional[float] = None
    source: str = ""


class InhibitionData(BaseModel):
    is_inhibitor: bool = False
    inhibition_type: Optional[str] = None
    ic50_um: Optional[float] = None
    ki_um: Optional[float] = None
    source: str = ""


class InductionData(BaseModel):
    is_inducer: bool = False
    induction_type: Optional[str] = None
    fold_change: Optional[float] = None
    source: str = ""


class CompoundInput(BaseModel):
    compound_name: str
    substrate_data: Dict[str, EnzymeData] = Field(default_factory=dict)
    inhibition_data: Dict[str, InhibitionData] = Field(default_factory=dict)
    induction_data: Dict[str, InductionData] = Field(default_factory=dict)

    def to_internal_dict(self) -> Dict:
        return {
            "compound_name": self.compound_name,
            "enzyme_data": {
                "substrate": {k: v.model_dump() for k, v in self.substrate_data.items()},
                "inhibition": {k: v.model_dump() for k, v in self.inhibition_data.items()},
                "induction": {k: v.model_dump() for k, v in self.induction_data.items()},
            },
        }


class DrugPairInput(BaseModel):
    drug_a: CompoundInput
    drug_b: CompoundInput


class EnzymePredictionSchema(BaseModel):
    enzyme: str
    fraction_metabolized: Optional[float]
    is_dominant: bool
    confidence: str
    evidence: List[str]


class DominantEnzymeResponse(BaseModel):
    compound_name: str
    dominant_enzymes: List[str]
    overall_confidence: str
    enzyme_predictions: List[EnzymePredictionSchema]
    notes: List[str]


class DDIRiskResponse(BaseModel):
    drug_a: str
    drug_b: str
    risk_category: str
    mechanism: str
    affected_enzymes: List[str]
    risk_score: float
    confidence: str
    clinical_implications: List[str]
    recommended_actions: List[str]


class ValidationExperimentSchema(BaseModel):
    experiment_type: str
    priority: str
    description: str
    rationale: str
    regulatory_relevance: str
    estimated_cost: str
    timeline: str
    success_criteria: List[str]


class ValidationResponse(BaseModel):
    compound_name: str
    overall_priority: str
    summary: str
    experiments: List[ValidationExperimentSchema]
    regulatory_notes: List[str]
