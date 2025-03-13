# Spelling Bee Solver Documentation

## Components

### Web Interface (`src/web/`)

#### Application (`app.py`)
Flask-based web application that provides a user interface for the Spelling Bee solver.

### Core Module (`src/core/`)

#### Solver (`solver.py`)
The main puzzle solver that implements the logic for finding valid words in the Spelling Bee puzzle.

### Utils Module (`src/utils/`)

#### Lexicon (`lexicon.py`)
Handles word list scraping from the sbhinter NYT approved word list lexicon.

#### Word Comparison (`comparison.py`)
Utility functions for comparing and analyzing words from the sbhinter lexicon and the english_words python package, including similarity metrics and pattern matching.

## Data Structure

### Processed Data (`data/`)
- `spelling_bee_words.jsonl`: Processed word list specific to sbhinter approved Spelling Bee list
- `word_comparison.jsonl`: ALL word comparison data including english_words and sbhinter.


## Docker Deployment

To deploy the application using Docker, follow these steps:

1. Build the Docker image:
   ```bash
   docker-compose build
   ```
2. Run the Docker container:
   ```bash
   docker-compose up
   ```

This will build and run the application. The container will be accessible at the specified port.
