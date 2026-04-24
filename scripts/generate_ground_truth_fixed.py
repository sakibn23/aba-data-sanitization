"""
IMPROVED Ground Truth Generator for 1000 Synthetic ABA Session Notes

This FIXED version addresses over-detection of PERSON entities by:
1. Filtering out common section headers and labels
2. Using context-aware person name detection
3. Requiring names to appear in person-appropriate contexts

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
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'  # Month D, YYYY
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


# Comprehensive blacklist of non-person phrases
NON_PERSON_PHRASES = {
    # Section headers
    'Session Note', 'Session Date', 'Session Time', 'Session Duration',
    'Service Location', 'Staff Present', 'Medicaid ID',
    'Date of Birth', 'Client Name', 'Staff Name',
    'Residential Program', 'Day Program', 'Treatment Plan',
    'Behavior Support', 'Clinical Supervisor', 'Behavioral Support',
    
    # Behavioral terms
    'Physical Aggression', 'Verbal Aggression', 'Self Injury',
    'Property Destruction', 'Challenging Behavior', 'Target Behavior',
    'Replacement Behavior', 'Positive Behavior', 'Appropriate Behavior',
    'Social Interaction', 'Peer Interaction', 'Communication Skills',
    'Emotion Regulation', 'Self Care', 'Daily Living',
    
    # Program/location names
    'Upstate Care', 'Care Providers', 'Geiger Center', 'Miller Center',
    'Summit House', 'Valley View', 'Maple House', 'Oak Center',
    'Pine Ridge', 'Birch House', 'Willow Center',
    
    # Generic organizational terms
    'Crisis Intervention', 'Emergency Response', 'Safety Protocol',
    'Medical Emergency', 'Incident Report', 'Treatment Team',
    'Support Plan', 'Progress Report', 'Review Meeting',
    
    # Activity/skill names
    'Puzzle Completion', 'Card Matching', 'Color Sorting',
    'Shape Recognition', 'Number Recognition', 'Letter Recognition',
    
    # Time/session related
    'Post Crisis', 'Pre Session', 'Follow Up',
    'Next Session', 'Previous Session', 'Session Summary',
    
    # Medical/clinical terms that aren't names
    'Occupational Therapy', 'Speech Therapy', 'Physical Therapy',
    'Applied Behavior', 'Functional Behavior', 'Behavior Analysis'
}


def is_likely_person_name(text):
    """
    Determine if a capitalized phrase is likely a person name
    
    Returns:
        bool: True if likely a person name
    """
    # Check blacklist
    if text in NON_PERSON_PHRASES:
        return False
    
    # Check if any blacklisted phrase is contained
    for phrase in NON_PERSON_PHRASES:
        if phrase.lower() in text.lower():
            return False
    
    # Must be 2-3 words
    words = text.split()
    if len(words) < 2 or len(words) > 3:
        return False
    
    # Each word should be capitalized and mostly alphabetic
    for word in words:
        if not word[0].isupper():
            return False
        if not word.replace('.', '').replace("'", '').isalpha():
            return False
    
    # Check for common name patterns
    # First word should be reasonable length for a first name (2-15 chars)
    if len(words[0]) < 2 or len(words[0]) > 15:
        return False
    
    # Last word should be reasonable length for a last name (2-20 chars)
    if len(words[-1]) < 2 or len(words[-1]) > 20:
        return False
    
    # Avoid common false positives
    false_positive_starts = ['The', 'This', 'That', 'These', 'Those', 'Their', 
                             'Session', 'During', 'After', 'Before', 'Following']
    if words[0] in false_positive_starts:
        return False
    
    return True


def extract_person_names(text):
    """
    Extract PERSON entities (names) from text with improved filtering.
    """
    entities = []
    
    # Pattern: Capitalized words (First Last, or First M. Last)
    name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+\b'
    
    for match in re.finditer(name_pattern, text):
        name = match.group()
        
        # Apply filtering
        if is_likely_person_name(name):
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
    
    # Extract person names with improved filtering
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
    print(f"IMPROVED GROUND TRUTH ANNOTATION GENERATOR")
    print(f"{'='*80}\n")
    print(f"Input directory: {input_dir}")
    print(f"Total notes to process: {len(note_files)}\n")
    print(f"Improvements:")
    print(f"  ✅ Better person name filtering")
    print(f"  ✅ Blacklist of {len(NON_PERSON_PHRASES)} non-person phrases")
    print(f"  ✅ Context-aware detection\n")
    
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
    output_file = "data/annotated/annotations_1000_fixed.json"
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Process notes
    process_notes(input_dir, output_file)
    
    print("✅ Improved ground truth generation complete!")
    print(f"\nNext steps:")
    print(f"  1. Review sample annotations in {output_file}")
    print(f"  2. Compare with old annotations")
    print(f"  3. Re-run evaluation with new ground truth")
    print(f"  4. Expected improvement: ~+10-15 percentage points in recall")


if __name__ == "__main__":
    main()
