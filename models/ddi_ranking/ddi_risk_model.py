"""
DDI Risk Ranking Model

Baseline model for ranking drug-drug interaction risk based on enzyme profiles.
Considers substrate/inhibitor/inducer relationships to predict DDI potential.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class DDICategory(Enum):
    """DDI risk categories."""
    CONTRAINDICATED = "contraindicated"
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"
    UNKNOWN = "unknown"


class Mechanism(Enum):
    """DDI mechanism types."""
    INHIBITION = "inhibition"
    INDUCTION = "induction"
    COMPETITIVE_SUBSTRATE = "competitive_substrate"
    MIXED = "mixed"


@dataclass
class DDIPrediction:
    """Prediction for a single drug pair."""
    drug_a: str
    drug_b: str
    risk_category: DDICategory
    mechanism: Mechanism
    affected_enzymes: List[str]
    risk_score: float  # 0-100
    confidence: str
    clinical_implications: List[str]
    recommended_actions: List[str]


@dataclass
class EnzymeInteraction:
    """Interaction at the enzyme level."""
    enzyme: str
    drug_a_role: str  # substrate, inhibitor, inducer
    drug_b_role: str  # substrate, inhibitor, inducer
    interaction_type: str  # inhibition, induction, competition
    severity: str  # strong, moderate, weak


class DDIRiskRanker:
    """
    Baseline DDI risk ranking model.
    
    Evaluates drug pairs based on their enzyme interaction profiles
    to predict DDI risk and recommend actions.
    """
    
    ENZYMES = [
        "CYP1A2", "CYP2B6", "CYP2C8", "CYP2C9", 
        "CYP2C19", "CYP2D6", "CYP2E1", "CYP3A4", "CYP3A5"
    ]
    
    # Risk scoring weights
    STRONG_INHIBITION_WEIGHT = 40
    MODERATE_INHIBITION_WEIGHT = 25
    WEAK_INHIBITION_WEIGHT = 10
    
    STRONG_INDUCTION_WEIGHT = 35
    MODERATE_INDUCTION_WEIGHT = 20
    WEAK_INDUCTION_WEIGHT = 10
    
    COMPETITION_WEIGHT = 15
    CYP3A_MULTIPLIER = 1.3  # CYP3A interactions are higher risk
    
    # Thresholds for risk categories
    CONTRAINDICATED_THRESHOLD = 75
    MAJOR_THRESHOLD = 50
    MODERATE_THRESHOLD = 25
    
    def __init__(self):
        """Initialize the ranker."""
        pass
    
    def rank_drug_pair(
        self, 
        drug_a_data: dict, 
        drug_b_data: dict
    ) -> DDIPrediction:
        """
        Rank DDI risk for a drug pair.
        
        Args:
            drug_a_data: Compound data for drug A
            drug_b_data: Compound data for drug B
        
        Returns:
            DDIPrediction with risk assessment
        """
        drug_a_name = drug_a_data.get("compound_name", "Drug A")
        drug_b_name = drug_b_data.get("compound_name", "Drug B")
        
        # Identify enzyme-level interactions
        enzyme_interactions = self._identify_enzyme_interactions(
            drug_a_data, drug_b_data
        )
        
        # Calculate risk score
        risk_score, mechanism = self._calculate_risk_score(
            enzyme_interactions
        )
        
        # Determine risk category
        risk_category = self._determine_risk_category(risk_score)
        
        # Extract affected enzymes
        affected_enzymes = [ei.enzyme for ei in enzyme_interactions]
        
        # Determine confidence
        confidence = self._determine_confidence(enzyme_interactions)
        
        # Generate clinical implications
        clinical_implications = self._generate_clinical_implications(
            enzyme_interactions, mechanism, risk_category
        )
        
        # Generate recommended actions
        recommended_actions = self._generate_recommendations(
            risk_category, enzyme_interactions
        )
        
        return DDIPrediction(
            drug_a=drug_a_name,
            drug_b=drug_b_name,
            risk_category=risk_category,
            mechanism=mechanism,
            affected_enzymes=affected_enzymes,
            risk_score=risk_score,
            confidence=confidence,
            clinical_implications=clinical_implications,
            recommended_actions=recommended_actions
        )
    
    def _identify_enzyme_interactions(
        self,
        drug_a_data: dict,
        drug_b_data: dict
    ) -> List[EnzymeInteraction]:
        """Identify enzyme-level interactions between two drugs."""
        interactions = []
        
        enzyme_data_a = drug_a_data.get("enzyme_data", {})
        enzyme_data_b = drug_b_data.get("enzyme_data", {})
        
        for enzyme in self.ENZYMES:
            substrate_a = enzyme_data_a.get("substrate", {}).get(enzyme, {})
            substrate_b = enzyme_data_b.get("substrate", {}).get(enzyme, {})
            inhibition_a = enzyme_data_a.get("inhibition", {}).get(enzyme, {})
            inhibition_b = enzyme_data_b.get("inhibition", {}).get(enzyme, {})
            induction_a = enzyme_data_a.get("induction", {}).get(enzyme, {})
            induction_b = enzyme_data_b.get("induction", {}).get(enzyme, {})
            
            # Check for inhibition interactions
            if substrate_a.get("is_substrate", False) and inhibition_b.get("is_inhibitor", False):
                severity = inhibition_b.get("inhibition_type", "weak")
                interactions.append(EnzymeInteraction(
                    enzyme=enzyme,
                    drug_a_role="substrate",
                    drug_b_role="inhibitor",
                    interaction_type="inhibition",
                    severity=severity
                ))
            
            if substrate_b.get("is_substrate", False) and inhibition_a.get("is_inhibitor", False):
                severity = inhibition_a.get("inhibition_type", "weak")
                interactions.append(EnzymeInteraction(
                    enzyme=enzyme,
                    drug_a_role="inhibitor",
                    drug_b_role="substrate",
                    interaction_type="inhibition",
                    severity=severity
                ))
            
            # Check for induction interactions
            if substrate_a.get("is_substrate", False) and induction_b.get("is_inducer", False):
                severity = induction_b.get("induction_type", "weak")
                interactions.append(EnzymeInteraction(
                    enzyme=enzyme,
                    drug_a_role="substrate",
                    drug_b_role="inducer",
                    interaction_type="induction",
                    severity=severity
                ))
            
            if substrate_b.get("is_substrate", False) and induction_a.get("is_inducer", False):
                severity = induction_a.get("induction_type", "weak")
                interactions.append(EnzymeInteraction(
                    enzyme=enzyme,
                    drug_a_role="inducer",
                    drug_b_role="substrate",
                    interaction_type="induction",
                    severity=severity
                ))
            
            # Check for competitive substrate interactions
            if (substrate_a.get("is_substrate", False) and 
                substrate_b.get("is_substrate", False)):
                # Only flag if both have significant fm
                fm_a = substrate_a.get("fm", 0)
                fm_b = substrate_b.get("fm", 0)
                if fm_a > 0.1 and fm_b > 0.1:
                    interactions.append(EnzymeInteraction(
                        enzyme=enzyme,
                        drug_a_role="substrate",
                        drug_b_role="substrate",
                        interaction_type="competition",
                        severity="moderate"
                    ))
        
        return interactions
    
    def _calculate_risk_score(
        self,
        enzyme_interactions: List[EnzymeInteraction]
    ) -> Tuple[float, Mechanism]:
        """Calculate overall risk score from enzyme interactions."""
        if not enzyme_interactions:
            return 0.0, Mechanism.COMPETITIVE_SUBSTRATE
        
        total_score = 0.0
        has_inhibition = False
        has_induction = False
        has_competition = False
        
        for interaction in enzyme_interactions:
            base_score = 0.0
            
            # Apply CYP3A multiplier
            multiplier = self.CYP3A_MULTIPLIER if "CYP3A" in interaction.enzyme else 1.0
            
            if interaction.interaction_type == "inhibition":
                has_inhibition = True
                if interaction.severity == "strong":
                    base_score = self.STRONG_INHIBITION_WEIGHT
                elif interaction.severity == "moderate":
                    base_score = self.MODERATE_INHIBITION_WEIGHT
                else:
                    base_score = self.WEAK_INHIBITION_WEIGHT
            
            elif interaction.interaction_type == "induction":
                has_induction = True
                if interaction.severity == "strong":
                    base_score = self.STRONG_INDUCTION_WEIGHT
                elif interaction.severity == "moderate":
                    base_score = self.MODERATE_INDUCTION_WEIGHT
                else:
                    base_score = self.WEAK_INDUCTION_WEIGHT
            
            elif interaction.interaction_type == "competition":
                has_competition = True
                base_score = self.COMPETITION_WEIGHT
            
            total_score += base_score * multiplier
        
        # Cap score at 100
        total_score = min(total_score, 100.0)
        
        # Determine mechanism
        if has_inhibition and has_induction:
            mechanism = Mechanism.MIXED
        elif has_inhibition:
            mechanism = Mechanism.INHIBITION
        elif has_induction:
            mechanism = Mechanism.INDUCTION
        else:
            mechanism = Mechanism.COMPETITIVE_SUBSTRATE
        
        return total_score, mechanism
    
    def _determine_risk_category(self, risk_score: float) -> DDICategory:
        """Determine risk category from risk score."""
        if risk_score >= self.CONTRAINDICATED_THRESHOLD:
            return DDICategory.CONTRAINDICATED
        elif risk_score >= self.MAJOR_THRESHOLD:
            return DDICategory.MAJOR
        elif risk_score >= self.MODERATE_THRESHOLD:
            return DDICategory.MODERATE
        elif risk_score > 0:
            return DDICategory.MINOR
        else:
            return DDICategory.UNKNOWN
    
    def _determine_confidence(self, enzyme_interactions: List[EnzymeInteraction]) -> str:
        """Determine confidence level of prediction."""
        if not enzyme_interactions:
            return "low"
        
        # Count strong/moderate interactions
        strong_count = sum(1 for ei in enzyme_interactions if ei.severity == "strong")
        moderate_count = sum(1 for ei in enzyme_interactions if ei.severity == "moderate")
        
        if strong_count > 0:
            return "high"
        elif moderate_count > 0:
            return "medium"
        else:
            return "low"
    
    def _generate_clinical_implications(
        self,
        enzyme_interactions: List[EnzymeInteraction],
        mechanism: Mechanism,
        risk_category: DDICategory
    ) -> List[str]:
        """Generate clinical implications based on interactions."""
        implications = []
        
        if risk_category == DDICategory.CONTRAINDICATED:
            implications.append("Contraindicated - do not co-administer")
            implications.append("Risk of serious or life-threatening adverse events")
        
        elif risk_category == DDICategory.MAJOR:
            implications.append("Significant interaction expected")
            implications.append("Therapeutic drug monitoring recommended")
            implications.append("Dose adjustment may be required")
        
        elif risk_category == DDICategory.MODERATE:
            implications.append("Potential interaction may occur")
            implications.append("Monitor for clinical effects")
            implications.append("Consider dose adjustment if needed")
        
        elif risk_category == DDICategory.MINOR:
            implications.append("Minimal clinical significance expected")
            implications.append("Routine monitoring sufficient")
        
        # Mechanism-specific implications
        if mechanism == Mechanism.INHIBITION:
            implications.append("Inhibition may increase substrate drug concentrations")
        elif mechanism == Mechanism.INDUCTION:
            implications.append("Induction may decrease substrate drug concentrations")
        elif mechanism == Mechanism.COMPETITIVE_SUBSTRATE:
            implications.append("Competition for metabolism may affect both drugs")
        
        # Enzyme-specific implications
        cyp3a_involved = any("CYP3A" in ei.enzyme for ei in enzyme_interactions)
        if cyp3a_involved:
            implications.append("CYP3A involvement - high interindividual variability")
        
        return implications
    
    def _generate_recommendations(
        self,
        risk_category: DDICategory,
        enzyme_interactions: List[EnzymeInteraction]
    ) -> List[str]:
        """Generate recommended actions based on risk category."""
        recommendations = []
        
        if risk_category == DDICategory.CONTRAINDICATED:
            recommendations.append("Avoid concomitant use")
            recommendations.append("Consider alternative therapies")
        
        elif risk_category == DDICategory.MAJOR:
            recommendations.append("Conduct in vitro DDI study if not available")
            recommendations.append("Consider clinical DDI study")
            recommendations.append("Implement therapeutic drug monitoring")
            recommendations.append("Prepare dose adjustment protocol")
        
        elif risk_category == DDICategory.MODERATE:
            recommendations.append("Consider in vitro screening")
            recommendations.append("Monitor clinical response")
            recommendations.append("Patient education on potential interactions")
        
        elif risk_category == DDICategory.MINOR:
            recommendations.append("Routine monitoring")
            recommendations.append("Document interaction in patient record")
        
        # Add validation experiment recommendations
        if risk_category in [DDICategory.MAJOR, DDICategory.CONTRAINDICATED]:
            recommendations.append("Validation: CYP inhibition assay (IC50 determination)")
            recommendations.append("Validation: CYP induction assay (mRNA/protein expression)")
        
        return recommendations


def create_example_prediction():
    """Create an example prediction for testing."""
    ranker = DDIRiskRanker()
    
    # Example: Warfarin (CYP2C9 substrate) + Fluconazole (CYP2C9 inhibitor)
    # Note: fm value set to None - requires sourced data for accurate prediction
    drug_a = {
        "compound_name": "Warfarin",
        "enzyme_data": {
            "substrate": {
                "CYP2C9": {"is_substrate": True, "fm": None}
            }
        }
    }
    
    drug_b = {
        "compound_name": "Fluconazole",
        "enzyme_data": {
            "inhibition": {
                "CYP2C9": {"is_inhibitor": True, "inhibition_type": "moderate"}
            }
        }
    }
    
    result = ranker.rank_drug_pair(drug_a, drug_b)
    return result


if __name__ == "__main__":
    # Test the ranker
    result = create_example_prediction()
    
    print(f"Drug Pair: {result.drug_a} + {result.drug_b}")
    print(f"Risk Category: {result.risk_category.value}")
    print(f"Risk Score: {result.risk_score:.1f}/100")
    print(f"Mechanism: {result.mechanism.value}")
    print(f"Affected Enzymes: {', '.join(result.affected_enzymes)}")
    print(f"Confidence: {result.confidence}")
    print("\nClinical Implications:")
    for imp in result.clinical_implications:
        print(f"  - {imp}")
    print("\nRecommended Actions:")
    for action in result.recommended_actions:
        print(f"  - {action}")
