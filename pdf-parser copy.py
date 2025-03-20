import pdfplumber
import json
import pandas as pd
import os

def parse_irs_pdf(pdf_path: str = 'data/p535--2022.pdf'):
    """Parse IRS Publication 535 PDF to extract text for Tax Compliance AI."""
    publication_data = []
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)  # Create data directory if it doesn’t exist
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text and len(text.strip()) > 10:  # Filter out empty or short text
                    publication_data.append({
                        "section": f"Page {page_num}",
                        "content": text.strip(),
                        "url": "https://www.irs.gov/pub/irs-prior/p535--2022.pdf",
                        "timestamp": pd.Timestamp.now().isoformat()
                    })
        
        # Save to JSON in the data directory
        json_path = os.path.join(output_dir, 'irs_publication_535_2022.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(publication_data, f, indent=4)

        # Save to CSV in the data directory
        csv_path = os.path.join(output_dir, 'irs_publication_535_2022.csv')
        df = pd.DataFrame(publication_data)
        df.to_csv(csv_path, index=False)

        print(f"Parsed {len(publication_data)} sections from IRS Publication 535 2022 PDF and saved to '{json_path}' and '{csv_path}'")
        return publication_data
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return []

if __name__ == "__main__":
    parse_irs_pdf()