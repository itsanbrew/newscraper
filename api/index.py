#!/usr/bin/env python3
"""
Vercel serverless function for the news scraper API.
"""
import os
import sys
import json
import subprocess
import pandas as pd
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import threading
import time
import tempfile
import shutil

# Add current directory to path for imports
sys.path.append('.')

app = Flask(__name__)
CORS(app)

# Global state for scraping process
scraping_status = {"state": "idle", "progress": 0, "message": "Ready"}
scraping_logs = []
scraping_thread = None

# Use temporary directory for output in Vercel
OUTPUT_DIR = "/tmp/news_scraper_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_CSV_PATH = os.path.join(OUTPUT_DIR, "enriched_articles.csv")

def run_scraper_in_background(urls_str: str):
    """Runs the scraper script in a separate thread."""
    global scraping_status, scraping_logs
    
    scraping_status = {"state": "running", "progress": 0, "message": "Scraping started..."}
    scraping_logs.clear()
    scraping_logs.append("Scraping started...")
    
    try:
        # Construct the command to run the scraper script
        script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'run_scraper.py')
        cmd = [sys.executable, script_path, "--urls", urls_str, "--output-dir", OUTPUT_DIR]
        
        # Run the scraper as a subprocess
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            scraping_status = {"state": "done", "progress": 100, "message": "Scraping completed successfully"}
            scraping_logs.append("Scraping completed successfully")
        else:
            scraping_status = {"state": "error", "progress": 0, "message": f"Scraping failed: {result.stderr}"}
            scraping_logs.append(f"Error: {result.stderr}")
            
    except Exception as e:
        scraping_status = {"state": "error", "progress": 0, "message": f"Error: {str(e)}"}
        scraping_logs.append(f"Error: {str(e)}")

@app.route('/api/run_scraper', methods=['POST'])
def run_scraper():
    """Start a scraping run."""
    global scraping_status, scraping_thread
    
    if scraping_status["state"] == "running":
        return jsonify({"error": "Scraper is already running"}), 400
    
    data = request.get_json()
    print(f"Received data: {data}")  # Debug logging
    
    # Handle both 'urls' and 'keyword' fields
    urls = data.get('urls', [])
    keyword = data.get('keyword', '')
    
    # If keyword is provided, treat it as a single URL
    if keyword and not urls:
        urls = [keyword]
    
    if not urls:
        return jsonify({"error": "No URLs provided"}), 400
    
    # Convert list to comma-separated string
    urls_str = ','.join(urls) if isinstance(urls, list) else urls
    
    # Start scraping in background thread
    scraping_thread = threading.Thread(target=run_scraper_in_background, args=(urls_str,))
    scraping_thread.start()
    
    return jsonify({"message": "Scraping started", "status": scraping_status}), 200

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current scraping status."""
    return jsonify(scraping_status)

@app.route('/api/results', methods=['GET'])
def get_results():
    """Get scraping results from the CSV file."""
    if os.path.exists(OUTPUT_CSV_PATH):
        try:
            df = pd.read_csv(OUTPUT_CSV_PATH)
            return jsonify(df.to_dict(orient='records'))
        except Exception as e:
            return jsonify({"error": f"Failed to read CSV: {str(e)}"}), 500
    return jsonify([])

@app.route('/api/download/csv', methods=['GET'])
def download_csv():
    """Download results as CSV."""
    if os.path.exists(OUTPUT_CSV_PATH):
        return send_file(OUTPUT_CSV_PATH, as_attachment=True, download_name='enriched_articles.csv', mimetype='text/csv')
    return jsonify({"error": "CSV file not found"}), 404

@app.route('/api/download/json', methods=['GET'])
def download_json():
    """Download results as JSON."""
    if os.path.exists(OUTPUT_CSV_PATH):
        try:
            df = pd.read_csv(OUTPUT_CSV_PATH)
            return send_file(
                pd.io.common.StringIO(df.to_json(orient='records', indent=2)),
                as_attachment=True,
                download_name='enriched_articles.json',
                mimetype='application/json'
            )
        except Exception as e:
            return jsonify({"error": f"Failed to convert to JSON: {str(e)}"}), 500
    return jsonify({"error": "CSV file not found"}), 404

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get scraping logs."""
    return '\n'.join(scraping_logs)

@app.route('/api/delete_results', methods=['POST'])
def delete_results():
    """Delete all scraping results."""
    try:
        # Delete the CSV file
        if os.path.exists(OUTPUT_CSV_PATH):
            os.remove(OUTPUT_CSV_PATH)
            return jsonify({"message": "Results deleted successfully"})
        else:
            return jsonify({"message": "No results to delete"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "message": "API server is running"})

# For Vercel, we need to export the app
handler = app
