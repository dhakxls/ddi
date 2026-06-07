"""
Validation Experiment Recommendation Engine

Recommends appropriate validation experiments based on:
- DDI risk predictions
- Enzyme interaction profiles
- Regulatory requirements
- Clinical trial stage
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ExperimentType(Enum):
    """Types of validation experiments."""
    IN_VITRO_INHIBITION = "in_vitro_inhibition"
    IN_VITRO_INDUCTION = "in_vitro_induction"
    IN_VITRO_METABOLISM = "in_vitro_metabolism"
    CLINICAL_DDI = "clinical_ddi"
    TDM = "therapeutic_drug_monitoring"
    PHENOTYPING = "phenotyping"
    PBPK_MODELING = "pbpk_modeling"


class Priority(Enum):
    """Priority levels for experiments."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ValidationExperiment:
    """Recommended validation experiment."""
    experiment_type: ExperimentType
    priority: Priority
    description: str
    rationale: str
    regulatory_relevance: str
    estimated_cost: str
    timeline: str
    success_criteria: List[str]


@dataclass
class ValidationRecommendation:
    """Complete validation recommendation set."""
    compound_name: str
    overall_priority: Priority
    experiments: List[ValidationExperiment]
    summary: str
    regulatory_notes: List[str]


class ValidationRecommendationEngine:
    """
    Engine for recommending validation experiments based on DDI risk assessment.
    """
    
    def __init__(self):
        """Initialize the engine."""
        pass
    
    def recommend_experiments(
        self,
        compound_data: dict,
        ddi_predictions: Optional[List[dict]] = None
    ) -> ValidationRecommendation:
        """
        Recommend validation experiments for a compound.
        
        Args:
            compound_data: Compound data dictionary
            ddi_predictions: Optional list of DDI predictions with other drugs
        
        Returns:
            ValidationRecommendation with experiment recommendations
        """
        compound_name = compound_data.get("compound_name", "Unknown")
        experiments = []
        
        # Analyze enzyme profile
        enzyme_profile = self._analyze_enzyme_profile(compound_data)
        
        # Analyze DDI risk if predictions provided
        ddi_risk_profile = self._analyze_ddi_risk(ddi_predictions) if ddi_predictions else None
        
        # Generate recommendations based on profile
        experiments.extend(self._recommend_in_vitro_experiments(enzyme_profile))
        experiments.extend(self._recommend_clinical_experiments(enzyme_profile, ddi_risk_profile))
        experiments.extend(self._recommend_regulatory_experiments(enzyme_profile, ddi_risk_profile))
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        experiments.sort(key=lambda x: priority_order[x.priority.value])
        
        # Determine overall priority
        overall_priority = self._determine_overall_priority(experiments)
        
        # Generate summary
        summary = self._generate_summary(enzyme_profile, ddi_risk_profile, experiments)
        
        # Generate regulatory notes
        regulatory_notes = self._generate_regulatory_notes(enzyme_profile, ddi_risk_profile)
        
        return ValidationRecommendation(
            compound_name=compound_name,
            overall_priority=overall_priority,
            experiments=experiments,
            summary=summary,
            regulatory_notes=regulatory_notes
        )
    
    def _analyze_enzyme_profile(self, compound_data: dict) -> dict:
        """Analyze the enzyme interaction profile of a compound."""
        enzyme_data = compound_data.get("enzyme_data", {})
        
        profile = {
            "substrate_enzymes": [],
            "inhibited_enzymes": [],
            "induced_enzymes": [],
            "dominant_enzymes": [],
            "high_risk_enzymes": []
        }
        
        substrate_data = enzyme_data.get("substrate", {})
        inhibition_data = enzyme_data.get("inhibition", {})
        induction_data = enzyme_data.get("induction", {})
        
        # Analyze substrate profile
        for enzyme, data in substrate_data.items():
            if data.get("is_substrate", False):
                profile["substrate_enzymes"].append(enzyme)
                fm = data.get("fm", 0)
                if fm >= 0.25:
                    profile["dominant_enzymes"].append(enzyme)
                if "CYP3A" in enzyme:
                    profile["high_risk_enzymes"].append(enzyme)
        
        # Analyze inhibition profile
        for enzyme, data in inhibition_data.items():
            if data.get("is_inhibitor", False):
                inhibition_type = data.get("inhibition_type", "weak")
                profile["inhibited_enzymes"].append((enzyme, inhibition_type))
                if inhibition_type in ["strong", "moderate"] or "CYP3A" in enzyme:
                    profile["high_risk_enzymes"].append(enzyme)
        
        # Analyze induction profile
        for enzyme, data in induction_data.items():
            if data.get("is_inducer", False):
                induction_type = data.get("induction_type", "weak")
                profile["induced_enzymes"].append((enzyme, induction_type))
                if induction_type in ["strong", "moderate"] or "CYP3A" in enzyme:
                    profile["high_risk_enzymes"].append(enzyme)
        
        return profile
    
    def _analyze_ddi_risk(self, ddi_predictions: List[dict]) -> dict:
        """Analyze DDI risk profile from predictions."""
        if not ddi_predictions:
            return {}
        
        risk_profile = {
            "high_risk_count": 0,
            "moderate_risk_count": 0,
            "contraindicated_count": 0,
            "mechanisms": set(),
            "affected_enzymes": set()
        }
        
        for prediction in ddi_predictions:
            risk_category = prediction.get("risk_category", "unknown")
            if risk_category == "contraindicated":
                risk_profile["contraindicated_count"] += 1
            elif risk_category == "major":
                risk_profile["high_risk_count"] += 1
            elif risk_category == "moderate":
                risk_profile["moderate_risk_count"] += 1
            
            mechanism = prediction.get("mechanism")
            if mechanism:
                risk_profile["mechanisms"].add(mechanism)
            
            affected_enzymes = prediction.get("affected_enzymes", [])
            risk_profile["affected_enzymes"].update(affected_enzymes)
        
        risk_profile["mechanisms"] = list(risk_profile["mechanisms"])
        risk_profile["affected_enzymes"] = list(risk_profile["affected_enzymes"])
        
        return risk_profile
    
    def _recommend_in_vitro_experiments(self, enzyme_profile: dict) -> List[ValidationExperiment]:
        """Recommend in vitro validation experiments."""
        experiments = []
        
        # In vitro inhibition assays
        if enzyme_profile["inhibited_enzymes"]:
            for enzyme, inhibition_type in enzyme_profile["inhibited_enzymes"]:
                priority = Priority.CRITICAL if inhibition_type == "strong" else Priority.HIGH
                experiments.append(ValidationExperiment(
                    experiment_type=ExperimentType.IN_VITRO_INHIBITION,
                    priority=priority,
                    description=f"{enzyme} inhibition assay (IC50/Ki determination)",
                    rationale=f"Compound identified as {inhibition_type} {enzyme} inhibitor",
                    regulatory_relevance="FDA/EMA require IC50 values for inhibitors",
                    estimated_cost="$5,000 - $15,000 per enzyme",
                    timeline="4-8 weeks",
                    success_criteria=[
                        "IC50 < 10 μM for strong inhibitors",
                        "IC50 < 50 μM for moderate inhibitors",
                        "Reversible vs irreversible mechanism determined",
                        "Time-dependent inhibition assessed if relevant"
                    ]
                ))
        
        # In vitro induction assays
        if enzyme_profile["induced_enzymes"]:
            for enzyme, induction_type in enzyme_profile["induced_enzymes"]:
                priority = Priority.CRITICAL if induction_type == "strong" else Priority.HIGH
                experiments.append(ValidationExperiment(
                    experiment_type=ExperimentType.IN_VITRO_INDUCTION,
                    priority=priority,
                    description=f"{enzyme} induction assay (mRNA and protein expression)",
                    rationale=f"Compound identified as {induction_type} {enzyme} inducer",
                    regulatory_relevance="FDA/EMA require induction data for inducers",
                    estimated_cost="$10,000 - $25,000 per enzyme",
                    timeline="6-10 weeks",
                    success_criteria=[
                        ">2-fold mRNA increase for inducers",
                        "Dose-response relationship established",
                        "Cytotoxicity assessed",
                        "Positive and negative controls included"
                    ]
                ))
        
        # In vitro metabolism studies
        if enzyme_profile["substrate_enzymes"]:
            priority = Priority.HIGH if enzyme_profile["dominant_enzymes"] else Priority.MEDIUM
            experiments.append(ValidationExperiment(
                experiment_type=ExperimentType.IN_VITRO_METABOLISM,
                priority=priority,
                description="Reaction phenotyping with recombinant CYP enzymes",
                rationale=f"Compound is substrate for {len(enzyme_profile['substrate_enzymes'])} CYP enzymes",
                regulatory_relevance="Required for understanding metabolic pathways",
                estimated_cost="$15,000 - $30,000",
                timeline="8-12 weeks",
                success_criteria=[
                    "Fraction metabolized (fm) determined for each enzyme",
                    "Correlation with human liver microsomes",
                    "Major metabolites identified",
                    "Kinetic parameters (Km, Vmax) determined"
                ]
            ))
        
        return experiments
    
    def _recommend_clinical_experiments(
        self,
        enzyme_profile: dict,
        ddi_risk_profile: Optional[dict]
    ) -> List[ValidationExperiment]:
        """Recommend clinical validation experiments."""
        experiments = []
        
        # Clinical DDI studies
        high_risk = False
        if ddi_risk_profile:
            high_risk = (
                ddi_risk_profile.get("contraindicated_count", 0) > 0 or
                ddi_risk_profile.get("high_risk_count", 0) > 0
            )
        
        if high_risk or enzyme_profile["dominant_enzymes"]:
            priority = Priority.CRITICAL if high_risk else Priority.HIGH
            experiments.append(ValidationExperiment(
                experiment_type=ExperimentType.CLINICAL_DDI,
                priority=priority,
                description="Clinical drug-drug interaction study",
                rationale="High DDI risk potential identified",
                regulatory_relevance="Required for co-administered drugs",
                estimated_cost="$500,000 - $2,000,000",
                timeline="6-12 months",
                success_criteria=[
                    "AUC ratio within 0.8-1.25 for no interaction",
                    "Cmax ratio within 0.8-1.25 for no interaction",
                    "Safety and tolerability assessed",
                    "Pharmacokinetic parameters characterized"
                ]
            ))
        
        # Therapeutic drug monitoring
        if enzyme_profile["dominant_enzymes"]:
            experiments.append(ValidationExperiment(
                experiment_type=ExperimentType.TDM,
                priority=Priority.MEDIUM,
                description="Therapeutic drug monitoring protocol development",
                rationale=f"Narrow therapeutic index likely with {', '.join(enzyme_profile['dominant_enzymes'])} metabolism",
                regulatory_relevance="Recommended for drugs with narrow therapeutic index",
                estimated_cost="$50,000 - $100,000",
                timeline="3-6 months",
                success_criteria=[
                    "Assay validation completed",
                    "Reference range established",
                    "Sampling schedule defined",
                    "Clinical decision support integrated"
                ]
            ))
        
        return experiments
    
    def _recommend_regulatory_experiments(
        self,
        enzyme_profile: dict,
        ddi_risk_profile: Optional[dict]
    ) -> List[ValidationExperiment]:
        """Recommend regulatory-focused experiments."""
        experiments = []
        
        # Phenotyping studies
        if enzyme_profile["substrate_enzymes"]:
            polymorphic_enzymes = [e for e in enzyme_profile["substrate_enzymes"] 
                                 if e in ["CYP2D6", "CYP2C9", "CYP2C19"]]
            if polymorphic_enzymes:
                experiments.append(ValidationExperiment(
                    experiment_type=ExperimentType.PHENOTYPING,
                    priority=Priority.HIGH,
                    description=f"Phenotyping study for {', '.join(polymorphic_enzymes)}",
                    rationale=f"Polymorphic enzymes involved in metabolism",
                    regulatory_relevance="Required for drugs metabolized by polymorphic enzymes",
                    estimated_cost="$100,000 - $300,000",
                    timeline="6-9 months",
                    success_criteria=[
                        "Poor vs extensive metabolizer comparison",
                        "Genotype-phenotype correlation",
                        "Dose adjustment recommendations",
                        "Labeling implications determined"
                    ]
                ))
        
        # PBPK modeling
        if enzyme_profile["high_risk_enzymes"]:
            experiments.append(ValidationExperiment(
                experiment_type=ExperimentType.PBPK_MODELING,
                priority=Priority.MEDIUM,
                description="Physiologically-based pharmacokinetic (PBPK) model development",
                rationale=f"High-risk enzyme profile ({', '.join(set(enzyme_profile['high_risk_enzymes']))})",
                regulatory_relevance="Accepted by FDA/EMA for DDI predictions",
                estimated_cost="$150,000 - $400,000",
                timeline="4-8 months",
                success_criteria=[
                    "Model validated against clinical data",
                    "DDI predictions match observed data",
                    "Sensitivity analysis completed",
                    "Regulatory submission package prepared"
                ]
            ))
        
        return experiments
    
    def _determine_overall_priority(self, experiments: List[ValidationExperiment]) -> Priority:
        """Determine overall priority from experiment list."""
        if any(e.priority == Priority.CRITICAL for e in experiments):
            return Priority.CRITICAL
        elif any(e.priority == Priority.HIGH for e in experiments):
            return Priority.HIGH
        elif any(e.priority == Priority.MEDIUM for e in experiments):
            return Priority.MEDIUM
        else:
            return Priority.LOW
    
    def _generate_summary(
        self,
        enzyme_profile: dict,
        ddi_risk_profile: Optional[dict],
        experiments: List[ValidationExperiment]
    ) -> str:
        """Generate a summary of recommendations."""
        summary_parts = []
        
        summary_parts.append(
            f"Based on enzyme profile analysis, {len(experiments)} validation experiments are recommended."
        )
        
        if enzyme_profile["dominant_enzymes"]:
            summary_parts.append(
                f"Compound is primarily metabolized by {', '.join(enzyme_profile['dominant_enzymes'])}."
            )
        
        if enzyme_profile["inhibited_enzymes"]:
            inhibited = [f"{e} ({t})" for e, t in enzyme_profile["inhibited_enzymes"]]
            summary_parts.append(f"Inhibits {', '.join(inhibited)}.")
        
        if enzyme_profile["induced_enzymes"]:
            induced = [f"{e} ({t})" for e, t in enzyme_profile["induced_enzymes"]]
            summary_parts.append(f"Induces {', '.join(induced)}.")
        
        if ddi_risk_profile:
            high_risk = ddi_risk_profile.get("high_risk_count", 0) + ddi_risk_profile.get("contraindicated_count", 0)
            if high_risk > 0:
                summary_parts.append(f"{high_risk} high-risk DDI predictions require clinical validation.")
        
        critical_count = sum(1 for e in experiments if e.priority == Priority.CRITICAL)
        if critical_count > 0:
            summary_parts.append(f"{critical_count} critical experiments should be prioritized.")
        
        return " ".join(summary_parts)
    
    def _generate_regulatory_notes(
        self,
        enzyme_profile: dict,
        ddi_risk_profile: Optional[dict]
    ) -> List[str]:
        """Generate regulatory notes."""
        notes = []
        
        notes.append("FDA Guidance: Drug Interaction Studies (2020)")
        notes.append("EMA Guideline on the Investigation of Drug Interactions (2012)")
        
        if enzyme_profile["dominant_enzymes"]:
            notes.append(
                "FDA requires fm determination for major metabolic pathways (>25% of metabolism)"
            )
        
        if enzyme_profile["inhibited_enzymes"]:
            strong_inhibitors = [e for e, t in enzyme_profile["inhibited_enzymes"] if t == "strong"]
            if strong_inhibitors:
                notes.append(
                    f"Strong inhibitors of {', '.join(strong_inhibitors)} require clinical DDI studies"
                )
        
        if enzyme_profile["induced_enzymes"]:
            strong_inducers = [e for e, t in enzyme_profile["induced_enzymes"] if t == "strong"]
            if strong_inducers:
                notes.append(
                    f"Strong inducers of {', '.join(strong_inducers)} require clinical DDI studies"
                )
        
        if "CYP3A4" in enzyme_profile["high_risk_enzymes"]:
            notes.append("CYP3A4 interactions have high regulatory scrutiny due to broad substrate specificity")
        
        return notes


