import json
from english_words import get_english_words_set
from collections import defaultdict
from pathlib import Path

def load_bee_words(jsonl_file):
    """Load words from the spelling bee JSONL file."""
    bee_words = {}
    with open(jsonl_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            bee_words[data['word']] = {
                'bee_count': data['count'],
                'letter': data['letter']
            }
    return bee_words

def compare_word_sources():
    # Load spelling bee words
    bee_words = load_bee_words('data/spelling_bee_words.jsonl')
    
    # Get english words in lowercase for comparison
    english_words = get_english_words_set(['web2'], lower=True)
    
    # Create output file
    output_file = 'data/word_comparison.jsonl'
    stats = defaultdict(int)
    
    print("Comparing words from both sources...")
    
    with open(output_file, 'w') as f:
        # Process all unique words from both sources
        all_words = set(bee_words.keys()) | english_words
        
        for word in sorted(all_words):
            # Create word data
            word_data = {
                'word': word,
                'in_bee': word in bee_words,
                'in_english_words': word in english_words,
                'bee_count': bee_words[word]['bee_count'] if word in bee_words else 0,
                'letter': bee_words[word]['letter'] if word in bee_words else word[0]
            }
            
            # Update stats
            source_key = (
                'both' if word_data['in_bee'] and word_data['in_english_words']
                else 'bee_only' if word_data['in_bee']
                else 'english_only'
            )
            stats[source_key] += 1
            stats[f'total_{word_data["letter"]}'] += 1
            
            # Write to output file
            json.dump(word_data, f)
            f.write('\n')
    
    # Print summary
    print("\nComparison complete!")
    print(f"Results saved to {output_file}")
    print("\nStatistics:")
    print(f"Words in both sources: {stats['both']}")
    print(f"Words only in Spelling Bee: {stats['bee_only']}")
    print(f"Words only in english_words: {stats['english_only']}")
    print(f"Total unique words: {sum(stats[k] for k in ['both', 'bee_only', 'english_only'])}")
    
    print("\nWords per letter:")
    for letter in sorted(l for l in stats.keys() if l.startswith('total_')):
        print(f"  {letter[-1]}: {stats[letter]}")

if __name__ == "__main__":
    compare_word_sources() 