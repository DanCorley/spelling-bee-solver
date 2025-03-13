#!/usr/bin/env python3
"""
Spelling Bee Solver Web Interface

This web application provides a user interface for the Spelling Bee solver.
Access the application at:
http://localhost:8080 or http://0.0.0.0:8080
"""

import os
import uuid
import logging
from datetime import datetime
from flask import Flask, render_template, request, send_from_directory, jsonify
from flask_cors import CORS
from src.core.solver import solve_spelling_bee, load_word_list

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../logs')
os.makedirs(log_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(request_id)s] - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'spelling_bee.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add request_id to log records
class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(record, 'request_id', 'no_request_id')
        return True

logger.addFilter(RequestIdFilter())

app = Flask(__name__)
# Enable CORS for all routes
CORS(app)

# Add security headers but allow all access
@app.after_request
def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'sb-favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

# Add cache dictionary at module level
word_cache = {}

def process_spelling_bee_request(mandatory, allowed, all_words, request_id, source):
    """Process the spelling bee request and return results."""
    error = None
    valid_words = []
    pangrams = []
    mandatory = ""
    allowed = ""
    all_words = False
    
    if request.method == "POST":
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        
        mandatory = request.form.get("mandatory", "").strip().lower()
        allowed = request.form.get("allowed", "").strip().lower()
        all_words = bool(request.form.get("all_words"))
        
        # Create extra log context
        extra = {'request_id': request_id}
        
        # Log the form submission
        logger.info(
            "Form submission - IP: %s, Mandatory: %s, Allowed: %s, Show All Words: %s",
            request.remote_addr,
            mandatory,
            allowed,
            all_words,
            extra=extra
        )
        
        if len(mandatory) != 1 or not mandatory.isalpha():
            error = "Mandatory letter must be a single alphabetic character."
            logger.warning(
                "Invalid submission - IP: %s, Error: %s, Mandatory: %s",
                request.remote_addr,
                error,
                mandatory,
                extra=extra
            )
        elif len(allowed) != 6 or not allowed.isalpha():
            error = "You must specify exactly 6 allowed letters."
            logger.warning(
                "Invalid submission - IP: %s, Error: %s, Allowed: %s",
                request.remote_addr,
                error,
                allowed,
                extra=extra
            )
        else:
            try:
                valid_words, pangrams = solve_spelling_bee(mandatory, allowed)
                if not all_words:
                    valid_words = [w for w in valid_words if w['in_bee']]
                    pangrams = [p for p in pangrams if p['in_bee']]
                logger.info(
                    "Successful search - IP: %s, Words Found: %d, Pangrams Found: %d",
                    request.remote_addr,
                    len(valid_words),
                    len(pangrams),
                    extra=extra
                )
            except FileNotFoundError as e:
                error = str(e)
                logger.error(
                    "File error - IP: %s, Error: %s",
                    request.remote_addr,
                    str(e),
                    extra=extra
                )
    
    return error, valid_words, pangrams

