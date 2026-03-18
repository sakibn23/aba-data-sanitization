#!/usr/bin/env python3
"""
Medicaid ID Generator for UCP Data Sanitization Project
Generates realistic 8-character Medicaid IDs (2 letters + 6 digits)
Format: AB123456
"""

import random
import string
from pathlib import Path

def generate_medicaid_id():
    """
    Generate a single realistic 8-character Medicaid ID
    
    Format: 2 uppercase letters + 6 digits
    Example: EM456789, JR234567
    
    Returns:
        str: 8-character Medicaid ID
    """
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=6))
    return f"{letters}{numbers}"

def generate_batch(n=200, output_file=None):
    """
    Generate n unique Medicaid IDs
    
    Args:
        n (int): Number of IDs to generate (default: 200)
        output_file (str or Path): Optional output file path
    
    Returns:
        list: List of unique Medicaid IDs
    """
    ids = set()
    
    # Generate unique IDs
    while len(ids) < n:
        ids.add(generate_medicaid_id())
    
    ids_list = sorted(list(ids))
    
    # Save to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            for med_id in ids_list:
                f.write(f"{med_id}\n")
        
        print(f"✅ Generated {len(ids_list)} Medicaid IDs")
        print(f"📁 Saved to: {output_path}")
    
    return ids_list

def validate_medicaid_id(med_id):
    """
    Validate a Medicaid ID matches expected format
    
    Args:
        med_id (str): Medicaid ID to validate
    
    Returns:
        bool: True if valid format, False otherwise
    """
    if len(med_id) != 8:
        return False
    
    if not med_id[:2].isupper():
        return False
    
    if not med_id[2:].isdigit():
        return False
    
    return True

def main():
    """Main execution function"""
    print("=" * 60)
    print("MEDICAID ID GENERATOR")
    print("UCP Data Sanitization Research Project")
    print("=" * 60)
    print()
    
    # Generate 200 unique IDs
    output_file = Path(__file__).parent / 'data' / 'identifiers' / 'medicaid_ids.txt'
    
    print(f"Generating 200 unique Medicaid IDs...")
    medicaid_ids = generate_batch(n=200, output_file=output_file)
    
    print()
    print("📊 Sample IDs (first 10):")
    for i, med_id in enumerate(medicaid_ids[:10], 1):
        print(f"   {i:2d}. {med_id}")
    
    print()
    print("✅ Validation Check:")
    all_valid = all(validate_medicaid_id(mid) for mid in medicaid_ids)
    print(f"   All IDs valid: {all_valid}")
    
    print()
    print("=" * 60)
    print("COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
