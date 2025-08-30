#!/usr/bin/env python3
"""
MediaWiki Content Scraper for RAG System
Scrapes all articles from a MediaWiki instance and saves clean content for LLM processing
"""

import requests
import json
import time
import mwparserfromhell
from tqdm import tqdm
import os
import sys

class MediaWikiScraper:
    def __init__(self, base_url, delay=1.5):
        """
        Initialize scraper
        
        Args:
            base_url: Base wiki URL (e.g., "https://wiki.theleague-ns.com")
            delay: Delay between requests in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api.php"
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MediaWikiScraper/1.0 (Educational/Research Use)'
        })
        
    def get_all_page_titles(self):
        """Get list of all page titles from the wiki"""
        print("Fetching all page titles...")
        all_titles = []
        continue_token = None
        
        while True:
            params = {
                'action': 'query',
                'list': 'allpages',
                'aplimit': 500,  # Max allowed
                'format': 'json',
                'apnamespace': 0  # Main namespace only (articles)
            }
            
            if continue_token:
                params['apcontinue'] = continue_token
                
            try:
                response = self.session.get(self.api_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'query' in data and 'allpages' in data['query']:
                    pages = data['query']['allpages']
                    all_titles.extend([page['title'] for page in pages])
                    print(f"Collected {len(all_titles)} page titles...")
                    
                # Check for continuation
                if 'continue' in data and 'apcontinue' in data['continue']:
                    continue_token = data['continue']['apcontinue']
                else:
                    break
                    
            except Exception as e:
                print(f"Error fetching page titles: {e}")
                break
                
            time.sleep(self.delay)
            
        print(f"Found {len(all_titles)} total pages")
        return all_titles
    
    def get_page_content(self, title):
        """Get the raw wikitext content for a specific page"""
        params = {
            'action': 'query',
            'prop': 'revisions',
            'titles': title,
            'rvprop': 'content',
            'format': 'json',
            'rvslots': 'main'
        }
        
        try:
            response = self.session.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            for page_id, page_data in pages.items():
                if 'revisions' in page_data and page_data['revisions']:
                    content = page_data['revisions'][0]['slots']['main']['*']
                    return content
                    
        except Exception as e:
            print(f"Error fetching content for '{title}': {e}")
            
        return None
    
    def clean_wikitext(self, wikitext):
        """Return raw wikitext with minimal processing"""
        if not wikitext:
            return ""
        
        # Just return the raw content - let the LLM handle it
        return wikitext.strip()
    
    def scrape_all_content(self, output_file='wiki_content.json'):
        """Scrape all pages and save to JSON file"""
        # Get all page titles
        titles = self.get_all_page_titles()
        
        if not titles:
            print("No pages found!")
            return
        
        # Create output directory if needed
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        
        scraped_content = []
        
        print(f"\nScraping content from {len(titles)} pages...")
        
        for i, title in enumerate(tqdm(titles, desc="Scraping pages")):
            # Get raw content
            raw_content = self.get_page_content(title)
            
            if raw_content:
                # Clean the content
                clean_content = self.clean_wikitext(raw_content)
                
                if clean_content.strip():  # Only save if there's actual content
                    page_data = {
                        'title': title,
                        'url': f"{self.base_url}/wiki/{title.replace(' ', '_')}",
                        'content': clean_content,
                        'raw_content': raw_content,
                        'word_count': len(clean_content.split())
                    }
                    scraped_content.append(page_data)
            
            # Save progress periodically
            if (i + 1) % 100 == 0:
                with open(f"{output_file}.tmp", 'w', encoding='utf-8') as f:
                    json.dump(scraped_content, f, indent=2, ensure_ascii=False)
                print(f"\nSaved progress: {len(scraped_content)} pages processed")
            
            time.sleep(self.delay)
        
        # Final save
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(scraped_content, f, indent=2, ensure_ascii=False)
        
        # Clean up temp file
        if os.path.exists(f"{output_file}.tmp"):
            os.remove(f"{output_file}.tmp")
        
        print(f"\nScraping complete!")
        print(f"Scraped {len(scraped_content)} pages")
        print(f"Content saved to: {output_file}")
        
        # Print some stats
        total_words = sum(page['word_count'] for page in scraped_content)
        print(f"Total words: {total_words:,}")
        print(f"Average words per page: {total_words // len(scraped_content) if scraped_content else 0}")
        
        return scraped_content

def main():
    # Configuration
    WIKI_URL = "https://wiki.theleague-ns.com"
    OUTPUT_FILE = "league_wiki_content.json"
    REQUEST_DELAY = 1.5  # Be nice to their server
    
    print("MediaWiki Content Scraper for RAG System")
    print(f"Target: {WIKI_URL}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Delay: {REQUEST_DELAY}s between requests")
    print("-" * 50)
    
    # Create scraper and run
    scraper = MediaWikiScraper(WIKI_URL, delay=REQUEST_DELAY)
    
    try:
        content = scraper.scrape_all_content(OUTPUT_FILE)
        print(f"\n✅ Successfully scraped wiki content!")
        print(f"📁 Data saved to: {OUTPUT_FILE}")
        print(f"📊 Ready for RAG processing")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Scraping interrupted by user")
        print(f"Partial data may be saved in {OUTPUT_FILE}.tmp")
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
