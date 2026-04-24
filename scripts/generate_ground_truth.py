"""
Ground Truth Generator for 1000 Synthetic ABA Session Notes

This script automatically generates ground truth annotations (true PHI entities)
for the 1000 synthetic notes by extracting all PHI patterns.

Entity Types:
- PERSON (client names, staff names, parent names, provider names)
- DATE (DOB, session dates, appointment dates, incident dates)
- MEDICAID_ID
- PHONE (phone numbers)
- ADDRESS (street addresses)
- CREDENTIAL (professional credentials)

Output: annotations_1000.json in the format required by evaluator.py
"""

import os
import re
import json
from pathlib import Path


# PHI Pattern Definitions
PATTERNS = {
    'MEDICAID_ID': r'\b[A-Z]{2}\d{6}\b',  # Format: AB123456
    
    'PHONE': r'\b315-\d{3}-\d{4}\b',  # Format: 315-XXX-XXXX
    
    'DATE': [
        r'\b\d{1,2}/\d{1,2}/\d{4}\b',      # M/D/YYYY, MM/DD/YYYY
        r'\b\d{1,2}/\d{1,2}/\d{2}\b',      # M/D/YY
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}\b'  # Month D, YYYY
    ],
    
    'CREDENTIAL': [
        r'\bBCBA\b',
        r'\bM\.A\.\b',
        r'\bMS CCC-SLP\b',
        r'\bOTR/L\b',
        r'\bRN\b',
        r'\bLCSW\b',
        r'\bBehavior Specialist II\b',
        r'\bPsychiatrist\b',
        r'\bOccupational Therapist\b',
        r'\bSpeech-Language Pathologist\b'
    ],
    
    # Address patterns - specific to UCP addresses
    'ADDRESS': [
        r'\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Court|Ct|Boulevard|Blvd),\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s+[A-Z]{2}\s+\d{5}'
    ]
}


def extract_person_names(text):
    """
    Extract PERSON entities (names) from text.
    Looks for capitalized word patterns that appear multiple times (likely names).
    """
    entities = []
    
    # Pattern: Capitalized words (First Last, or First Middle Last)
    # This will catch: "Emma Rodriguez", "John Parker", "Dr. Sarah Wilson"
    name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+\b'
    
    for match in re.finditer(name_pattern, text):
        name = match.group()
        
        # Skip if it's a location/program name
        skip_words = ['Upstate', 'Care', 'Center', 'Session', 'Note', 'Program', 
                      'Residential', 'Day', 'Treatment', 'Plan', 'Behavior', 
                      'Support', 'Clinical', 'Supervisor', 'Post', 'Crisis']
        
        if any(skip in name for skip in skip_words):
            continue
        
        entities.append({
            'text': name,
            'type': 'PERSON',
            'start': match.start(),
            'end': match.end()
        })
    
    return entities


def extract_entities_by_pattern(text, pattern, entity_type):
    """Extract entities matching a specific regex pattern"""
    entities = []
    
    if isinstance(pattern, list):
        # Multiple patterns for this entity type
        for p in pattern:
            for match in re.finditer(p, text):
                entities.append({
                    'text': match.group(),
                    'type': entity_type,
                    'start': match.start(),
                    'end': match.end()
                })
    else:
        # Single pattern
        for match in re.finditer(pattern, text):
            entities.append({
                'text': match.group(),
                'type': entity_type,
                'start': match.start(),
                'end': match.end()
            })
    
    return entities


def extract_all_entities(text):
    """Extract all PHI entities from a note"""
    all_entities = []
    
    # Extract by pattern
    for entity_type, pattern in PATTERNS.items():
        entities = extract_entities_by_pattern(text, pattern, entity_type)
        all_entities.extend(entities)
    
    # Extract person names
    person_entities = extract_person_names(text)
    all_entities.extend(person_entities)
    
    # Sort by start position
    all_entities.sort(key=lambda x: x['start'])
    
    # Remove exact duplicates (same text at same position)
    unique_entities = []
    seen = set()
    
    for entity in all_entities:
        key = (entity['text'], entity['start'], entity['end'], entity['type'])
        if key not in seen:
            unique_entities.append(entity)
            seen.add(key)
    
    return unique_entities


def process_notes(input_dir, output_file):
    """
    Process all synthetic notes and generate ground truth annotations
    
    Args:
        input_dir: Directory containing synthetic note .txt files
        output_file: Path to output annotations JSON file
    """
    
    annotations = []
    
    # Get all .txt files sorted by name
    note_files = sorted(Path(input_dir).glob('*.txt'))
    
    print(f"\n{'='*80}")
    print(f"GROUND TRUTH ANNOTATION GENERATOR")
    print(f"{'='*80}\n")
    print(f"Input directory: {input_dir}")
    print(f"Total notes to process: {len(note_files)}\n")
    
    for idx, note_file in enumerate(note_files, start=1):
        # Read note text
        with open(note_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Extract entities
        entities = extract_all_entities(text)
        
        # Create annotation entry
        annotation = {
            'doc_id': idx,
            'entities': entities
        }
        
        annotations.append(annotation)
        
        # Progress update
        if idx % 100 == 0:
            print(f"  Processed {idx}/{len(note_files)} notes...")
    
    # Save annotations
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ ANNOTATION GENERATION COMPLETE!")
    print(f"{'='*80}\n")
    
    # Statistics
    total_entities = sum(len(doc['entities']) for doc in annotations)
    entity_counts = {}
    
    for doc in annotations:
        for entity in doc['entities']:
            entity_type = entity['type']
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
    
    print(f"📊 Summary:")
    print(f"  Total documents: {len(annotations)}")
    print(f"  Total PHI entities: {total_entities}")
    print(f"  Average entities per note: {total_entities / len(annotations):.1f}\n")
    
    print(f"📋 Entity Type Distribution:")
    for entity_type, count in sorted(entity_counts.items()):
        print(f"  {entity_type:15s}: {count:5d} ({count/total_entities*100:.1f}%)")
    
    print(f"\n📁 Output saved to: {output_file}\n")
    print(f"{'='*80}\n")


def main():
    # Paths
    input_dir = "data/synthetic/raw"
    output_file = "data/annotated/annotations_1000.json"
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Process notes
    process_notes(input_dir, output_file)
    
    print("✅ Ground truth generation complete!")
    print(f"\nNext steps:")
    print(f"  1. Review sample annotations in {output_file}")
    print(f"  2. Run your PHI detection system on the 1000 notes")
    print(f"  3. Compare detected vs. ground truth using run_evaluation.py")


if __name__ == "__main__":
    main()
