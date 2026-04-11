"""
PHI Detection Runner for 1,245 Synthetic ABA Session Notes

This script runs PHI detection on all synthetic notes using the SpacyRegexDetector
and outputs detected_entities.json for evaluation.

Requirements:
- spaCy with en_core_web_sm model
- SpacyRegexDetector class
- Synthetic notes in data/synthetic/raw/

Output: outputs/detected_entities.json
"""

import os
import sys
import json
from pathlib import Path
import spacy
import re


# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SpacyRegexDetector:
    """
    Hybrid PHI detector using spaCy NER + Regex patterns
    """
    
    def __init__(self):
        print("Loading spaCy model...")
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("❌ spaCy model 'en_core_web_sm' not found!")
            print("   Install it with: python -m spacy download en_core_web_sm")
            sys.exit(1)
        
        # Define regex patterns for PHI
        self.regex_patterns = self._get_regex_patterns()
    
    def _get_regex_patterns(self):
        """Define regex patterns for PHI detection"""
        return {
            'DATE': [
                re.compile(r'\b\d{1,2}/\d{1,2}/\d{4}\b'),  # MM/DD/YYYY
                re.compile(r'\b\d{1,2}/\d{1,2}/\d{2}\b'),  # MM/DD/YY
                re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', re.IGNORECASE)
            ],
            'MEDICAID_ID': [
                re.compile(r'\b[A-Z]{2}\d{6}\b')  # AB123456
            ],
            'PHONE': [
                re.compile(r'\b\d{3}-\d{3}-\d{4}\b'),  # 315-123-4567
                re.compile(r'\b\(\d{3}\)\s*\d{3}-\d{4}\b')  # (315) 123-4567
            ],
            'ADDRESS': [
                re.compile(r'\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Court|Ct|Boulevard|Blvd),\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s+[A-Z]{2}\s+\d{5}')
            ],
            'CREDENTIAL': [
                re.compile(r'\bBCBA\b'),
                re.compile(r'\bM\.A\.\b'),
                re.compile(r'\bMS CCC-SLP\b'),
                re.compile(r'\bOTR/L\b'),
                re.compile(r'\bRN\b'),
                re.compile(r'\bLCSW\b')
            ]
        }
    
    def detect(self, text):
        """
        Detect PHI entities in text
        
        Returns:
            List of entities with format:
            [{"text": str, "type": str, "start": int, "end": int}]
        """
        entities = []
        
        # 1. SpaCy NER for PERSON entities
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                entities.append({
                    "text": ent.text,
                    "type": "PERSON",
                    "start": ent.start_char,
                    "end": ent.end_char
                })
        
        # 2. Regex patterns for other PHI types
        for entity_type, patterns in self.regex_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    entities.append({
                        "text": match.group(),
                        "type": entity_type,
                        "start": match.start(),
                        "end": match.end()
                    })
        
        # 3. Remove overlapping entities (keep longer spans)
        entities = self._remove_overlaps(entities)
        
        return entities
    
    def _remove_overlaps(self, entities):
        """Remove overlapping entities, keeping longer spans"""
        if not entities:
            return []
        
        # Sort by start position, then by length (descending)
        entities = sorted(entities, key=lambda x: (x["start"], -(x["end"] - x["start"])))
        
        final = []
        prev_end = -1
        
        for ent in entities:
            if ent["start"] >= prev_end:
                final.append(ent)
                prev_end = ent["end"]
        
        return final


def process_notes(input_dir, output_file):
    """
    Run PHI detection on all synthetic notes
    
    Args:
        input_dir: Directory containing .txt note files
        output_file: Path to save detected_entities.json
    """
    
    # Initialize detector
    detector = SpacyRegexDetector()
    
    # Get all note files
    note_files = sorted(Path(input_dir).glob('*.txt'))
    
    print(f"\n{'='*80}")
    print(f"PHI DETECTION RUNNER")
    print(f"{'='*80}\n")
    print(f"Input directory: {input_dir}")
    print(f"Total notes to process: {len(note_files)}\n")
    
    results = []
    
    for idx, note_file in enumerate(note_files, start=1):
        # Read note text
        with open(note_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Detect PHI
        entities = detector.detect(text)
        
        # Store results
        results.append({
            "id": idx,
            "entities": entities
        })
        
        # Progress update
        if idx % 100 == 0:
            print(f"  Processed {idx}/{len(note_files)} notes...")
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save detected entities
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ PHI DETECTION COMPLETE!")
    print(f"{'='*80}\n")
    
    # Statistics
    total_entities = sum(len(doc['entities']) for doc in results)
    entity_counts = {}
    
    for doc in results:
        for entity in doc['entities']:
            entity_type = entity['type']
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
    
    print(f"📊 Summary:")
    print(f"  Total documents: {len(results)}")
    print(f"  Total detected PHI: {total_entities}")
    print(f"  Average PHI per note: {total_entities / len(results):.1f}\n")
    
    print(f"📋 Detected Entity Types:")
    for entity_type, count in sorted(entity_counts.items()):
        print(f"  {entity_type:15s}: {count:5d} ({count/total_entities*100:.1f}%)")
    
    print(f"\n📁 Output saved to: {output_file}\n")
    print(f"{'='*80}\n")


def main():
    # Paths
    input_dir = "data/synthetic/raw"
    output_file = "outputs/detected_entities.json"
    
    # Check if input directory exists
    if not os.path.exists(input_dir):
        print(f"❌ Error: Input directory not found: {input_dir}")
        sys.exit(1)
    
    # Run detection
    process_notes(input_dir, output_file)
    
    print("✅ PHI detection complete!")
    print(f"\nNext steps:")
    print(f"  1. Review detected entities in {output_file}")
    print(f"  2. Run evaluation: python scripts/run_evaluation.py")
    print(f"  3. Compare precision/recall/F1 vs. ground truth")


if __name__ == "__main__":
    main()
