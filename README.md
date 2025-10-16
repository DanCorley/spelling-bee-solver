# Spelling Bee Solver

A Python-based tool for solving the New York Times Spelling Bee puzzle, available in both a cli tool and a web interface.

## Project Structure

```
spelling_bee/
├── src/                   # Source code
│   ├── core/              # Core functionality
│   │   ├── solver.py      # Main puzzle solver
│   ├── utils/             # Utility functions
│   │   ├── lexicon.py     # Lexicon scraping
│   │   └── comparison.py  # Word comparison utilities
│   └── web/               # Web application
│       └── app.py         # Web interface
├── data/                  # Data files
├── docs/                  # Documentation
├── Dockerfile          # Docker configuration
└── docker-compose.yaml # Docker Compose configuration
```

### Docker Deployment
Build and run using Docker:
```bash
docker-compose up --build
```

## Setup web interface from source

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate  # On Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the web application:
   ```bash
   python src/web/app.py
   ```

## CLI tool

```bash
python src/core/solver.py -m <mandatory_letter> -a <allowed_letters>
```

