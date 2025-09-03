#!/usr/bin/env python3
"""
Convert scraped wiki JSON to individual documents for Open WebUI
Splits the large JSON file into separate text files that Open WebUI can import
"""

import json
import os
import re
from pathlib import Path

def sanitize_filename(title):
    """Convert wiki page title to safe filename"""
    # Remove or replace characters that are problematic in filenames
    filename = re.sub(r'[<>:"/\\|?*]', '_', title)
    filename = re.sub(r'\s+', '_', filename)  # Replace spaces with underscores
    filename = filename.strip('._')  # Remove leading/trailing dots and underscores
    
    # Limit length to avoid filesystem issues
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename

def convert_json_to_documents(json_file, output_dir="wiki_documents"):
    """
    Convert JSON file to individual document files for Open WebUI
    
    Args:
        json_file: Path to your league_wiki_content.json file
        output_dir: Directory to save individual document files
    """
    
    print(f"Converting {json_file} to individual documents...")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Load the JSON data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            wiki_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {json_file}")
        print("Make sure the wiki scraping is complete and the file exists.")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {json_file}: {e}")
        return
    
    if not isinstance(wiki_data, list):
        print(f"Error: Expected a list of articles, got {type(wiki_data)}")
        return
    
    print(f"Found {len(wiki_data)} articles to convert")
    
    converted_count = 0
    skipped_count = 0
    
    for article in wiki_data:
        try:
            title = article.get('title', 'Untitled')
            content = article.get('content', '')
            url = article.get('url', '')
            word_count = article.get('word_count', 0)
            
            # Skip articles with no content
            if not content.strip():
                skipped_count += 1
                continue
            
            # Create filename
            filename = sanitize_filename(title) + '.txt'
            file_path = output_path / filename
            
            # Create document content with metadata
            document_content = f"""TITLE: {title}
URL: {url}
WORD COUNT: {word_count}

CONTENT:
{content}
"""
            
            # Write the document
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(document_content)
            
            converted_count += 1
            
            # Progress update every 500 files
            if converted_count % 500 == 0:
                print(f"Converted {converted_count} documents...")
                
        except Exception as e:
            print(f"Error processing article '{title}': {e}")
            skipped_count += 1
            continue
    
    print(f"\nConversion complete!")
    print(f"✅ Converted: {converted_count} documents")
    print(f"⚠️  Skipped: {skipped_count} documents (empty or errors)")
    print(f"📁 Documents saved to: {output_path.absolute()}")
    print(f"📊 Total size: {sum(f.stat().st_size for f in output_path.glob('*.txt') if f.is_file()) / 1024 / 1024:.1f} MB")
    
    return output_path

def create_batch_upload_info(output_dir="wiki_documents"):
    """Create instructions for batch uploading to Open WebUI"""
    output_path = Path(output_dir)
    
    if not output_path.exists():
        print(f"Directory {output_dir} doesn't exist. Run conversion first.")
        return
    
    txt_files = list(output_path.glob('*.txt'))
    
    info_content = f"""OPEN WEBUI UPLOAD INSTRUCTIONS
====================================

Generated documents: {len(txt_files)} files
Location: {output_path.absolute()}
Total size: {sum(f.stat().st_size for f in txt_files) / 1024 / 1024:.1f} MB

UPLOAD METHODS:

Method 1: Web Interface (Recommended for smaller batches)
1. Open Open WebUI in browser (http://localhost:3000)
2. Go to Admin Panel → Knowledge Base
3. Create new collection: "League NS Wiki"
4. Upload documents in batches (select multiple .txt files)
5. Process and index

Method 2: Bulk Upload (For all files)
1. Zip all documents: zip -r wiki_docs.zip {output_dir}/
2. Use Open WebUI's bulk import feature
3. Or use API if available

Method 3: API Upload (Advanced)
Use the Open WebUI API to programmatically upload all documents.

SYSTEM PROMPT RECOMMENDATION:
============================
Set this as your system prompt in Open WebUI:

"You are a search assistant for the League NS roleplay wiki. You must ONLY answer questions using information from the provided wiki context about the fictional countries and world in this roleplay setting. 

CRITICAL RULES:
- If the wiki context doesn't contain the answer, say 'I don't have that information in the wiki'
- Never use your general knowledge about the real world
- Never mention real countries, real wars, or real events unless they appear in the wiki
- All answers must be sourced from the League NS wiki content provided to you
- When asked about wars, countries, leaders, etc., only reference those mentioned in the wiki context

Remember: You are answering about a fictional roleplay world, not the real world."
"""
    
    # Save instructions
    info_file = output_path / "UPLOAD_INSTRUCTIONS.txt"
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(info_content)
    
    print(info_content)
    print(f"\nInstructions also saved to: {info_file}")

def main():
    """Main function to convert JSON and create upload instructions"""
    
    # Configuration
    JSON_FILE = "league_wiki_content.json"  # Your scraped wiki JSON
    OUTPUT_DIR = "wiki_documents"
    
    print("League NS Wiki → Open WebUI Converter")
    print("=" * 40)
    
    # Check if JSON file exists
    if not os.path.exists(JSON_FILE):
        print(f"Looking for: {JSON_FILE}")
        print("File not found. Please make sure your scraped wiki JSON file is in the current directory.")
        print("If it has a different name, update the JSON_FILE variable in this script.")
        return
    
    # Convert JSON to documents
    output_path = convert_json_to_documents(JSON_FILE, OUTPUT_DIR)
    
    if output_path:
        # Create upload instructions
        create_batch_upload_info(OUTPUT_DIR)
        
        print(f"\n🎉 Ready for Open WebUI!")
        print(f"Next steps:")
        print(f"1. Set up Open WebUI (if not done already)")
        print(f"2. Upload documents from {output_path}")
        print(f"3. Configure system prompt for wiki-only responses")
        print(f"4. Test with queries like 'What was the deadliest war?'")

if __name__ == "__main__":
    main()
