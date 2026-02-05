import os
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

class CompanyScraper:
    def __init__(self, output_dir="Data/web_scraping"):
        self.output_dir = Path(__file__).parent.parent / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Using Wikipedia URLs as safe, public data sources
        self.targets = {
            "Amazon": "https://en.wikipedia.org/wiki/Amazon_(company)",
            "Flipkart": "https://en.wikipedia.org/wiki/Flipkart",
            "Google": "https://en.wikipedia.org/wiki/Google",
            "IBM": "https://en.wikipedia.org/wiki/IBM",
            "Tech_Mahindra": "https://en.wikipedia.org/wiki/Tech_Mahindra",
            "TCS": "https://en.wikipedia.org/wiki/Tata_Consultancy_Services",
            "Capgemini": "https://en.wikipedia.org/wiki/Capgemini",
            "Infosys": "https://en.wikipedia.org/wiki/Infosys",
            "Wipro": "https://en.wikipedia.org/wiki/Wipro",
            "Accenture": "https://en.wikipedia.org/wiki/Accenture"
        }

    def scrape_all(self):
        print(f"Starting scraping for {len(self.targets)} companies...")
        for name, url in self.targets.items():
            try:
                self.scrape_url(name, url)
            except Exception as e:
                print(f"Failed to scrape {name}: {e}")
        print("Scraping completed.")

    def scrape_url(self, name, url):
        print(f"Scraping {name} from {url}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error {response.status_code} fetching {url}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.find('h1', {'id': 'firstHeading'}).text if soup.find('h1', {'id': 'firstHeading'}) else name
        
        # Extract main content paragraphs (limit to first 10 for brevity in demo)
        content_div = soup.find('div', {'id': 'mw-content-text'})
        paragraphs = content_div.find_all('p') if content_div else []
        text_content = "\n".join([p.text.strip() for p in paragraphs[:10] if p.text.strip()])

        # Structure data
        data = {
            "company": name,
            "source_url": url,
            "title": title,
            "description": text_content,
            "scraped_at": str(response.headers.get('Date', ''))
        }
        
        self.save_to_json(name, data)

    def save_to_json(self, name, data):
        output_file = self.output_dir / f"{name}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"Saved data to {output_file}")

if __name__ == "__main__":
    scraper = CompanyScraper()
    scraper.scrape_all()
