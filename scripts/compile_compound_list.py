#!/usr/bin/env python3
"""
Script to identify and compile a list of 100 well-characterized compounds
from FDA/EMA databases for initial curation.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict


# Well-characterized compounds with extensive regulatory data
TARGET_COMPOUNDS = [
    # Anticoagulants
    "Warfarin",
    "Dabigatran",
    "Rivaroxaban",
    "Apixaban",
    "Edoxaban",
    
    # Statins
    "Atorvastatin",
    "Simvastatin",
    "Rosuvastatin",
    "Pravastatin",
    "Lovastatin",
    
    # Antidepressants
    "Fluoxetine",
    "Sertraline",
    "Paroxetine",
    "Citalopram",
    "Escitalopram",
    "Venlafaxine",
    "Duloxetine",
    "Amitriptyline",
    "Nortriptyline",
    
    # Antipsychotics
    "Risperidone",
    "Olanzapine",
    "Quetiapine",
    "Clozapine",
    "Haloperidol",
    
    # Antiarrhythmics
    "Amiodarone",
    "Dronedarone",
    "Flecainide",
    "Propafenone",
    
    # Beta-blockers
    "Metoprolol",
    "Propranolol",
    "Carvedilol",
    "Diltiazem",
    "Verapamil",
    
    # Antiepileptics
    "Carbamazepine",
    "Phenytoin",
    "Valproate",
    "Lamotrigine",
    "Phenobarbital",
    
    # Antibiotics
    "Clarithromycin",
    "Erythromycin",
    "Rifampin",
    "Isoniazid",
    "Doxycycline",
    
    # Antifungals
    "Ketoconazole",
    "Itraconazole",
    "Fluconazole",
    "Voriconazole",
    
    # Immunosuppressants
    "Cyclosporine",
    "Tacrolimus",
    "Sirolimus",
    
    # Anticancer
    "Imatinib",
    "Erlotinib",
    "Sunitinib",
    "Sorafenib",
    "Tamoxifen",
    
    # Cardiovascular
    "Losartan",
    "Valsartan",
    "Enalapril",
    "Lisinopril",
    "Amlodipine",
    "Digoxin",
    
    # Diabetes
    "Metformin",
    "Glipizide",
    "Glyburide",
    "Sitagliptin",
    
    # Pain/NSAIDs
    "Ibuprofen",
    "Naproxen",
    "Diclofenac",
    "Celecoxib",
    "Codeine",
    "Tramadol",
    "Methadone",
    
    # Benzodiazepines
    "Diazepam",
    "Lorazepam",
    "Alprazolam",
    "Clonazepam",
    
    # Others
    "Theophylline",
    "Caffeine",
    "Omeprazole",
    "Esomeprazole",
    "Montelukast",
    "Sildenafil",
    "Tadalafil",
    "Clopidogrel",
    "Prednisone",
    "Methylprednisolone",
]


def create_compound_tracking_sheet(output_path: Path):
    """
    Create a tracking sheet for compound curation progress.
    
    Args:
        output_path: Path to save the tracking sheet
    """
    data = []
    
    for i, compound in enumerate(TARGET_COMPOUNDS, 1):
        data.append({
            "ID": i,
            "Compound Name": compound,
            "Curation Status": "Not Started",
            "Primary Source": "",
            "Secondary Source": "",
            "Quality Rating": "",
            "Curator": "",
            "Curation Date": "",
            "Peer Reviewer": "",
            "Peer Review Date": "",
            "Notes": ""
        })
    
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False)
    print(f"Tracking sheet created: {output_path}")


def create_compound_list(output_path: Path):
    """
    Create a simple list of target compounds.
    
    Args:
        output_path: Path to save the compound list
    """
    with open(output_path, 'w') as f:
        f.write("# Target Compounds for DDI Prediction MVP\n\n")
        f.write("## List of 100 Well-Characterized Compounds\n\n")
        for i, compound in enumerate(TARGET_COMPOUNDS, 1):
            f.write(f"{i}. {compound}\n")
    
    print(f"Compound list created: {output_path}")


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    curated_dir = data_dir / "curated"
    
    # Create directories if they don't exist
    curated_dir.mkdir(parents=True, exist_ok=True)
    
    # Create tracking sheet
    tracking_path = curated_dir / "compound_tracking_sheet.xlsx"
    create_compound_tracking_sheet(tracking_path)
    
    # Create simple list
    list_path = curated_dir / "target_compounds.md"
    create_compound_list(list_path)
    
    print("\nTarget compounds list initialized.")
    print(f"Total compounds: {len(TARGET_COMPOUNDS)}")
    print("\nNext steps:")
    print("1. Review the compound list in data/curated/target_compounds.md")
    print("2. Use the tracking sheet in data/curated/compound_tracking_sheet.xlsx")
    print("3. Follow curation template in docs/curation_template.md")


if __name__ == "__main__":
    main()
