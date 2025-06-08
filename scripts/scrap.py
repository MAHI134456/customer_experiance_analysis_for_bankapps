import pandas as pd
from google_play_scraper import app, Sort, reviews
import os
import sys
import traceback

# Define the bank apps to scrape
app_ids = [
    {"id": "com.combanketh.mobilebanking", "name": "Commercial Bank of Ethiopia"},
    {"id": "com.boa.boaMobileBanking", "name": "BoA Mobile Banking"},
    {"id": "com.dashen.dashensuperapp", "name": "Dashen Bank Super App"}
]

# Initialize an empty list to store all reviews
all_reviews = []

# Try scraping with English reviews and different country settings
settings = [
    {"lang": "en", "country": "et", "desc": "English, Ethiopia"},
    {"lang": "en", "country": None, "desc": "English, no country filter"}
]

for app_info in app_ids:
    app_id = app_info["id"]
    app_name = app_info["name"]
    
    for setting in settings:
        lang = setting["lang"]
        country = setting["country"]
        desc = setting["desc"]
        print(f"\nScraping 600 English reviews for {app_name} ({app_id}), {desc}...")
        
        try:
            # Verify app exists
            app_details = app(app_id, lang=lang, country=country or 'us')
            if not app_details:
                print(f"Error: No details found for {app_name}. Check appId.")
                continue
            print(f"App details: {app_details['title']} (Reviews: {app_details.get('reviews', 0)})")
            
            # Fetch up to 600 reviews
            result, _ = reviews(
                app_id,
                count=600,
                lang=lang,
                country=country,
                sort=Sort.NEWEST
            )
            
            if not result:
                print(f"No English reviews returned for {app_name} ({desc}).")
                continue
            
            # Process reviews
            for review in result:
                all_reviews.append({
                    'review': str(review.get('content', '')),
                    'rating': int(review.get('score', 0)),
                    'date': review.get('at', None),
                    'bank': app_name,
                    'source': 'Google Play'
                })
            
            print(f"Collected {len(result)} English reviews for {app_name} ({desc}).")
            if len(result) < 600:
                print(f"Warning: Only {len(result)} English reviews available.")
            break  # Exit settings loop if reviews are found
            
        except Exception as e:
            print(f"Error scraping {app_name} ({desc}): {str(e)}")
            print("Detailed traceback:")
            traceback.print_exc(file=sys.stdout)
            continue

# Create DataFrame
df = pd.DataFrame(all_reviews, columns=['review', 'rating', 'date', 'bank', 'source'])

# Remove duplicates
df = df.drop_duplicates(subset=['review', 'rating', 'date', 'bank'], keep='first')

# Ensure data/raw directory exists
os.makedirs('data/raw', exist_ok=True)

# Save to CSV
output_file = 'data/raw/bank_app_reviews.csv'
df.to_csv(output_file, index=False, encoding='utf-8')

# Print summary
print("\nSummary of collected reviews:")
for app_info in app_ids:
    app_name = app_info["name"]
    count = len(df[df['bank'] == app_name])
    print(f"{app_name}: {count} reviews")
print(f"Total: {len(df)} reviews saved to {output_file}.")