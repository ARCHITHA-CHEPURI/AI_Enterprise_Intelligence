import json
from pathlib import Path
import re

# Configuration
NORMALIZED_FILE = Path(__file__).parent.parent / "normalized_chunks.json"
ENTITIES_FILE = Path(__file__).parent.parent / "extracted_entities.json"
OUTPUT_FILE = Path(__file__).parent.parent / "relationship_extraction_output.json"

def load_json(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_entities_for_doc(doc_id, all_entities_data):
    for doc in all_entities_data:
        if doc.get("source_document") == doc_id:
            return doc.get("entities", [])
    return []

# ALLOWED SHORT ACRONYMS (Keep these even if short)
ALLOWED_SHORT = {"AI", "US", "UK", "HR", "IT", "NY", "EU", "UN", "GM", "VP", "CEO", "CFO", "CTO", "AWS", "SAP", "IBM"}

# BLOCKLIST - ALL LOWERCASE
BLOCKLIST = {
    "al", "li", "lo", "la", "le", "el", "et", "en", "de", "da", "di", "du", "po", "ga", "ref",
    "tim", "tom", "jim", "bob", "sam", "dan", "ben", 
    "gif", "jpg", "png", "bmp", "pdf", "log", "exe", "bin", "dat", "txt", "bee", "xp", "rca",
    "cloud computing", "server", "database", "analytics", "software", "infrastructure", 
    "ai", "deployment", "hasham premji's", "refer", "oracle", "linux ai", "deploying ai",
    "ps", "con", "prn", "aux", "nul", "com1",
    "section", "chapter", "page", "paragraph", "table", "figure",
    "gpg", "hacksaw", "pgp", "gpg hacksaw",
    "misc", "lib", "ge", "nec", "un", "ec", "p s", "s s", "sa s", "ft", "nl", "usr", "fort", "conn", "mag",
    "free s p join now", "join now", "forteana", "state", "fed", "sec", "nit", "irs", "cia", "epa",
    "logwrite misc", "lib s development", "peter pahern", "raul jurado", "martin adamson", # Specific bad lowercase names
    "department", "jobrole", "businesstravel", "educationfield", "maritalstatus", "gender", 
    "attrition", "standardhours", "yearsatcompany", "hourlyrate", "monthlyrate", 
    "monthlyincome", "joblevel", "employeecount", "education", "years in current role",
    "years since last promotion", "years with curr manager", "training times last year",
    "num companies worked", "percent salary hike", "total working years"
}

def is_valid_text(text):
    """
    Returns True if text is clean English-like text.
    Rejects:
    - Multi-byte characters (Chinese/Korean/etc)
    - Garbage patterns like xNUMBER, mailto, etc
    """
    # 1. Non-ASCII / Foreign text check
    if re.search(r'[\u4e00-\u9fff\u3000-\u303f\uac00-\ud7af]', text):
        return False
        
    # 2. Garbage Patterns
    if re.match(r'^x\d+$', text, re.IGNORECASE): # xNUMBER
        return False
    if "NUMBER" in text: # Global ban on NUMBER placeholder artifacts
        return False
    if "mailto" in text.lower():
        return False
    if "http" in text.lower() or "www." in text.lower():
        return False
        
    return True

def clean_entity(txt):
    txt = re.sub(r'\[\d+(?:,\s*\d+)*\]', '', txt) # remove [1], [1,2]
    # Remove surrounding quotes/brackets and COLONS
    txt = txt.strip(' "\'()[]{}.,-:;')
    # If it ends with a colon (even if not strictly at the end after stripping), clean it
    txt = re.sub(r':$', '', txt)
    return txt.strip()

# PROXIMITY THRESHOLDS
PROXIMITY_CSV = 120
PROXIMITY_NARRATIVE = 500

def is_valid_subject(text, label):
    """
    Stricter check for entities that can be subjects (PERSON/ORG).
    Avoids common NER misclassifications.
    """
    lower = text.lower()
    
    # Generic blocklist for subjects
    SUBJECT_BLOCKLIST = [
        "annual report", "management discussion", "consolidated financial",
        "financial statements", "intellectual property", "independent auditor",
        "stockholders", "directors", "officers", "employees", "customer", 
        "partner", "client", "business unit", "segment", "division",
        "the consolidated", "the management", "responsibility", "information",
        "accounting", "finance", "audit", "notes", "statement", "overview",
        "department", "jobrole", "businesstravel", "educationfield", 
        "maritalstatus", "gender", "attrition", "standardhours",
        "employee count", "job level", "years at company", "hourly rate",
        "monthly rate", "monthly income", "environment satisfaction",
        "job involvement", "job satisfaction", "performance rating",
        "relationship satisfaction", "work life balance", "position",
        "category", "status", "metric", "value", "data", "department:", "job title:", "role:"
    ]
    
    if any(lower == x for x in SUBJECT_BLOCKLIST) or any(lower.startswith(x) for x in SUBJECT_BLOCKLIST):
        return False

    if label == 'PERSON':
        # Reject common high-tech keywords often misclassified as people
        if any(x in lower for x in ["ai", "computing", "analysis", "server", "software", "infrastructure", "cloud", "data", "report", "deploy", "system", "quantum"]):
            return False
    
    return True

def extract_relationships_heuristics(doc_id, chunks, doc_entities):
    relationships = []
    
    # Adaptive Proximity
    is_csv = doc_id.lower().endswith('.csv')
    prox_limit = PROXIMITY_CSV if is_csv else PROXIMITY_NARRATIVE
    
    for chunk in chunks:
        text = chunk.get("text", "")
        if not text:
            continue
            
        # 1. Gather all unique occurrences of valid entities with their positions
        # Note: entities in doc_entities might mention 'start'/'end' relative to chunk text?
        # In entity_extraction.py, we only store text/label for structured, 
        # but for NLP bits we store start/end.
        # Here we re-locate them in the chunk text to get reliable offsets.
        
        candidates = []
        for ent in doc_entities:
            clean_txt = clean_entity(ent['text'])
            if not clean_txt or not is_valid_text(clean_txt):
                continue
            
            lower_txt = clean_txt.lower()
            if lower_txt in BLOCKLIST:
                 continue
            
            # Short Word Filter
            if len(clean_txt) < 4 and clean_txt.upper() not in ALLOWED_SHORT:
                continue

            # PERSON STRICTNESS
            if ent['label'] == 'PERSON':
                if not is_valid_subject(clean_txt, 'PERSON'):
                    continue
                parts = clean_txt.split()
                if len(parts) < 2 or not clean_txt[0].isupper():
                    continue

            # Find all occurrences in this chunk
            for m in re.finditer(re.escape(clean_txt), text):
                candidates.append({
                    "text": clean_txt,
                    "label": ent['label'],
                    "start": m.start(),
                    "end": m.end()
                })
        
        # 2. Block generic terms from being candidates
        GENERIC_ENTITIES = {
            "department", "metric", "value", "category", "status", "data", "information",
            "employee", "employees", "person", "persons", "user", "users",
            "system", "systems", "application", "applications", "management",
            "report", "reports", "annual report", "financial statement", "notes",
            "business", "businesses", "company", "companies", "organization", "organizations",
            "jobrole", "businesstravel", "educationfield", "maritalstatus", "gender", 
            "attrition", "standardhours", "yearsatcompany", "hourlyrate", "monthlyrate", 
            "monthlyincome", "joblevel", "employeecount", "environment satisfaction",
            "job involvement", "job satisfaction", "performance rating",
            "relationship satisfaction", "work life balance"
        }
        
        filtered_candidates = []
        for c in candidates:
            lower_c = c['text'].lower()
            # If the candidate text EXACTLY matches a generic term
            if lower_c in GENERIC_ENTITIES:
                continue
            # If the candidate text CONTAINS any blocklisted term (aggressive filtering)
            if any(term in lower_c for term in BLOCKLIST):
                # But allow some acronyms if they are part of a larger name? 
                # No, for noise reduction, let's be strict.
                continue
            # Specifically block headers with colons
            if ":" in lower_c:
                continue
            filtered_candidates.append(c)
        candidates = filtered_candidates

        # 3. Fix Tech Orgs misclassified as GPE
        for c in candidates:
            if c['label'] == 'GPE':
                if c['text'].lower() in ["cisco", "microsoft", "google", "ibm", "oracle", "sap", "aws", "azure", "red hat", "salesforce", "intel", "dell"]:
                    c['label'] = 'ORG'

        # 3. Proximity-Based Linking
        # Subjects: PERSON, ORG
        subjects = [c for c in candidates if c['label'] in ['PERSON', 'ORG']]
        subjects = [s for s in subjects if is_valid_subject(s['text'], s['label'])]
        
        for subj in subjects:
            for obj in candidates:
                if subj == obj: continue
                
                # Proximity check
                dist = min(abs(subj['start'] - obj['end']), abs(obj['start'] - subj['end']))
                if dist > prox_limit:
                    continue
                
                s_txt = subj['text']
                o_txt = obj['text']
                s_lab = subj['label']
                o_lab = obj['label']

                # Rules for Relationship Types
                
                # PERSON -> ROLE
                if s_lab == 'PERSON' and o_lab == 'JOB_ROLE':
                    relationships.append({"subject": s_txt, "predicate": "WORKS_AS", "object": o_txt})
                
                # PERSON -> ORG (Works at)
                if s_lab == 'PERSON' and o_lab == 'ORG' and s_txt != o_txt:
                    relationships.append({"subject": s_txt, "predicate": "WORKS_AT", "object": o_txt})

                # ORG -> GPE (Located in)
                if s_lab == 'ORG' and o_lab == 'GPE':
                    relationships.append({"subject": s_txt, "predicate": "LOCATED_IN", "object": o_txt})
                
                # PERSON -> GPE (Located in / Based in)
                if s_lab == 'PERSON' and o_lab == 'GPE':
                    relationships.append({"subject": s_txt, "predicate": "LOCATED_IN", "object": o_txt})

                # ORG -> PRODUCT (Provides/Develops)
                if s_lab == 'ORG' and o_lab == 'PRODUCT':
                    relationships.append({"subject": s_txt, "predicate": "PROVIDES", "object": o_txt})
                
                # PERSON -> FIELD_OF_STUDY
                if s_lab == 'PERSON' and o_lab == 'FIELD_OF_STUDY':
                    relationships.append({"subject": s_txt, "predicate": "STUDIED", "object": o_txt})

    return relationships

def main():
    print("Loading data for Rule-Based Extraction (Final Clean Mode v2)...")
    normalized_data = load_json(NORMALIZED_FILE)
    entities_data = load_json(ENTITIES_FILE)
    
    if not normalized_data or not entities_data:
        print("Missing input files.")
        return
    
    output_results = []
    total_triples = 0
    
    for doc_obj in normalized_data:
        doc_id = doc_obj.get("document_id")
        chunks = doc_obj.get("normalized_chunks", [])
        
        doc_entities = get_entities_for_doc(doc_id, entities_data)
        
        if not doc_entities:
            continue
            
        doc_rels = extract_relationships_heuristics(doc_id, chunks, doc_entities)
        
        # Deduplicate and Final Noise Filter
        unique_rels = []
        seen = set()
        for r in doc_rels:
            s_low = r['subject'].lower()
            o_low = r['object'].lower()
            
            # Final Safety Net Filter
            is_noise = False
            for term in BLOCKLIST:
                if term in s_low or term in o_low:
                    is_noise = True
                    break
            if is_noise:
                continue
                
            # Create tuple signature
            sig = (r['subject'], r['predicate'], r['object'])
            if sig not in seen and r['subject'] != r['object']: 
                seen.add(sig)
                unique_rels.append(r)
        
        if unique_rels:
            output_results.append({
                "document_id": doc_id,
                "relationships": unique_rels
            })
            total_triples += len(unique_rels)
            
    print(f"Extracted {total_triples} relationships from {len(output_results)} documents.")
    print(f"Saving to {OUTPUT_FILE}...")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_results, f, indent=4)
    print("Done.")

if __name__ == "__main__":
    main()
