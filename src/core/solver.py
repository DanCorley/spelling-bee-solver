import duckdb
import time
import os
import argparse
from typing import List, Tuple

_conn: duckdb.DuckDBPyConnection | None = None
_last_loaded: float = 0.0
_REFRESH_INTERVAL = int(os.environ.get('DATA_REFRESH_SECONDS', '86400'))


def _data_source() -> str:
    if os.environ.get('FLASK_ENV') == 'production':
        repo = os.environ.get('GITHUB_REPOSITORY', 'DanCorley/spelling-bee-solver')
        return f"https://github.com/{repo}/releases/download/data-latest/word_comparison.parquet"
    local = 'data/word_comparison.parquet'
    if not os.path.exists(local):
        raise FileNotFoundError(
            f"Local Mode Enabled and {local} not found. "
            "Run python src/utils/lexicon.py && python src/utils/comparison.py to generate local data."
        )
    return local


def _init_conn() -> duckdb.DuckDBPyConnection:
    source = _data_source()
    conn = duckdb.connect()
    if os.environ.get('FLASK_ENV') == 'production':
        conn.execute("INSTALL httpfs; LOAD httpfs;")
    conn.execute(f"CREATE TABLE words AS SELECT * FROM read_parquet('{source}')")
    return conn


def _get_conn() -> duckdb.DuckDBPyConnection:
    global _conn, _last_loaded
    if _conn is None or (time.time() - _last_loaded) > _REFRESH_INTERVAL:
        if _conn is not None:
            _conn.close()
        _conn = _init_conn()
        _last_loaded = time.time()
    return _conn


def solve_spelling_bee(mandatory: str, allowed: str, min_length: int = 4) -> Tuple[List[dict], List[dict]]:
    all_letters = set(mandatory + allowed)
    letter_pattern = ''.join(sorted(all_letters))

    rows = _get_conn().execute("""
        SELECT word, bee_count, in_bee, in_english_words
        FROM words
        WHERE length(word) >= ?
          AND contains(word, ?)
          AND NOT regexp_matches(word, ?)
          AND (in_bee OR in_english_words)
    """, [min_length, mandatory, f'[^{letter_pattern}]']).fetchall()

    valid_words = []
    pangrams = []

    for word, bee_count, in_bee, in_english_words in rows:
        is_pangram = all(letter in word for letter in all_letters)
        score = 1 if len(word) == 4 else len(word) + (7 if is_pangram else 0)
        entry = {
            'word': word,
            'length': len(word),
            'points': score,
            'bee_count': bee_count,
            'in_bee': in_bee,
            'status': "✓" if in_bee else "×",
            'in_english_words': in_english_words,
            'is_pangram': is_pangram,
        }
        valid_words.append(entry)
        if is_pangram:
            pangrams.append(entry)

    valid_words.sort(key=lambda x: x['word'])
    pangrams.sort(key=lambda x: x['word'])

    return valid_words, pangrams


def main():
    parser = argparse.ArgumentParser(description='Spelling Bee Solver')
    parser.add_argument('-m', '--mandatory', required=True)
    parser.add_argument('-a', '--allowed', required=True)
    parser.add_argument('-l', '--min-length', type=int, default=4)
    parser.add_argument('--all-words', action='store_true')
    args = parser.parse_args()

    mandatory = args.mandatory.strip().lower()
    allowed = args.allowed.strip().lower()

    if len(mandatory) != 1 or not mandatory.isalpha():
        print("Error: Mandatory letter must be a single alphabetic character.")
        return
    if len(allowed) != 6 or not allowed.isalpha():
        print("Error: You must specify exactly 6 allowed letters.")
        return

    valid_words, pangrams = solve_spelling_bee(mandatory, allowed, args.min_length)

    if not args.all_words:
        valid_words = [w for w in valid_words if w['in_bee']]
        pangrams = [p for p in pangrams if p['in_bee']]

    print(f"\nFound {len(valid_words)} valid words")
    print(f"Found {len(pangrams)} pangrams")

    template = "{status} {word} ({bee_count} times) - {points} points"
    if pangrams:
        print("\nPangrams:")
        for w in pangrams:
            print(template.format(**w))
    print("\nAll valid words (sorted alphabetically):")
    for w in valid_words:
        print(template.format(**w))


if __name__ == "__main__":
    main()
