from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
import os
import re
import requests
from urllib.parse import urljoin

def download_irs_pdf(pdf_url: str, output_path: str = 'data/p535--2022.pdf'):
    """Download the IRS Publication 535 PDF from the given URL."""
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        response = requests.get(pdf_url, stream=True, timeout=10)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded Publication 535 PDF to {output_path}")
        return output_path
    except requests.RequestException as e:
        print(f"Error downloading PDF from {pdf_url}: {e}")
        return None

def parse_irs_pdf(pdf_path: str):
    """Parse IRS Publication 535 PDF to extract text."""
    try:
        import pdfplumber  # Import here to handle dynamic loading
        publication_data = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text and len(text.strip()) > 10:
                    publication_data.append({
                        "section": f"Page {page_num}",
                        "content": text.strip(),
                        "url": "https://www.irs.gov/pub/irs-prior/p535--2022.pdf",
                        "timestamp": pd.Timestamp.now().isoformat()
                    })
        print(f"Parsed {len(publication_data)} sections from {pdf_path}")
        return publication_data
    except ImportError:
        print("Error: pdfplumber is not installed. Install with 'pip install pdfplumber'")
        return []
    except Exception as e:
        print(f"Error parsing PDF {pdf_path}: {e}")
        return []

def scrape_irs_business_expense_resources(url: str = "https://www.irs.gov/publications/p535"):
    """Scrape IRS business expense resources, including Publication 535 PDF links and mappings, using Playwright."""
    resource_data = []
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    
    with sync_playwright() as p:
        # Launch browser in headed mode for debugging (set headless=True for production)
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # Navigate to the original URL (will redirect to guide-to-business-expense-resources)
            page.goto(url)
            time.sleep(2)  # Respect server response time (avoid rate limiting)

            # Get the redirected URL
            redirected_url = page.url
            print(f"Redirected to: {redirected_url}")

            # Wait for dynamic content
            page.wait_for_load_state("networkidle")

            # Get page content after redirection
            page_content = page.content()
            soup = BeautifulSoup(page_content, 'html.parser')

            # Debugging: Print the page title and some HTML
            print(f"Page Title: {soup.title.text if soup.title else 'No title found'}")
            print("Sample HTML:", soup.prettify()[:1000])

            # Try multiple possible selectors for HTML content
            possible_selectors = [
                ('div', {'class': 'usa-content'}),
                ('section', {'class': 'irs-publication'}),
                ('div', {'class': 'irs-guide-section'}),
                ('div', {'class': 'content'}),
                ('main', {}),
            ]

            found_content = False
            for tag, attrs in possible_selectors:
                sections = soup.find_all(tag, attrs)
                if sections:
                    print(f"Found sections with {tag} and {attrs}")
                    found_content = True
                    break

            # Extract HTML content and links
            if found_content:
                for section in sections:
                    heading = section.find('h1') or section.find('h2') or section.find('h3')
                    heading_text = heading.get_text(strip=True) if heading else "No Heading"

                    paragraphs = section.find_all('p')
                    content = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

                    links = section.find_all('a', href=True)
                    link_data = []
                    for link in links:
                        href = urljoin(redirected_url, link['href'])
                        if 'pub535' in href.lower() or 'business expense' in link.get_text(strip=True).lower():
                            link_data.append({
                                "url": href,
                                "text": link.get_text(strip=True) or "Link to Publication 535"
                            })

                    if content or link_data:
                        resource_data.append({
                            "heading": heading_text,
                            "content": content if content else "No content",
                            "links": link_data,
                            "url": redirected_url,
                            "timestamp": pd.Timestamp.now().isoformat()
                        })

            # Fallback: Look for PDF links explicitly (e.g., Publication 535 2022 PDF)
            if not found_content:
                print("No sections found. Checking for PDF links...")
                pdf_links = soup.find_all('a', href=re.compile(r'p535.*\.pdf'))
                if pdf_links:
                    for link in pdf_links:
                        pdf_url = urljoin(redirected_url, link['href'])
                        print(f"Found PDF link: {pdf_url}")
                        pdf_path = download_irs_pdf(pdf_url)
                        if pdf_path:
                            print(f"Attempting to parse PDF at {pdf_path}")
                            pdf_data = parse_irs_pdf(pdf_path)
                            resource_data.extend(pdf_data)
                        else:
                            print(f"Failed to download PDF from {pdf_url}")
                else:
                    print("No PDF links or sections found. Manual download or PDF parsing required.")

            # Save to JSON and CSV in the data directory
            json_path = os.path.join(output_dir, 'irs_business_expense_resources.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(resource_data, f, indent=4)

            csv_path = os.path.join(output_dir, 'irs_business_expense_resources.csv')
            df = pd.DataFrame(resource_data)
            df.to_csv(csv_path, index=False)

            print(f"Scraped {len(resource_data)} resources from IRS business expense guide and saved to '{json_path}' and '{csv_path}'")

        except Exception as e:
            print(f"Error scraping IRS business expense resources: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_irs_business_expense_resources()