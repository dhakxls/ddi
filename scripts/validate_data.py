#!/usr/bin/env python3
"""
Data validation script for compound curation.
Validates curated compound data against the JSON schema.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import jsonschema


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON schema."""
    with open(schema_path, 'r') as f:
        return json.load(f)


def validate_compound_data(data_path: Path, schema_path: Path) -> bool:
    """
    Validate compound data against schema.
    
    Args:
        data_path: Path to compound data JSON file
        schema_path: Path to JSON schema file
    
    Returns:
        True if validation passes, False otherwise
    """
    schema = load_schema(schema_path)
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    try:
        jsonschema.validate(instance=data, schema=schema)
        print(f"✓ {data_path.name} validation passed")
        return True
    except jsonschema.ValidationError as e:
        print(f"✗ {data_path.name} validation failed:")
        print(f"  Path: {'.'.join(str(p) for p in e.path)}")
        print(f"  Message: {e.message}")
        return False


def validate_all_compounds(data_dir: Path, schema_path: Path) -> Dict[str, bool]:
    """
    Validate all compound JSON files in a directory.
    
    Args:
        data_dir: Directory containing compound JSON files
        schema_path: Path to JSON schema file
    
    Returns:
        Dictionary mapping filename to validation result
    """
    results = {}
    
    for json_file in data_dir.glob("*.json"):
        results[json_file.name] = validate_compound_data(json_file, schema_path)
    
    return results


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    schema_path = project_root / "data" / "schemas" / "compound_schema.json"
    curated_dir = project_root / "data" / "curated"
    
    if not schema_path.exists():
        print(f"Error: Schema not found at {schema_path}")
        sys.exit(1)
    
    if not curated_dir.exists():
        print(f"Error: Curated data directory not found at {curated_dir}")
        print("Creating directory...")
        curated_dir.mkdir(parents=True, exist_ok=True)
        sys.exit(0)
    
    results = validate_all_compounds(curated_dir, schema_path)
    
    if not results:
        print("No compound data files found to validate")
        sys.exit(0)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nValidation summary: {passed}/{total} files passed")
    
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
