"""
Dominant Enzyme Prediction Model

Baseline model for predicting the dominant CYP enzyme(s) responsible for drug metabolism.
Uses fraction metabolized (fm) data to rank enzymes by contribution.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence levels for predictions."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class EnzymePrediction:
    """Prediction result for a single enzyme."""
    enzyme: str
    fraction_metabolized: float
    is_dominant: bool
    confidence: ConfidenceLevel
    evidence: List[str]


@dataclass
class DominantEnzymeResult:
    """Complete prediction result for a compound."""
    compound_name: str
    dominant_enzymes: List[str]
    enzyme_predictions: List[EnzymePrediction]
    overall_confidence: ConfidenceLevel
    notes: List[str]


class DominantEnzymePredictor:
    """
    Baseline predictor for dominant CYP enzymes.
    
    Uses fraction metabolized (fm) values to determine which enzymes
    contribute most to a drug's metabolism.
    """
    
    ENZYMES = [
        "CYP1A2", "CYP2B6", "CYP2C8", "CYP2C9", 
        "CYP2C19", "CYP2D6", "CYP2E1", "CYP3A4", "CYP3A5"
    ]
    
    # Thresholds for classification
    DOMINANT_FM_THRESHOLD = 0.25  # Enzyme with fm > 25% considered dominant
    SIGNIFICANT_FM_THRESHOLD = 0.10  # Enzyme with fm > 10% considered significant
    TOTAL_FM_THRESHOLD = 0.70  # Total fm must account for >70% of metabolism
    
    def __init__(self):
        """Initialize the predictor."""
        pass
    
    def predict_from_fm(self, compound_name: str, fm_data: Dict[str, float]) -> DominantEnzymeResult:
        """
        Predict dominant enzymes from fraction metabolized data.
        
        Args:
            compound_name: Name of the compound
            fm_data: Dictionary mapping enzyme names to fraction metabolized values (0-1)
        
        Returns:
            DominantEnzymeResult with predictions
        """
        enzyme_predictions = []
        total_fm = 0.0
        
        # Build predictions for each enzyme
        for enzyme in self.ENZYMES:
            fm = fm_data.get(enzyme, 0.0)
            
            if fm > 0:
                total_fm += fm
                is_dominant = fm >= self.DOMINANT_FM_THRESHOLD
                confidence = self._calculate_confidence(fm)
                evidence = self._generate_evidence(fm)
                
                prediction = EnzymePrediction(
                    enzyme=enzyme,
                    fraction_metabolized=fm,
                    is_dominant=is_dominant,
                    confidence=confidence,
                    evidence=evidence
                )
                enzyme_predictions.append(prediction)
        
        # Determine dominant enzymes
        dominant_enzymes = [
            p.enzyme for p in enzyme_predictions if p.is_dominant
        ]
        
        # Sort by fraction metabolized (descending)
        enzyme_predictions.sort(key=lambda x: x.fraction_metabolized, reverse=True)
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            dominant_enzymes, total_fm, enzyme_predictions
        )
        
        # Generate notes
        notes = self._generate_notes(
            dominant_enzymes, total_fm, enzyme_predictions
        )
        
        return DominantEnzymeResult(
            compound_name=compound_name,
            dominant_enzymes=dominant_enzymes,
            enzyme_predictions=enzyme_predictions,
            overall_confidence=overall_confidence,
            notes=notes
        )
    
    def _calculate_confidence(self, fm: float) -> ConfidenceLevel:
        """Calculate confidence level for a single enzyme prediction."""
        if fm >= self.DOMINANT_FM_THRESHOLD:
            return ConfidenceLevel.HIGH
        elif fm >= self.SIGNIFICANT_FM_THRESHOLD:
            return ConfidenceLevel.MEDIUM
        elif fm > 0:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNKNOWN
    
    def _calculate_overall_confidence(
        self, 
        dominant_enzymes: List[str], 
        total_fm: float,
        predictions: List[EnzymePrediction]
    ) -> ConfidenceLevel:
        """Calculate overall confidence for the prediction."""
        if not dominant_enzymes:
            return ConfidenceLevel.LOW
        
        if total_fm < self.TOTAL_FM_THRESHOLD:
            return ConfidenceLevel.LOW
        
        # Check if we have high confidence dominant enzyme
        has_high_confidence = any(
            p.confidence == ConfidenceLevel.HIGH and p.is_dominant
            for p in predictions
        )
        
        if has_high_confidence and total_fm >= 0.85:
            return ConfidenceLevel.HIGH
        elif total_fm >= 0.75:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _generate_evidence(self, fm: float) -> List[str]:
        """Generate evidence statements for an enzyme."""
        evidence = []
        
        if fm >= self.DOMINANT_FM_THRESHOLD:
            evidence.append(f"High fraction metabolized ({fm:.2f}) indicates major pathway")
        elif fm >= self.SIGNIFICANT_FM_THRESHOLD:
            evidence.append(f"Moderate fraction metabolized ({fm:.2f}) indicates significant pathway")
        elif fm > 0:
            evidence.append(f"Minor fraction metabolized ({fm:.2f}) indicates minor pathway")
        
        return evidence
    
    def _generate_notes(
        self,
        dominant_enzymes: List[str],
        total_fm: float,
        predictions: List[EnzymePrediction]
    ) -> List[str]:
        """Generate notes about the prediction."""
        notes = []
        
        if not dominant_enzymes:
            notes.append("No dominant enzyme identified based on fm data")
            notes.append("Consider non-CYP metabolism pathways")
        elif len(dominant_enzymes) == 1:
            notes.append(f"Single dominant enzyme: {dominant_enzymes[0]}")
            notes.append("DDI risk primarily from inhibitors/inducers of this enzyme")
        else:
            notes.append(f"Multiple dominant enzymes: {', '.join(dominant_enzymes)}")
            notes.append("DDI risk from inhibitors/inducers of any dominant enzyme")
        
        if total_fm < self.TOTAL_FM_THRESHOLD:
            notes.append(f"Low total fm ({total_fm:.2f}) - significant non-CYP metabolism likely")
            notes.append("Consider additional metabolic pathways")
        
        # Check for CYP3A family
        cyp3a_enzymes = [e for e in dominant_enzymes if "CYP3A" in e]
        if cyp3a_enzymes:
            notes.append("CYP3A family involvement - high DDI risk potential")
        
        return notes
    
    def predict_from_compound_data(self, compound_data: dict) -> DominantEnzymeResult:
        """
        Predict dominant enzymes from full compound data structure.
        
        Args:
            compound_data: Compound data dictionary following the schema
        
        Returns:
            DominantEnzymeResult with predictions
        """
        compound_name = compound_data.get("compound_name", "Unknown")
        
        # Extract fm data from substrate information
        fm_data = {}
        substrate_data = compound_data.get("enzyme_data", {}).get("substrate", {})
        
        for enzyme, data in substrate_data.items():
            if data.get("is_substrate", False):
                fm = data.get("fm")
                if fm is not None and fm > 0:
                    fm_data[enzyme] = fm
        
        return self.predict_from_fm(compound_name, fm_data)


def create_example_prediction():
    """Create an example prediction for testing."""
    predictor = DominantEnzymePredictor()
    
    # Example: Warfarin-like compound
    # Note: fm values set to None - requires sourced data for accurate prediction
    fm_data = {
        "CYP2C9": None,
        "CYP1A2": None,
        "CYP3A4": None
    }
    
    result = predictor.predict_from_fm("Example Compound", fm_data)
    return result


if __name__ == "__main__":
    # Test the predictor
    result = create_example_prediction()
    
    print(f"Compound: {result.compound_name}")
    print(f"Dominant Enzymes: {result.dominant_enzymes}")
    print(f"Overall Confidence: {result.overall_confidence.value}")
    print("\nEnzyme Predictions:")
    for pred in result.enzyme_predictions:
        print(f"  {pred.enzyme}: fm={pred.fraction_metabolized:.2f}, "
              f"dominant={pred.is_dominant}, confidence={pred.confidence.value}")
    print("\nNotes:")
    for note in result.notes:
        print(f"  - {note}")
