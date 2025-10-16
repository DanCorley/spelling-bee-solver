#!/usr/bin/env python3
"""
Spelling Bee Solver

This script helps solve the Spelling Bee game by finding words that:
- Must contain a specific mandatory letter
- Can only use letters from a set of 7 letters (the mandatory letter + 6 others)
- Are at least 4 letters long (standard Spelling Bee rule)
- Prioritizes words that have appeared in past Spelling Bee games
- By default, only shows words that have appeared in past games
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set

def load_word_list() -> Dict[str, dict]:
    """Load words from the word comparison JSONL file"""
    words_data = {}
    comparison_file = Path('data/word_comparison.jsonl')
    
    if not comparison_file.exists():
        raise FileNotFoundError("word_comparison.jsonl not found. Please run word_comparison.py first.")
    
    with open(comparison_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            # Only include words that have appeared in Spelling Bee or are in the english words set
            if data['in_bee'] or data['in_english_words']:
                words_data[data['word']] = {
                    'bee_count': data['bee_count'],
                    'in_bee': data['in_bee'],
                    'in_english_words': data['in_english_words']
                }
    
    return words_data

def is_valid_spelling_bee_word(word: str, mandatory: str, allowed: str, min_length: int = 4) -> bool:
    """Check if a word is valid for Spelling Bee rules"""
    # Check minimum word length
    if len(word) < min_length:
        return False
        
    # Check if mandatory letter is in the word
    if mandatory not in word:
        return False
    
    # Check if word only uses allowed letters
    all_allowed = set(mandatory + allowed)
    return all(letter in all_allowed for letter in word)

def solve_spelling_bee(mandatory: str, allowed: str, min_length: int = 4) -> Tuple[List[dict], List[dict]]:
    """Find all valid Spelling Bee words"""
    words_data = load_word_list()
    all_letters = set(mandatory + allowed)
    
    valid_words = []
    for word, data in words_data.items():
        if is_valid_spelling_bee_word(word, mandatory, allowed, min_length):

            is_pangram = all(letter in word for letter in all_letters)

            score = 0
            if len(word) == 4:
                score = 1
            elif len(word) > 4:
                score = len(word)
                if is_pangram:
                    score += 7
            

            valid_words.append({
                'word': word,
                'length': len(word),
                'points': score,
                'bee_count': data['bee_count'],
                'in_bee': data['in_bee'],
                'status': "✓" if data['in_bee'] else "×",
                'in_english_words': data['in_english_words'],
                'is_pangram': is_pangram
            })
    
    # Sort alphabetically
    valid_words.sort(key=lambda x: x['word'])
    
    # Find pangrams (words that use all 7 letters)
    pangrams = [word_data for word_data in valid_words if word_data['is_pangram']]
    
    return valid_words, pangrams

def main():
    parser = argparse.ArgumentParser(description='Spelling Bee Solver')
    parser.add_argument('-m', '--mandatory', required=True, help='The mandatory letter that must appear in all words')
    parser.add_argument('-a', '--allowed', required=True, help='The 6 other allowed letters')
    parser.add_argument('-l', '--min-length', type=int, default=4, help='Minimum word length (default: 4)')
    parser.add_argument('--all-words', action='store_true', help='Show all possible words, including those that have never appeared in Spelling Bee')

    args = parser.parse_args()
    
    mandatory = args.mandatory.strip().lower()
    allowed = args.allowed.strip().lower()
    
    if len(mandatory) != 1 or not mandatory.isalpha():
        print("Error: Mandatory letter must be a single alphabetic character.")
        return
    
    if len(allowed) != 6 or not allowed.isalpha():
        print("Error: You must specify exactly 6 allowed letters.")
        return
    
    try:
        valid_words, pangrams = solve_spelling_bee(mandatory, allowed, args.min_length)
        
        # By default, only show words that have appeared in Spelling Bee
        if not args.all_words:
            valid_words = [w for w in valid_words if w['in_bee']]
            pangrams = [p for p in pangrams if p['in_bee']]
        
        print(f"\nFound {len(valid_words)} valid words")
        print(f"Found {len(pangrams)} pangrams (words using all 7 letters)")
        
        template = "{status} {word} ({bee_count} times) - {points} points"

        if pangrams:
            print("\nPangrams:")
            for word_data in pangrams:
                print(template.format(**word_data))
        
        print("\nAll valid words (sorted alphabetically):")
        for word_data in valid_words:
            print(template.format(**word_data))
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run word_comparison.py first to generate the word list.")

if __name__ == "__main__":
    main()
