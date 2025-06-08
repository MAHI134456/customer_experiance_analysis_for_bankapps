import pandas as pd
import os

# Load the raw CSV
input_file = 'data/raw/bank_app_reviews.csv'
# Ensure the input file exists
try:
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} reviews from {input_file}.")
except FileNotFoundError:
    print(f"Error: {input_file} not found. Please ensure the raw data exists.")
    exit(1)

# Initial row count
initial_count = len(df)

# Remove duplicates
df = df.drop_duplicates(subset=['review', 'rating', 'date', 'bank', 'source'], keep='first')
print(f"Removed {initial_count - len(df)} duplicate reviews. {len(df)} reviews remain.")

# Handle missing data
# Review: Replace missing/empty with empty string
df['review'] = df['review'].fillna('').astype(str)

# Rating: Replace missing with 0, ensure integer
df['rating'] = df['rating'].fillna(0).astype(int)

# Source: Replace missing with 'Google Play'
df['source'] = df['source'].fillna('Google Play').astype(str)

# Date and Bank: Drop rows with missing values
df = df.dropna(subset=['date', 'bank'])
print(f"Dropped {initial_count - len(df)} rows with missing date or bank. {len(df)} reviews remain.")

# Normalize dates to YYYY-MM-DD
try:
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
except ValueError as e:
    print(f"Error normalizing dates: {e}. Dropping rows with invalid dates.")
    df = df[df['date'].apply(lambda x: pd.to_datetime(x, errors='coerce').notna())]
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    print(f"Dropped additional rows with invalid dates. {len(df)} reviews remain.")

# Ensure column order
df = df[['review', 'rating', 'date', 'bank', 'source']]

# Ensure the data/processed directory exists
os.makedirs('data/processed', exist_ok=True)

# Save the processed DataFrame to CSV
output_file = 'data/processed/bank_app_reviews_processed.csv'
df.to_csv(output_file, index=False, encoding='utf-8')

# Print summary
print("\nSummary of processed reviews:")
for bank in df['bank'].unique():
    count = len(df[df['bank'] == bank])
    print(f"{bank}: {count} reviews")
print(f"Total: {len(df)} reviews saved to {output_file}.")