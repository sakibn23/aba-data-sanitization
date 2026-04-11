"""
Sanitization Runner for Synthetic ABA Notes

This script applies all 4 sanitization strategies to your 1,245 synthetic notes
and evaluates their effectiveness.

Sanitization Methods:
1. REPLACE - Replace PHI with entity type labels [PERSON], [DATE], etc.
2. MASK - Partial masking (e.g., "Emma" -> "E**a")
3. HASH - Replace with deterministic hash (e.g., "Emma" -> "a3f5e8b2")
4. HYBRID - Context-aware combination of above methods

Evaluation Metrics:
- PHI Removal Rate: % of detected PHI successfully removed
- Document Similarity: Cosine similarity (original vs sanitized)
- Utility Preservation: Qualitative assessment of clinical content retention
"""

import os
import json
import hashlib
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


# ========================================
# SANITIZER CLASS (Enhanced)
# ========================================

class Sanitizer:
    """Sanitization methods for PHI removal"""
    
    def __init__(self, method="replace"):
        self.method = method
        self.replacement_map = {}  # For consistent replacement across documents
    
    def replace(self, text, ent_type):
        """Replace with entity type label"""
        return f"[{ent_type}]"
    
    def mask(self, text):
        """Partial masking - keep first and last character"""
        if len(text) <= 2:
            return "*" * len(text)
        return text[0] + "*" * (len(text) - 2) + text[-1]
    
    def hash_text(self, text):
        """Deterministic hash"""
        return hashlib.sha256(text.encode()).hexdigest()[:8]
    
    def hybrid(self, text, ent_type):
        """Context-aware hybrid approach"""
        if ent_type == "PERSON":
            return "[PERSON]"
        elif ent_type == "DATE":
            return self.mask(text)
        elif ent_type == "MEDICAID_ID":
            return self.hash_text(text)
        elif ent_type == "PHONE":
            return "[PHONE]"
        elif ent_type == "ADDRESS":
            return "[ADDRESS]"
        elif ent_type == "CREDENTIAL":
            return text  # Keep credentials for clinical context
        else:
            return text
    
    def sanitize(self, text, entities):
        """
        Apply sanitization to text based on detected entities
        
        Args:
            text: Original document text
            entities: List of detected PHI entities with start, end, type
        
        Returns:
            Sanitized text with PHI removed/replaced
        """
        # Sort entities by start position (descending) to preserve indices
        entities_sorted = sorted(entities, key=lambda x: x["start"], reverse=True)
        
        sanitized_text = text
        
        for ent in entities_sorted:
            start = ent["start"]
            end = ent["end"]
            original = text[start:end]
            ent_type = ent["type"]
            
            # Apply selected sanitization method
            if self.method == "replace":
                replacement = self.replace(original, ent_type)
            elif self.method == "mask":
                replacement = self.mask(original)
            elif self.method == "hash":
                replacement = self.hash_text(original)
            elif self.method == "hybrid":
                replacement = self.hybrid(original, ent_type)
            else:
                replacement = original
            
            # Replace in text
            sanitized_text = sanitized_text[:start] + replacement + sanitized_text[end:]
        
        return sanitized_text


# ========================================
# EVALUATION METRICS
# ========================================

def calculate_phi_removal_rate(original_entities, sanitized_text):
    """
    Calculate percentage of PHI successfully removed
    
    Returns:
        float: Removal rate (0-1)
    """
    if not original_entities:
        return 1.0
    
    removed_count = 0
    
    for entity in original_entities:
        original_text = entity["text"]
        # Check if original PHI text still appears in sanitized version
        if original_text not in sanitized_text:
            removed_count += 1
    
    removal_rate = removed_count / len(original_entities)
    return removal_rate


def calculate_similarity(original_text, sanitized_text, model):
    """
    Calculate semantic similarity using SentenceTransformer
    
    Returns:
        float: Cosine similarity (0-1)
    """
    emb_original = model.encode(original_text)
    emb_sanitized = model.encode(sanitized_text)
    
    similarity = cosine_similarity([emb_original], [emb_sanitized])[0][0]
    return float(similarity)


# ========================================
# MAIN PROCESSING
# ========================================

