import requests
import json
from datetime import datetime

# Priority drug categories
priority_drugs = [
    "efavirenz", "tenofovir", "lamivudine",   # ARVs
    "ibuprofen", "aspirin", "naproxen",       # NSAIDs
    "artemether", "lumefantrine", "chloroquine", # Antimalarials
    "isoniazid", "rifampicin", "ethambutol"   # TB drugs
]

OPENFDA_ENDPOINT = "https://api.fda.gov/drug/label.json"

def fetch_interactions(drug_name):
    """Fetch drug label data from OpenFDA for a given drug."""
    try:
        params = {"search": f"openfda.generic_name:{drug_name}", "limit": 1}
        response = requests.get(OPENFDA_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
        if "results" in data:
            return data["results"][0]
        return None
    except Exception as e:
        print(f"Error fetching {drug_name}: {e}")
        return None

def assign_risk_level(text):
    """Assign risk level based on keywords in interaction text."""
    text_lower = text.lower()
    if any(word in text_lower for word in ["contraindicated", "fatal", "life-threatening"]):
        return "CRITICAL"
    elif any(word in text_lower for word in ["avoid", "do not use", "dangerous"]):
        return "HIGH"
    elif any(word in text_lower for word in ["monitor", "caution", "risk"]):
        return "MODERATE"
    else:
        return "LOW"

def convert_to_schema(drug_name, openfda_data):
    """Convert OpenFDA data to OCML-DI schema format."""
    if not openfda_data:
        return None
    
    interactions_text = openfda_data.get("drug_interactions", ["No interaction data"])[0]
    risk_level = assign_risk_level(interactions_text)
    
    return {
        "drug": drug_name.capitalize(),
        "interaction_type": "drug-drug",  # default assumption
        "conflict_with": "See label details",
        "risk_level": risk_level,
        "outcome": interactions_text[:200] + "...",  # truncate for readability
        "recommendation": "Review full FDA label for detailed guidance",
        "population": "General",
        "dosage_threshold": "Not specified",
        "evidence_level": "OpenFDA drug label",
        "alternative_drugs": []
    }

def main():
    rules = []
    for drug in priority_drugs:
        print(f"Fetching interactions for {drug}...")
        data = fetch_interactions(drug)
        schema_entry = convert_to_schema(drug, data)
        if schema_entry:
            rules.append(schema_entry)
    
    output = {
        "metadata": {
            "source": "OpenFDA Drug Label API",
            "version": "2026",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "notes": "Auto-generated interaction rules for priority drugs"
        },
        "rules": rules
    }
    
    with open("who_essential_medicines_rules.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    
    print("✅ Interaction rules saved to who_essential_medicines_rules.json")

if __name__ == "__main__":
    main()