@app.route("/prefilter", methods=["POST"])
def prefilter():
    """Pre-filter words based on mandatory letter."""
    start_time = datetime.now()
    mandatory = request.json.get("mandatory", "").strip().lower()
    request_id = str(uuid.uuid4())
    
    # Log the incoming request
    logger.info(
        "Prefilter request received - IP: %s, Letter: %s",
        request.remote_addr,
        mandatory,
        extra={'request_id': request_id}
    )
    
    if len(mandatory) != 1 or not mandatory.isalpha():
        logger.warning(
            "Invalid prefilter request - IP: %s, Letter: %s",
            request.remote_addr,
            mandatory,
            extra={'request_id': request_id}
        )
        return jsonify({"error": "Mandatory letter must be a single alphabetic character."}), 400
    
    try:
        # Check if we already have the filtered words for this letter
        cache_hit = mandatory in word_cache
        logger.info(
            "Cache status - IP: %s, Letter: %s, Cache Hit: %s",
            request.remote_addr,
            mandatory,
            cache_hit,
            extra={'request_id': request_id}
        )
        
        if not cache_hit:
            # Load all words and filter by mandatory letter
            words_data = load_word_list()
            filtered_words = {
                word: data for word, data in words_data.items()
                if mandatory in word and len(word) >= 4
            }
            word_cache[mandatory] = filtered_words
            
            logger.info(
                "Pre-filtered words - IP: %s, Letter: %s, Words Found: %d",
                request.remote_addr,
                mandatory,
                len(filtered_words),
                extra={'request_id': request_id}
            )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(
            "Prefilter request completed - IP: %s, Letter: %s, Words: %d, Time: %.3fs, Cache Hit: %s",
            request.remote_addr,
            mandatory,
            len(word_cache[mandatory]),
            processing_time,
            cache_hit,
            extra={'request_id': request_id}
        )
        
        return jsonify({
            "success": True, 
            "count": len(word_cache[mandatory]),
            "cache_hit": cache_hit,
            "processing_time": processing_time,
            "is_production": os.environ.get('FLASK_ENV') == 'production'
        }), 200
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(
            "Error in prefilter - IP: %s, Letter: %s, Error: %s, Time: %.3fs",
            request.remote_addr,
            mandatory,
            str(e),
            processing_time,
            request_id,
            extra={'request_id': request_id}
        )
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    valid_words = []
    pangrams = []
    mandatory = ""
    allowed = ""
    all_words = False
    
    # Generate a unique request ID
    request_id = str(uuid.uuid4())
    
    if request.method == "POST":
        # Handle form submission
        mandatory = request.form.get("mandatory", "").strip().lower()
        allowed = request.form.get("allowed", "").strip().lower()
        all_words = bool(request.form.get("all_words"))
        
        # Use cached words if available
        if mandatory in word_cache:
            try:
                # Filter cached words using allowed letters
                filtered_words = []
                all_allowed = set(mandatory + allowed)
                
                for word, data in word_cache[mandatory].items():
                    if all(letter in all_allowed for letter in word):
                        filtered_words.append({
                            'word': word,
                            'length': len(word),
                            'bee_count': data['bee_count'],
                            'in_bee': data['in_bee'],
                            'in_english_words': data['in_english_words']
                        })
                
                # Sort alphabetically
                filtered_words.sort(key=lambda x: x['word'])
                
                # Find pangrams
                pangrams = [
                    word_data for word_data in filtered_words 
                    if all(letter in word_data['word'] for letter in all_allowed)
                ]
                
                if not all_words:
                    filtered_words = [w for w in filtered_words if w['in_bee']]
                    pangrams = [p for p in pangrams if p['in_bee']]
                
                valid_words = filtered_words
                
                logger.info(
                    "Used cached results - IP: %s, Words Found: %d, Pangrams Found: %d",
                    request.remote_addr,
                    len(valid_words),
                    len(pangrams),
                    extra={'request_id': request_id}
                )
            except Exception as e:
                logger.error(
                    "Error using cached results - IP: %s, Error: %s",
                    request.remote_addr,
                    str(e),
                    extra={'request_id': request_id}
                )
                # Fall back to normal processing if cache use fails
                error, valid_words, pangrams = process_spelling_bee_request(
                    mandatory, allowed, all_words, request_id, "Form"
                )
        else:
            error, valid_words, pangrams = process_spelling_bee_request(
                mandatory, allowed, all_words, request_id, "Form"
            )
    elif request.args:
        # Handle URL parameters
        mandatory = request.args.get("mandatory", "").strip().lower()
        allowed = request.args.get("allowed", "").strip().lower()
        all_words = request.args.get("all-words", "").lower() in ('true', '1', 'yes')
        if mandatory or allowed:  # Only process if at least one parameter is provided
            error, valid_words, pangrams = process_spelling_bee_request(
                mandatory, allowed, all_words, request_id, "URL"
            )
    
    return render_template(
        'index.html',
        valid_words=valid_words,
        pangrams=pangrams,
        error=error,
        mandatory=mandatory,
        allowed=allowed,
        all_words=all_words
    )

if __name__ == "__main__":
    # Allow all hosts, disable debug in production
    app.run(host='0.0.0.0', port=8080, debug=False)
