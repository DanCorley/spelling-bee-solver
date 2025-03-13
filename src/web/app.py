#!/usr/bin/env python3
"""
Spelling Bee Solver Web Interface

This web application provides a user interface for the Spelling Bee solver.
Access the application at:
http://localhost:8080 or http://0.0.0.0:8080

URL Parameters:
- mandatory: Single letter that must be used in all words
- allowed: Six letters that can be used in words
- all-words: Set to 'true' to show all possible words (optional)

Example: http://localhost:8080/?mandatory=a&allowed=tyshfl&all-words=true
"""

import os
import uuid
import logging
from datetime import datetime
from flask import Flask, render_template, request, send_from_directory
from flask_cors import CORS
from src.core.solver import solve_spelling_bee

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../logs')
os.makedirs(log_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
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

def process_spelling_bee_request(mandatory, allowed, all_words, request_id, source):
    """Process the spelling bee request and return results."""
    error = None
    valid_words = []
    pangrams = []
    
    # Create extra log context
    extra = {'request_id': request_id}
    
    # Log the request
    logger.info(
        "%s request - IP: %s, Mandatory: %s, Allowed: %s, Show All Words: %s",
        source,
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
