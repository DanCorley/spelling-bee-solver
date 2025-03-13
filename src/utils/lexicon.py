import requests
from bs4 import BeautifulSoup
import string
import json
from time import sleep
from datetime import datetime

def scrape_words_for_letter(letter):
    url = f"https://sbhinter.com/spelling-bee-lexicon/{letter}"
    print(f"\nScraping words for letter {letter.upper()}...")
    
    # Add a small delay to be respectful to the server
    sleep(.5)
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all divs with class containing 'stats-box'
        stats_boxes = soup.find_all('div', class_=lambda x: x and 'stats-box' in x)
        
        if stats_boxes:
            words_with_counts = []
            for stats_box in stats_boxes:
                # Find all word cells and their corresponding count cells
                word_cell = stats_box.find('div', class_='bee-cell-first')
                count_cell = stats_box.find('div', class_='bee-count-fixed')
                word = word_cell.text.strip()
                count = int(count_cell.text.strip())

                words_with_counts.append({
                    "word": word,
                    "count": count,
                    "letter": letter
                })
            
            return words_with_counts
        else:
            print(f"No stats box found for letter {letter}")
            return []
            
    except requests.RequestException as e:
        print(f"Error scraping letter {letter}: {e}")
        return []

def main():
    start_time = datetime.now()
    total_words = 0
    output_file = 'data/spelling_bee_words.jsonl'
    
    # Open the output file and write each word as we get it
    with open(output_file, 'w') as f:
        # Scrape words for each letter of the alphabet
        for letter in string.ascii_lowercase:
            words = scrape_words_for_letter(letter)
            letter_count = len(words)
            total_words += letter_count
            print(f"Found {letter_count} words for letter {letter}")
            
            # Write each word to the file as we get it
            for word_data in words:
                json.dump(word_data, f)
                f.write('\n')
    
    # Print summary
    duration = datetime.now() - start_time
    print(f"\nScraping complete!")
    print(f"Total words collected: {total_words}")
    print(f"Time taken: {duration}")
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main() 