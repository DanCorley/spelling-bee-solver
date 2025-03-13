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
from flask import Flask, render_template, request
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

@app.route("/", methods=["GET", "POST"])
def index():
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
