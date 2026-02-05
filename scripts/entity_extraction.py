import json
import spacy
import re
from pathlib import Path

# Configuration
INPUT_FILE = Path(__file__).parent.parent / "normalized_chunks.json"
OUTPUT_FILE = Path(__file__).parent.parent / "extracted_entities.json"
SPACY_MODEL = "en_core_web_sm"

# --- 1. Domain Specific Mappings (HR & General) ---

# Map keys found in normalized text to Entity Labels
KEY_TO_LABEL = {
    "Employee Name": "PERSON",
    "Employee Name": "PERSON",
    "Name": "PERSON",
    "Job Title": "JOB_ROLE",
    "JobTitle": "JOB_ROLE",
    "JobRole": "JOB_ROLE",
    "Role": "JOB_ROLE",
    "Department": "ORG", 
    "Company": "ORG",
    "Location": "GPE",
    "City": "GPE",
    "State": "GPE",
    "Country": "GPE",
    "EducationField": "FIELD_OF_STUDY",
    "University": "ORG",
    "Gender": "DEMOGRAPHIC",
    "MaritalStatus": "DEMOGRAPHIC",
    "Over18": "DEMOGRAPHIC",
    "Education": "EDUCATION_LEVEL",
    "BusinessTravel": "CATEGORY",
    "Attrition": "STATUS" # or CATEGORY
}

# Generic Ignore Keys (Metrics, Dates, numeric fields)
# We ignore the VALUES associated with these keys if they are just numbers,
# but sometimes we might want to keep them if they are categorical?
# For now, we only extract ENTITIES (Persons, Orgs, GPEs, Roles).
IGNORE_KEYS = {
    "Employee ID", "EmployeeNumber", "Salary INR", "Join Date", "Age", 
    "DailyRate", "MonthlyIncome", "MonthlyRate", "HourlyRate", "Distance", 
    "DistanceFromHome", "NumCompaniesWorked", "PercentSalaryHike", 
    "TotalWorkingYears", "TrainingTimesLastYear", "YearsAtCompany", 
    "YearsInCurrentRole", "YearsSinceLastPromotion", "YearsWithCurrManager",
    "JobLevel", "StockOptionLevel", "StandardHours", "EmployeeCount",
    "EnvironmentSatisfaction", "JobInvolvement", "JobSatisfaction",
    "PerformanceRating", "RelationshipSatisfaction", "WorkLifeBalance",
    "BusinessTravel", "EducationField", "JobRole", "MaritalStatus", "Over18", 
    "StandardHours", "Gender", "Attrition", "Department", "Education"
}

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

def load_data(filepath):
    if not filepath.exists():
        print(f"Error: {filepath} not found.")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_text(text):
    """
    Remove URLs and basic cleanup.
    """
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def process_data(data):
    try:
        nlp = spacy.load(SPACY_MODEL)
    except OSError:
        from spacy.cli import download
        print(f"Downloading {SPACY_MODEL}...")
        download(SPACY_MODEL)
        nlp = spacy.load(SPACY_MODEL)

    nlp.max_length = 2000000 
    
    processed_results = []
    
    for doc_obj in data:
        doc_filename = doc_obj.get("document_id", "unknown")
        chunks = doc_obj.get("normalized_chunks", [])
        
        unique_entities = {}
        
        for chunk in chunks:
            text = chunk.get("text", "")
            if not text:
                continue
                
            # 1. Structured Key-Value Extraction (Heuristics)
            # We assume normalized text often follows "Key: Value" pattern.
            # We split by sequences that look like ", Key:" to separate pairs.
            # This regex looks for a comma, optional space, then a word followed by colon.
            parts = re.split(r',\s*(?=[a-zA-Z0-9_ ]+:)', text) 
            
            for part in parts:
                if ":" in part:
                    # Split only on first colon
                    try:
                        k, v = part.split(":", 1)
                    except ValueError:
                        continue
                        
                    k = k.strip()
                    v = v.strip(" .") # clean trailing dot
                    
                    if not v or k in IGNORE_KEYS or v.lower() == "nan":
                        continue
                    
                    v_clean = clean_text(v).strip(' :;.,')
                    if not v_clean or v_clean.lower() in GENERIC_ENTITIES:
                        continue

                    # Check if Key is in our map
                    label = KEY_TO_LABEL.get(k)
                    
                    # Fuzzy match or normalization for keys?
                    if not label:
                        # Heuristics
                        if "Name" in k: label = "PERSON"
                        elif "Location" in k: label = "GPE"
                        elif "Department" in k: label = "ORG"
                        elif "Company" in k: label = "ORG"
                        elif "Title" in k: 
                            label = "PRODUCT" if "nike" in doc_filename.lower() else "JOB_ROLE"
                    
                    if label:
                        unique_entities[v] = {
                            "text": v,
                            "label": label,
                            "source": "structured" 
                        }
                        
            # 2. Run NLP for unstructured bits or missed entities
            # We run NLP on the whole text to capture things even if Key-Value parsing missed them
            # or if there is narrative text.
            doc = nlp(text)
            for ent in doc.ents:
                clean_ent = clean_text(ent.text)
                if len(clean_ent) < 2: continue
                
                # Filter out numeric cardinal/dates if not interesting
                if ent.label_ in ["CARDINAL", "DATE", "TIME", "PERCENT", "MONEY", "QUANTITY", "ORDINAL"]:
                     continue
                
                # Filter out generic terms and headers misclassified as entities
                lower_ent = clean_ent.lower()
                if lower_ent in GENERIC_ENTITIES or clean_ent in IGNORE_KEYS:
                    continue
                
                # Check for "Header: Value" pollution in NLP extraction
                if ":" in clean_ent:
                    # If it's something like "Department: Engineering", we already handle it in structured.
                    # If NLP picks it up, it's often messy.
                    continue

                # If we already found this text via Structured extraction, skip (Trust structured label)
                if clean_ent in unique_entities:
                    continue
                
                unique_entities[clean_ent] = {
                    "text": clean_ent,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                }
        
        if unique_entities:
            processed_results.append({
                "source_document": doc_filename,
                "entities": list(unique_entities.values())
            })
            
    return processed_results

def main():
    print("Loading validated data...")
    try:
        data = load_data(INPUT_FILE)
    except Exception as e:
        print(f"Failed to load data: {e}")
        return

    if not data:
        print("No data to process.")
        return

    print("Extracting entities with HR/General rules...")
    results = process_data(data)
    
    print(f"Saving {len(results)} documents with entities to {OUTPUT_FILE}...")
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
        print("Done.")
    except Exception as e:
        print(f"Failed to save output: {e}")

if __name__ == "__main__":
    main()