def load_synthetic_notes(notes_dir):
    """Load all synthetic note text files"""
    notes = []
    note_files = sorted(Path(notes_dir).glob('*.txt'))
    
    for idx, note_file in enumerate(note_files, start=1):
        with open(note_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        notes.append({
            'id': idx,
            'filename': note_file.name,
            'text': text
        })
    
    return notes


def load_detected_entities(detection_file):
    """Load detected entities JSON"""
    with open(detection_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_sanitization_pipeline(notes_dir, detection_file, output_dir):
    """
    Run all sanitization methods and evaluate
    
    Args:
        notes_dir: Directory with synthetic .txt notes
        detection_file: Path to detected_entities.json
        output_dir: Directory to save sanitized outputs
    """
    
    print("\n" + "="*80)
    print("SANITIZATION PIPELINE RUNNER")
    print("="*80 + "\n")
    
    # Load data
    print("Loading data...")
    notes = load_synthetic_notes(notes_dir)
    detections = load_detected_entities(detection_file)
    
    print(f"  Loaded {len(notes)} synthetic notes")
    print(f"  Loaded detections for {len(detections)} documents\n")
    
    # Create entity lookup
    entity_map = {d['id']: d['entities'] for d in detections}
    
    # Initialize similarity model
    print("Loading SentenceTransformer model...")
    similarity_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("  Model loaded!\n")
    
    # Sanitization methods to test
    methods = ['replace', 'mask', 'hash', 'hybrid']
    
    results = {}
    
    for method in methods:
        print(f"\n{'='*80}")
        print(f"PROCESSING METHOD: {method.upper()}")
        print(f"{'='*80}\n")
        
        sanitizer = Sanitizer(method=method)
        
        sanitized_docs = []
        phi_removal_rates = []
        similarities = []
        
        for note in notes:
            doc_id = note['id']
            original_text = note['text']
            
            # Get detected entities for this document
            entities = entity_map.get(doc_id, [])
            
            # Sanitize
            sanitized_text = sanitizer.sanitize(original_text, entities)
            
            # Calculate metrics
            removal_rate = calculate_phi_removal_rate(entities, sanitized_text)
            similarity = calculate_similarity(original_text, sanitized_text, similarity_model)
            
            phi_removal_rates.append(removal_rate)
            similarities.append(similarity)
            
            # Store result
            sanitized_docs.append({
                'id': doc_id,
                'filename': note['filename'],
                'original_text': original_text,
                'sanitized_text': sanitized_text,
                'num_entities': len(entities),
                'phi_removal_rate': round(removal_rate, 4),
                'similarity_score': round(similarity, 4)
            })
            
            # Progress update
            if doc_id % 100 == 0:
                print(f"  Processed {doc_id}/{len(notes)} documents...")
        
        # Aggregate metrics
        avg_removal = np.mean(phi_removal_rates)
        avg_similarity = np.mean(similarities)
        
        results[method] = {
            'avg_phi_removal_rate': round(avg_removal, 4),
            'avg_similarity_score': round(avg_similarity, 4),
            'total_documents': len(notes)
        }
        
        print(f"\n  ✅ {method.upper()} Complete:")
        print(f"     PHI Removal Rate: {avg_removal:.2%}")
        print(f"     Avg Similarity:   {avg_similarity:.2%}")
        
        # Save sanitized documents
        method_output_dir = Path(output_dir) / method
        method_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON
        json_output = method_output_dir / f"{method}_sanitized.json"
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(sanitized_docs, f, indent=2)
        
        # Save as individual text files (for easy review)
        text_output_dir = method_output_dir / "notes"
        text_output_dir.mkdir(exist_ok=True)
        
        for doc in sanitized_docs:
            output_file = text_output_dir / f"sanitized_{doc['filename']}"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(doc['sanitized_text'])
        
        print(f"     Saved to: {method_output_dir}")
    
    # Save summary results
    summary_file = Path(output_dir) / "sanitization_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    # Print comparison table
    print(f"\n{'='*80}")
    print("SANITIZATION METHODS COMPARISON")
    print(f"{'='*80}\n")
    
    print(f"{'Method':<15} {'PHI Removal':>15} {'Similarity':>15}")
    print("-" * 80)
    
    for method, metrics in results.items():
        removal = metrics['avg_phi_removal_rate']
        similarity = metrics['avg_similarity_score']
        print(f"{method.upper():<15} {removal:>14.2%} {similarity:>14.2%}")
    
    print(f"\n📁 Summary saved to: {summary_file}")
    print(f"\n{'='*80}\n")
    
    return results


def main():
    # Configuration
    notes_dir = "data/synthetic/raw"
    detection_file = "outputs/detected_entities.json"
    output_dir = "outputs/sanitized"
    
    # Check inputs exist
    if not Path(notes_dir).exists():
        print(f"❌ Error: Notes directory not found: {notes_dir}")
        return
    
    if not Path(detection_file).exists():
        print(f"❌ Error: Detection file not found: {detection_file}")
        print("   Run PHI detection first: python scripts/run_phi_detection.py")
        return
    
    # Run sanitization
    results = run_sanitization_pipeline(notes_dir, detection_file, output_dir)
    
    print("✅ Sanitization pipeline complete!")
    print("\nNext steps:")
    print("  1. Review sanitized notes in outputs/sanitized/")
    print("  2. Compare methods in sanitization_summary.json")
    print("  3. Document findings in thesis Chapter 4")


if __name__ == "__main__":
    main()
