import pandas as pd
import numpy as np
from google_play_scraper import app, Sort, reviews
import os
from datetime import datetime
import uuid

# Define the bank apps to scrape (appId and display name)
app_ids = [
    {"id": "com.combanketh.mobilebanking", "name": "Commercial Bank of Ethiopia"},
    {"id": "com.boa.boaMobileBanking", "name": "BoA Mobile Banking"},
    {"id": "com.dashen.dashensuperapp", "name": "Dashen Bank Super App"},
]
 
# Initialize an empty list to store all reviews
all_reviews = []

# Scrape 600 reviews for each app
for app_info in app_ids:
    app_id = app_info["id"]
    app_name = app_info["name"]
    print(f"Scraping 600 reviews for {app_name} ({app_id})...")
    
    try:
        # Fetch app details to verify the app exists
        app_details = app(app_id, lang='en', country='us')
        if not app_details:
            print(f"No details found for {app_name}. Skipping...")
            continue
        
        # Fetch up to 600 reviews for the app
        result, _ = reviews(
            app_id,
            count=600,              # Limit to 600 reviews
            sleep_milliseconds=100, # Add delay to avoid rate limiting
            lang='en',              # English reviews
            sort=Sort.NEWEST        # Sort by newest reviews
        )
        
        # Process each review
        for review in result:
            all_reviews.append({
                'review': str(review.get('content', '')),  # Ensure review is string
                'rating': int(review.get('score', 0)),     # Ensure rating is int, default 0 if missing
                'date': review.get('at', None),            # Datetime object, None if missing
                'bank': app_name,                          # App name
                'source': 'Google Play'                    # Static source
            })
        
        print(f"Collected {len(result)} reviews for {app_name}.")
        if len(result) < 600:
            print(f"Warning: Only {len(result)} reviews available for {app_name} (fewer than 600).")
        
    except Exception as e:
        print(f"Error scraping {app_name}: {str(e)}")
        continue

# Creating a DataFrame with explicit column order
df = pd.DataFrame(all_reviews, columns=['review', 'rating', 'date', 'bank', 'source'])

# Ensure the data/raw directory exists
os.makedirs('data/raw', exist_ok=True)

# Define the output CSV file path
output_file = 'data/raw/bank_app_reviews.csv'

# Save the DataFrame to CSV
df.to_csv(output_file, index=False, encoding='utf-8')

# Print summary
print("\nSummary of collected reviews:")
for app_info in app_ids:
    app_name = app_info["name"]
    count = len(df[df['bank'] == app_name])
    print(f"{app_name}: {count} reviews")
print(f"Total: {len(df)} reviews saved to {output_file}.")