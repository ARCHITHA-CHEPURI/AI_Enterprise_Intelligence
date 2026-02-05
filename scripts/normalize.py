import json
import re
import spacy
import sys
import os

# Ensure spacy model is loaded
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spacy model...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

INPUT_FILE = "ingested_data.json"
OUTPUT_FILE = "normalized_chunks.json"

def clean_text(text):
    """
    Refined noise removal.
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove common boilerplate/noise
    # Signatures, disclaimers (heuristic)
    text = re.sub(r'(?i)sent from my \w+', '', text)
    text = re.sub(r'(?i)unsubscribe', '', text)
    
    # Remove standalone page numbers (e.g., "Page 10 of 20")
    text = re.sub(r'(?i)page \d+ of \d+', '', text)
    
    # Remove formatting artifacts like bullet points at start of line
    text = re.sub(r'^\s*[-*•]\s+', '', text)

    return text.strip()

# Field mappings based on Report Section
SECTION_MAPPINGS = {
    "AVERAGE_ORDER_VALUE": {
        "Metric1": "Average_Order_Value", 
        "Metric2": "Total_Orders", 
        "Metric3": "Total_Gross_Sales", 
        "Metric4": "Avg_Rating" 
    },
    "CATEGORY_PERFORMANCE": {
        "Metric1": "Total_Revenue", 
        "Metric2": "Units_Sold", 
        "Metric3": "Avg_Order_Value", 
        "Metric4": "Avg_Rating"
    },
    "COD_VS_DIGITAL_PAYMENTS": {
         "Metric1": "Transaction_Count", 
         "Metric2": "Process_Time_Sec", 
         "Metric3": "Total_Value",
         "Metric4": "Avg_Rating"
    },
    "CUSTOMER_COUNT_BY_STATE": {
        "Metric1": "Male_Customer_Count",
        "Metric2": "Female_Customer_Count",
        "Metric3": "Global_AOV",
        "Metric4": "Global_Rating"
    },
    "CUSTOMER_PURCHASE_FREQUENCY": {
        "Metric1": "Purchase_Count",
        "Metric2": "Total_Spend",
        "Metric3": "Global_AOV",
        "Metric4": "Global_Rating"
    },
    "DELIVERY_SUCCESS_RATE": {
        "Metric1": "Order_Count",
        "Metric2": "Percentage",
        "Metric3": "Total_Value"
    },
    "HIGH_VALUE_ORDERS": {
        "Metric1": "Order_Count",
        "Metric2": "Total_Value"
    },
    "MONTHLY_SALES_TRENDS": {
        "Metric1": "Total_Sales",
        "Metric2": "Total_Orders",
        "Metric3": "Average_Order_Value",
        "Metric4": "Avg_Rating" 
    },
    "PAYMENT_METHOD_PREFERENCES": {
        "Metric1": "Usage_Count",
        "Metric2": "Usage_Percentage",
        "Metric3": "Total_Transaction_Value"
    },
    "PRODUCT_QUANTITY_DISTRIBUTION": {
        "Metric1": "Scale_Rating", 
        "Metric2": "Quantity_Count"
    },
    "RETURNS_BY_CATEGORY": {
        "Metric1": "Return_Count",
        "Metric2": "Refund_Value",
        "Metric3": "Return_Rate_Percentage"
    },
    "STATE_WISE_SALES": {
        "Metric1": "Total_Sales",
        "Metric2": "Female_Customers", 
        "Metric3": "Male_Customers"
    },
    "TOP_REVENUE_STATES_2025": {
        "Metric1": "Total_Revenue",
        "Metric2": "Order_Count",
        "Metric3": "Avg_Revenue_Per_Customer"
    },
    "TOP_SELLING_PRODUCTS": {
        "Metric1": "Total_Revenue",
        "Metric2": "Units_Sold"
    }
}

def normalize_csv(content):
    """
    Convert CSV rows (list of dicts) into sentences dynamically
    using context-aware mappings for field names.
    """
    sentences = []
    if isinstance(content, list):
        for row in content:
            if not isinstance(row, dict):
                continue
            
            # Filter empty values
            clean_row = {k: v for k, v in row.items() if v is not None and str(v).strip() != ""}
            if not clean_row:
                continue

            # Identify Section for Mapping
            section_name = clean_row.get("Report Section", clean_row.get("Report_Section", "")).strip()
            
            parts = []
            
            # Prioritize Dimension/Section first for readability
            if "Report Section" in clean_row:
                term = clean_row.pop("Report Section")
                parts.append(f"Report Section: {term}")
            elif "Report_Section" in clean_row:
                term = clean_row.pop("Report_Section")
                parts.append(f"Report Section: {term}")
                
            if "Dimension" in clean_row:
                term = clean_row.pop("Dimension")
                parts.append(f"Dimension: {term}")

            # Process remaining keys
            for k, v in clean_row.items():
                k_clean = k.strip()
                v_str = str(v).strip()
                
                # Apply Mapping if exists
                if section_name in SECTION_MAPPINGS and k_clean in SECTION_MAPPINGS[section_name]:
                    k_clean = SECTION_MAPPINGS[section_name][k_clean]
                else:
                    # Fallback cleanup
                    k_clean = k_clean.replace("_", " ") 

                parts.append(f"{k_clean}: {v_str}")
            
            if parts:
                sentence = ", ".join(parts) + "."
                sentences.append(sentence)

    return sentences

def normalize_general_text(content, source_type):
    """
    Handle generic text content (Email, PDF, Web).
    """
    raw_text = ""
    # Extract text content based on likely structure
    if isinstance(content, str):
        raw_text = content
    elif isinstance(content, dict):
        # Try to find relevant text fields
        if source_type == 'email':
            subject = content.get("subject", "")
            body = content.get("body", "")
            raw_text = f"Subject: {subject}.\n{body}"
        else:
            # Join all string values
            parts = [str(v) for v in content.values() if isinstance(v, (str, int, float))]
            raw_text = " ".join(parts)
    elif isinstance(content, list):
        # List of strings or dicts
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                 # Improved: preserve field names for better NER/KG context
                 item_parts = [f"{k}: {v}" for k, v in item.items() if v is not None and str(v).strip() != ""]
                 if item_parts:
                     parts.append(", ".join(item_parts) + ".")
            else:
                parts.append(str(item))
        raw_text = " ".join(parts)
    
    cleaned_text = clean_text(raw_text)
    
    # Sentence splitting
    doc = nlp(cleaned_text)
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 5]
    
    return sentences

def get_topics(text):
    """
    Simple placeholder for topic extraction.
    extracts Nouns/Proper Nouns as potential topics.
    """
    doc = nlp(text)
    topics = list(set([token.text for token in doc if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop]))
    # Return top 5 frequent or just distinct ones
    return topics[:5] # Limit to 5

def estimate_confidence(text, source_type):
    """
    Estimate confidence based on text quality.
    """
    if not text or len(text) < 10:
        return "low"
    
    # If it's a CSV converted to text, it's usually high factual confidence
    if source_type == 'csv':
        return "high"
        
    return "medium"

def chunk_content(sentences, min_words=80, max_words=200):
    """
    Semantic chunking based on word count targets.
    """
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for sent in sentences:
        word_count = len(sent.split())
        
        # If adding this sentence exceeds max, save current chunk (if it has content)
        if current_word_count + word_count > max_words and current_chunk:
             chunks.append(" ".join(current_chunk))
             current_chunk = []
             current_word_count = 0

        current_chunk.append(sent)
        current_word_count += word_count
        
        # If we have enough words, start a new chunk? 
        # Requirement: "Split chunks when topic changes... Ideal 80-200 words"
        # Since we don't have deep topic change detection, we'll try to fill to min_words
        # But if we go over max, we forced a split above.
        
        # If we are effectively "full" (between min and max), we CAN split, but maybe we should wait for max
        # or a natural break? For now, let's fill up to higher end to keep context together.
        
    # Add remainder
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

def process_data():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"Reading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    final_output = {
        "document_id": "combined_ingestion", # This might be wrong per schema
         # Wait, the SCHEMA request was:
         # { "document_id": "...", "source_type": "...", "normalized_chunks": [...] }
         # This implies One JSON Object per document?
         # Or a LIST of these objects.
         # The User input example shows a single object.
         # But we have multiple documents.
         # I will output a LIST of these objects.
    }
    
    output_list = []

    for entry in data:
        filename = entry.get("filename", "unknown_file")
        file_type = entry.get("file_type", "unknown")
        content = entry.get("content")

        print(f"Processing {filename} ({file_type})...")

        normalized_sentences = []

        if file_type == 'csv':
            normalized_sentences = normalize_csv(content)
        else:
            normalized_sentences = normalize_general_text(content, file_type)

        # Skip if no content
        if not normalized_sentences:
            continue

        # Chunking
        chunk_texts = chunk_content(normalized_sentences, min_words=80, max_words=200)
        
        normalized_chunks_list = []
        for idx, txt in enumerate(chunk_texts):
            normalized_chunks_list.append({
                "chunk_id": f"norm_chunk_{idx+1}",
                "text": txt,
                "topics": get_topics(txt),
                "confidence": estimate_confidence(txt, file_type)
            })
            
        doc_obj = {
            "document_id": filename,
            "source_type": file_type,
            "normalized_chunks": normalized_chunks_list
        }
        output_list.append(doc_obj)

    print(f"Writing structure to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_list, f, indent=2)
    print("Done.")

if __name__ == "__main__":
    process_data()
