import json

with open('data/tax_compliance_ai_results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

for result in results[:5]:  # Review first 5 results
    print(result)