#!/usr/bin/env python3
"""
Simple Flask API server for the news scraper dashboard.
"""
import os
import sys
import json
import subprocess
import pandas as pd
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import threading
import time

# Add current directory to path for imports
sys.path.append('.')

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the dashboard

# Global state
scraping_status = {"state": "idle", "progress": 0, "message": ""}
scraping_logs = []

def run_scraper_async(urls, output_dir="./output"):
    """Run the scraper in a separate thread."""
    global scraping_status, scraping_logs
    
    scraping_status = {"state": "running", "progress": 0, "message": "Starting scraper..."}
    scraping_logs = ["Starting scraper..."]
    
    try:
        # Build command
        cmd = [sys.executable, "scripts/run_scraper.py", "--urls", urls, "--output-dir", output_dir]
        
        # Run scraper
        scraping_status["message"] = "Running scraper..."
        scraping_logs.append("Running scraper...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            scraping_status = {"state": "done", "progress": 100, "message": "Scraping completed successfully"}
            scraping_logs.append("Scraping completed successfully")
        else:
            scraping_status = {"state": "error", "progress": 0, "message": f"Scraping failed: {result.stderr}"}
            scraping_logs.append(f"Error: {result.stderr}")
            
    except Exception as e:
        scraping_status = {"state": "error", "progress": 0, "message": f"Error: {str(e)}"}
        scraping_logs.append(f"Error: {str(e)}")

@app.route('/run_scraper', methods=['POST'])
def run_scraper():
    """Start a scraping run."""
    global scraping_status
    
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
    thread = threading.Thread(target=run_scraper_async, args=(urls_str,))
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "Scraping started", "status": "running"})

@app.route('/results', methods=['GET'])
def get_results():
    """Get scraping results as JSON."""
    csv_path = "./output/enriched_articles.csv"
    
    if not os.path.exists(csv_path):
        return jsonify([])
    
    try:
        # Read CSV and convert to JSON
        df = pd.read_csv(csv_path)
        return jsonify(df.to_dict('records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/csv', methods=['GET'])
def download_csv():
    """Download CSV file."""
    csv_path = "./output/enriched_articles.csv"
    
    if not os.path.exists(csv_path):
        return jsonify({"error": "CSV file not found"}), 404
    
    return send_file(csv_path, as_attachment=True, download_name="enriched_articles.csv")

@app.route('/download/json', methods=['GET'])
def download_json():
    """Download JSON file."""
    csv_path = "./output/enriched_articles.csv"
    
    if not os.path.exists(csv_path):
        return jsonify({"error": "CSV file not found"}), 404
    
    try:
        df = pd.read_csv(csv_path)
        json_data = df.to_dict('records')
        
        # Create temporary JSON file
        json_path = "./output/enriched_articles.json"
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        return send_file(json_path, as_attachment=True, download_name="enriched_articles.json")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get scraping status."""
    return jsonify(scraping_status)

@app.route('/logs', methods=['GET'])
def get_logs():
    """Get scraping logs."""
    return '\n'.join(scraping_logs)

@app.route('/delete_results', methods=['POST'])
def delete_results():
    """Delete all scraping results."""
    try:
        # Delete the CSV file
        csv_path = "./output/enriched_articles.csv"
        if os.path.exists(csv_path):
            os.remove(csv_path)
            return jsonify({"message": "Results deleted successfully"})
        else:
            return jsonify({"message": "No results to delete"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "message": "API server is running"})

@app.route('/dashboard/')
def dashboard():
    """Serve the dashboard HTML."""
    return send_from_directory('dashboard', 'index.html')

@app.route('/dashboard/<path:filename>')
def dashboard_files(filename):
    """Serve dashboard static files (CSS, JS)."""
    return send_from_directory('dashboard', filename)

if __name__ == '__main__':
    print("Starting News Scraper API Server...")
    print("Dashboard will be available at: http://localhost:8080/dashboard/")
    print("API endpoints:")
    print("  POST /run_scraper - Start scraping")
    print("  GET  /results - Get results as JSON")
    print("  GET  /download/csv - Download CSV")
    print("  GET  /download/json - Download JSON")
    print("  GET  /status - Get scraping status")
    print("  GET  /logs - Get scraping logs")
    print("  POST /delete_results - Delete all results")
    
    app.run(host='0.0.0.0', port=8080, debug=True)