def create_example_recommendation():
    """Create an example recommendation for testing."""
    engine = ValidationRecommendationEngine()
    
    # Example compound: Warfarin-like
    # Note: fm values set to None - requires sourced data for accurate validation
    compound_data = {
        "compound_name": "Example Compound",
        "enzyme_data": {
            "substrate": {
                "CYP2C9": {"is_substrate": True, "fm": None},
                "CYP1A2": {"is_substrate": True, "fm": None}
            },
            "inhibition": {},
            "induction": {}
        }
    }
    
    # Example DDI predictions
    ddi_predictions = [
        {
            "risk_category": "major",
            "mechanism": "inhibition",
            "affected_enzymes": ["CYP2C9"]
        }
    ]
    
    result = engine.recommend_experiments(compound_data, ddi_predictions)
    return result


if __name__ == "__main__":
    # Test the engine
    result = create_example_recommendation()
    
    print(f"Compound: {result.compound_name}")
    print(f"Overall Priority: {result.overall_priority.value}")
    print(f"\nSummary: {result.summary}")
    print(f"\nExperiments ({len(result.experiments)}):")
    for exp in result.experiments:
        print(f"\n  [{exp.priority.value.upper()}] {exp.description}")
        print(f"  Rationale: {exp.rationale}")
        print(f"  Cost: {exp.estimated_cost}, Timeline: {exp.timeline}")
    
    print(f"\nRegulatory Notes:")
    for note in result.regulatory_notes:
        print(f"  - {note}")
