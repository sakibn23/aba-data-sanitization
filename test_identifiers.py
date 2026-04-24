#!/usr/bin/env python3
"""
Test Identifier Selection
Tests that all identifier files work together to generate random clients
"""

import csv
import random
from datetime import datetime, timedelta

def generate_dob(min_age=3, max_age=18):
    """Generate random date of birth for child"""
    today = datetime.today()
    age_years = random.randint(min_age, max_age)
    age_days = age_years * 365 + random.randint(0, 364)
    dob = today - timedelta(days=age_days)
    return dob.strftime("%m/%d/%Y")

def test_identifiers():
    """Test all identifier files"""
    
    print("=" * 70)
    print("IDENTIFIER SELECTION TEST")
    print("UCP Data Sanitization Research Project")
    print("=" * 70)
    print()
    
    # Read first names
    print(" Loading first_names.csv...")
    with open('data/identifiers/first_names.csv', 'r') as f:
        reader = csv.DictReader(f)
        first_names = [row['first_name'] for row in reader]
    print(f"    Loaded {len(first_names)} first names")
    
    # Read last names
    print(" Loading last_names.csv...")
    with open('data/identifiers/last_names.csv', 'r') as f:
        reader = csv.DictReader(f)
        last_names = [row['last_name'] for row in reader]
    print(f"    Loaded {len(last_names)} last names")
    
    # Read addresses
    print(" Loading syracuse_addresses.csv...")
    with open('data/identifiers/syracuse_addresses.csv', 'r') as f:
        reader = csv.DictReader(f)
        addresses = list(reader)
    print(f"    Loaded {len(addresses)} addresses")
    
    # Read Medicaid IDs
    print(" Loading medicaid_ids.txt...")
    with open('data/identifiers/medicaid_ids.txt', 'r') as f:
        medicaid_ids = [line.strip() for line in f]
    print(f"    Loaded {len(medicaid_ids)} Medicaid IDs")
    
    print()
    print("=" * 70)
    print("GENERATING 5 RANDOM SYNTHETIC CLIENTS")
    print("=" * 70)
    print()
    
    # Generate 5 random clients
    for i in range(1, 6):
        # Random selections
        first = random.choice(first_names)
        last = random.choice(last_names)
        addr = random.choice(addresses)
        medicaid = random.choice(medicaid_ids)
        dob = generate_dob()
        
        # Calculate age
        dob_date = datetime.strptime(dob, "%m/%d/%Y")
        age = (datetime.today() - dob_date).days // 365
        
        print(f"CLIENT {i}:")
        print(f"  Name:        {first} {last}")
        print(f"  DOB:         {dob}")
        print(f"  Age:         {age} years")
        print(f"  Address:     {addr['street']}")
        print(f"               {addr['city']}, {addr['state']} {addr['zip']}")
        print(f"  Medicaid ID: {medicaid}")
        print()
    
    print("=" * 70)
    print("✅ ALL IDENTIFIER FILES WORKING PERFECTLY!")
    print("=" * 70)
    print()
    
    # Calculate total combinations
    total_combinations = len(first_names) * len(last_names) * len(addresses) * len(medicaid_ids)
    print(f" STATISTICS:")
    print(f"   Total possible unique clients: {total_combinations:,}")
    print(f"   More than enough for 100-200 synthetic notes!")
    print()

if __name__ == "__main__":
    test_identifiers()