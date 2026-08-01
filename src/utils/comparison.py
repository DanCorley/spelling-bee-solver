import duckdb
from english_words import get_english_words_set
from collections import defaultdict

def load_bee_words(jsonl_file):
    import json
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
    bee_words = load_bee_words('data/spelling_bee_words.jsonl')
    english_words = get_english_words_set(['web2'], lower=True)

    stats = defaultdict(int)
    rows = []

    print("Comparing words from both sources...")

    for word in sorted(set(bee_words.keys()) | english_words):
        in_bee = word in bee_words
        in_english = word in english_words
        bee_count = bee_words[word]['bee_count'] if in_bee else 0
        letter = bee_words[word]['letter'] if in_bee else word[0]

        rows.append((word, in_bee, in_english, bee_count, letter))

        source_key = 'both' if in_bee and in_english else 'bee_only' if in_bee else 'english_only'
        stats[source_key] += 1
        stats[f'total_{letter}'] += 1

    output_file = 'data/word_comparison.parquet'
    conn = duckdb.connect()
    conn.execute("""
        CREATE TABLE words (
            word VARCHAR,
            in_bee BOOLEAN,
            in_english_words BOOLEAN,
            bee_count INTEGER,
            letter VARCHAR
        )
    """)
    conn.executemany("INSERT INTO words VALUES (?, ?, ?, ?, ?)", rows)
    conn.execute(f"COPY words TO '{output_file}' (FORMAT PARQUET, COMPRESSION ZSTD)")

    print(f"\nComparison complete! Results saved to {output_file}")
    print(f"\nWords in both sources: {stats['both']}")
    print(f"Words only in Spelling Bee: {stats['bee_only']}")
    print(f"Words only in english_words: {stats['english_only']}")
    print(f"Total unique words: {sum(stats[k] for k in ['both', 'bee_only', 'english_only'])}")

if __name__ == "__main__":
    compare_word_sources()
