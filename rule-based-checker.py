import requests
import PyPDF2
import json
import os
from datetime import datetime

# Step 1: Download IRS Publication 535 (2022)
def download_pdf(url, output_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded PDF to {output_path}")
    else:
        raise Exception(f"Failed to download PDF. Status code: {response.status_code}")

# Step 2: Extract text from PDF
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        pages = []
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            pages.append({
                "section": f"Page {page_num + 1}",
                "content": text,
                "url": pdf_path,
                "timestamp": datetime.now().isoformat()
            })
        return pages

# Step 3: Define Tax Rules
rules = [
    {
        "name": "mileage_rate",
        "description": "Identify IRS mileage rate for business travel",
        "action": "Compare against 2025 rate ($0.67/mile, per IRS updates)",
        "keywords": ["mileage", "cents per mile", "business use"],
        "rate": 0.67  # 2025 assumed rate for demo
    },
    {
        "name": "health_insurance_deduction",
        "description": "Identify self-employed health insurance deductions",
        "action": "Verify eligibility and limits for 2023+ tax years (up to net profit or $5,000)",
        "keywords": ["self-employed", "health insurance", "deduction"],
        "limit": 5000  # Example limit for demo
    },
    {
        "name": "tax_year_applicability",
        "description": "Identify applicable tax year for rules",
        "action": "Verify compliance with 2025 tax year rules",
        "keywords": ["tax year", "2022", "effective"]
    }
]

# Step 4: Rule-Based Checker
def apply_rules_to_content(pages, rules, user_input=None):
    results = []
    for page in pages:
        page_result = {
            "section": page["section"],
            "content": page["content"],
            "url": page["url"],
            "timestamp": page["timestamp"],
            "rule_results": []
        }
        
        for rule in rules:
            matches = []
            for keyword in rule["keywords"]:
                if keyword.lower() in page["content"].lower():
                    matches.append(keyword)
            
            rule_result = {
                "rule_name": rule["name"],
                "description": rule["description"],
                "action": rule["action"],
                "matches": matches
            }
            
            # Custom logic based on rule
            if rule["name"] == "mileage_rate" and user_input and "miles" in user_input:
                miles = user_input.get("miles", 0)
                rule_result["calculated_cost"] = f"${miles * rule['rate']:.2f}"
            
            if rule["name"] == "health_insurance_deduction" and user_input and "deduction" in user_input:
                claimed_amount = user_input.get("deduction", 0)
                if claimed_amount > rule["limit"]:
                    rule_result["compliance_risk"] = f"Claimed ${claimed_amount} exceeds limit of ${rule['limit']}"
            
            page_result["rule_results"].append(rule_result)
        
        page_result["timestamp"] = datetime.now().isoformat()
        results.append(page_result)
    
    return results

# Step 5: Save Results to JSON
def save_results_to_json(results, output_file):
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)
    print(f"Saved results to {output_file}")

# Main Execution
def main():
    pdf_url = "https://www.irs.gov/pub/irs-prior/p535--2022.pdf"
    pdf_path = "data/p535_2022.pdf"
    output_json = "data/irs_business_expense_analysis.json"
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Download the PDF
    try:
        download_pdf(pdf_url, pdf_path)
    except Exception as e:
        print(e)
        return
    
    # Extract text
    pages = extract_text_from_pdf(pdf_path)
    if not pages:
        print("No data extracted from PDF.")
        return
    
    # Example user input for testing rule application
    user_input = {
        "miles": 10000,  # Example: 10,000 miles driven
        "deduction": 10000  # Example: $10,000 claimed for health insurance
    }
    
    # Apply rules
    analysis_results = apply_rules_to_content(pages, rules, user_input)
    
    # Save results
    save_results_to_json(analysis_results, output_json)

if __name__ == "__main__":
    main()