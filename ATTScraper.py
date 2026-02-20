import requests
from bs4 import BeautifulSoup
import time
import os
from urllib.parse import urljoin, urlparse
import re

def scrape_transcript_links(main_url):
    """
    Scrape all transcript links from the main category page, organized by season
    """
    print(f"Fetching main page: {main_url}")
    response = requests.get(main_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all season headings (h2 tags with season information)
    seasons = {}
    current_season = None
    
    # Find all h2 headings (they contain the season names)
    for heading in soup.find_all('h2'):
        heading_text = heading.get_text().strip()
        if 'Season' in heading_text or 'Pilot' in heading_text:
            current_season = heading_text
            seasons[current_season] = []
            
            # Find the table following this heading
            next_element = heading.find_next('table')
            if next_element:
                # Find all links in the table that end with '/Transcript'
                for link in next_element.find_all('a', href=True):
                    href = link['href']
                    if href.endswith('/Transcript'):
                        full_url = urljoin(main_url, href)
                        episode_name = link.get_text().strip()
                        seasons[current_season].append({
                            'episode': episode_name,
                            'url': full_url
                        })
    
    return seasons

def download_transcript(url, output_dir, episode_name):
    """
    Download and save a single transcript page
    """
    try:
        print(f"  Downloading: {episode_name}")
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the main content of the transcript
        # On Fandom wiki, transcripts are usually in the mw-parser-output div
        content_div = soup.find('div', {'class': 'mw-parser-output'})
        
        if content_div:
            # Clean up the filename (remove invalid characters)
            safe_filename = re.sub(r'[^\w\s-]', '', episode_name).strip().replace(' ', '_')
            filename = f"{safe_filename}.txt"
            filepath = os.path.join(output_dir, filename)
            
            # Extract text content
            text_content = content_div.get_text(separator='\n', strip=True)
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Episode: {episode_name}\n")
                f.write(f"Source: {url}\n")
                f.write("="*50 + "\n\n")
                f.write(text_content)
            
            return True
        else:
            print(f"  Warning: Could not find content for {episode_name}")
            return False
            
    except Exception as e:
        print(f"  Error downloading {episode_name}: {str(e)}")
        return False

def main():
    # Configuration
    main_url = "https://adventuretime.fandom.com/wiki/Category_talk:Transcripts"
    base_output_dir = "adventure_time_transcripts"
    
    # Create base output directory
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)
    
    # Step 1: Get all transcript links
    print("Step 1: Scraping transcript links...")
    seasons = scrape_transcript_links(main_url)
    
    # Print summary of found transcripts
    total_transcripts = 0
    for season, episodes in seasons.items():
        print(f"{season}: {len(episodes)} transcripts")
        total_transcripts += len(episodes)
    print(f"Total transcripts found: {total_transcripts}\n")
    
    # Step 2: Download each transcript
    print("Step 2: Downloading transcripts...")
    
    for season, episodes in seasons.items():
        # Create season directory
        season_dir = os.path.join(base_output_dir, season.replace(' ', '_').replace('(', '').replace(')', ''))
        if not os.path.exists(season_dir):
            os.makedirs(season_dir)
        
        print(f"\nDownloading {season} ({len(episodes)} episodes)...")
        
        for episode in episodes:
            success = download_transcript(
                episode['url'], 
                season_dir, 
                episode['episode']
            )
            
            # Be respectful to the server - add a small delay
            time.sleep(1)
    
    print(f"\n✅ Download complete! Transcripts saved in '{base_output_dir}' directory")

def download_all_transcripts_advanced():
    """
    Advanced version with more features:
    - Resume capability
    - Error logging
    - JSON metadata export
    """
    import json
    from datetime import datetime
    
    main_url = "https://adventuretime.fandom.com/wiki/Category_talk:Transcripts"
    base_output_dir = "adventure_time_transcripts_advanced"
    metadata_file = os.path.join(base_output_dir, "metadata.json")
    
    # Create base output directory
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)
    
    # Load existing metadata if available (for resume capability)
    existing_metadata = {}
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r', encoding='utf-8') as f:
            existing_metadata = json.load(f)
    
    # Scrape links
    print("Scraping transcript links...")
    seasons = scrape_transcript_links(main_url)
    
    # Prepare metadata structure
    metadata = {
        "last_updated": datetime.now().isoformat(),
        "total_seasons": len(seasons),
        "seasons": {}
    }
    
    # Download transcripts
    for season, episodes in seasons.items():
        season_dir = os.path.join(base_output_dir, season.replace(' ', '_').replace('(', '').replace(')', ''))
        if not os.path.exists(season_dir):
            os.makedirs(season_dir)
        
        metadata["seasons"][season] = {
            "total_episodes": len(episodes),
            "episodes": []
        }
        
        print(f"\nProcessing {season}...")
        
        for episode in episodes:
            # Check if already downloaded (resume capability)
            safe_filename = re.sub(r'[^\w\s-]', '', episode['episode']).strip().replace(' ', '_')
            filepath = os.path.join(season_dir, f"{safe_filename}.txt")
            
            episode_metadata = {
                "episode": episode['episode'],
                "url": episode['url'],
                "downloaded": False,
                "filepath": None
            }
            
            if os.path.exists(filepath):
                print(f"  ✓ Already exists: {episode['episode']}")
                episode_metadata["downloaded"] = True
                episode_metadata["filepath"] = filepath
            else:
                success = download_transcript(episode['url'], season_dir, episode['episode'])
                episode_metadata["downloaded"] = success
                if success:
                    episode_metadata["filepath"] = filepath
                time.sleep(1)  # Be respectful
            
            metadata["seasons"][season]["episodes"].append(episode_metadata)
    
    # Save metadata
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*50)
    print("DOWNLOAD SUMMARY")
    print("="*50)
    
    total_downloaded = 0
    for season, data in metadata["seasons"].items():
        season_downloaded = sum(1 for ep in data["episodes"] if ep["downloaded"])
        total_downloaded += season_downloaded
        print(f"{season}: {season_downloaded}/{data['total_episodes']} downloaded")
    
    print(f"\nTotal: {total_downloaded}/{sum(len(episodes) for episodes in seasons.values())} transcripts downloaded")
    print(f"Metadata saved to: {metadata_file}")

if __name__ == "__main__":
    # Choose which version to run
    print("Adventure Time Transcript Downloader")
    print("="*50)
    print("1. Basic version")
    print("2. Advanced version (with resume capability and metadata)")
    
    choice = input("\nSelect version (1 or 2): ").strip()
    
    if choice == "2":
        download_all_transcripts_advanced()
    else:
        main()