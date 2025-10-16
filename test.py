#!/usr/bin/env python3
"""
Enhanced test script using the new scraper pipeline.
"""
import os
import sys
import subprocess
from pathlib import Path

def run_enhanced_scraper():
    """Run the enhanced scraper and display results."""
    
    # Get the script directory
    script_dir = Path(__file__).parent
    scraper_script = script_dir / "scripts" / "run_scraper.py"
    
    # Test URL
    test_url = "https://www.bbc.com/news/articles/c4gkm0243wzo"
    
    print("=== ENHANCED NEWS SCRAPER TEST ===")
    print(f"Testing URL: {test_url}")
    print("Running enhanced scraper with email enrichment...")
    print("-" * 50)
    
    try:
        # Run the enhanced scraper
        result = subprocess.run([
            sys.executable, str(scraper_script),
            "--urls", test_url,
            "--output-dir", "./output"
        ], capture_output=True, text=True, cwd=script_dir)
        
        # Print the output
        print("SCRAPER OUTPUT:")
        print(result.stdout)
        
        if result.stderr:
            print("ERRORS:")
            print(result.stderr)
        
        # Check if CSV was created
        output_dir = script_dir / "output"
        enriched_csv = output_dir / "enriched_articles.csv"
        
        if enriched_csv.exists():
            print("\n=== ENRICHED CSV CREATED ===")
            print(f"File: {enriched_csv}")
            print("(Includes contact data columns: full_name, email, confidence)")
            print("\nCSV Content:")
            with open(enriched_csv, 'r') as f:
                print(f.read())
        else:
            print("\n❌ No CSV files were created")
            
    except Exception as e:
        print(f"Error running scraper: {e}")

if __name__ == "__main__":
    run_enhanced_scraper()