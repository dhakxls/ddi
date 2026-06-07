"""FastAPI service exposing prediction endpoints backed by trained models."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from models.ddi_ranking.ddi_risk_model import DDIRiskRanker
from models.enzyme_prediction.dominant_enzyme_model import DominantEnzymePredictor
from models.validation_recommendation.validation_engine import (
    ValidationRecommendationEngine,
)

from .config import ServiceConfig, service_config_from_env
from .schemas import (
    CompoundInput,
    DominantEnzymeResponse,
    DrugPairInput,
    DDIRiskResponse,
    ValidationResponse,
    ValidationExperimentSchema,
)


def create_app(config: ServiceConfig | None = None) -> FastAPI:
    if config is None:
        config = service_config_from_env(default_port=8090, model_version_env="PREDICTION_MODEL_VERSION")
    app = FastAPI(
        title="DDI Prediction Service",
        version=config.model_version or "0.0.1",
        docs_url="/docs" if config.enable_docs else None,
        redoc_url="/redoc" if config.enable_docs else None,
    )

    enzyme_predictor = DominantEnzymePredictor()
    ddi_ranker = DDIRiskRanker()
    validation_engine = ValidationRecommendationEngine()

    @app.get("/healthz")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metadata")
    async def metadata() -> dict[str, str | None]:
        return {
            "model_version": config.model_version,
            "data_snapshot": None,
        }

    @app.post("/predict/enzyme", response_model=DominantEnzymeResponse)
    async def predict_dominant_enzyme(compound: CompoundInput) -> DominantEnzymeResponse:
        try:
            internal = compound.to_internal_dict()
            result = enzyme_predictor.predict_from_compound_data(internal)
            return DominantEnzymeResponse(
                compound_name=result.compound_name,
                dominant_enzymes=result.dominant_enzymes,
                overall_confidence=result.overall_confidence.value,
                enzyme_predictions=[
                    {
                        "enzyme": pred.enzyme,
                        "fraction_metabolized": pred.fraction_metabolized,
                        "is_dominant": pred.is_dominant,
                        "confidence": pred.confidence.value,
                        "evidence": pred.evidence,
                    }
                    for pred in result.enzyme_predictions
                ],
                notes=result.notes,
            )
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail=str(exc))

    @app.post("/predict/ddi", response_model=DDIRiskResponse)
    async def predict_ddi(drug_pair: DrugPairInput) -> DDIRiskResponse:
        try:
            result = ddi_ranker.rank_drug_pair(
                drug_pair.drug_a.to_internal_dict(),
                drug_pair.drug_b.to_internal_dict(),
            )
            return DDIRiskResponse(
                drug_a=result.drug_a,
                drug_b=result.drug_b,
                risk_category=result.risk_category.value,
                mechanism=result.mechanism.value,
                affected_enzymes=result.affected_enzymes,
                risk_score=result.risk_score,
                confidence=result.confidence,
                clinical_implications=result.clinical_implications,
                recommended_actions=result.recommended_actions,
            )
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail=str(exc))

    @app.post("/recommend/validation", response_model=ValidationResponse)
    async def recommend_validation(compound: CompoundInput) -> ValidationResponse:
        try:
            internal = compound.to_internal_dict()
            recommendation = validation_engine.recommend_experiments(internal)
            return ValidationResponse(
                compound_name=recommendation.compound_name,
                overall_priority=recommendation.overall_priority.value,
                summary=recommendation.summary,
                experiments=[
                    ValidationExperimentSchema(
                        experiment_type=exp.experiment_type.value,
                        priority=exp.priority.value,
                        description=exp.description,
                        rationale=exp.rationale,
                        regulatory_relevance=exp.regulatory_relevance,
                        estimated_cost=exp.estimated_cost,
                        timeline=exp.timeline,
                        success_criteria=exp.success_criteria,
                    )
                    for exp in recommendation.experiments
                ],
                regulatory_notes=recommendation.regulatory_notes,
            )
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail=str(exc))

    return app
