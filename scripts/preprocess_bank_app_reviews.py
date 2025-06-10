import pandas as pd
import os
from langdetect import detect, DetectorFactory, LangDetectException
from deep_translator import GoogleTranslator
import time
import re


# Set seed for langdetect to ensure reproducibility
DetectorFactory.seed = 42

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

'''# Downsample CBE and BOA to match Dashen's 449 reviews
# Filter by bank
cbe_reviews = df[df['bank'] == 'Commercial Bank of Ethiopia']
boa_reviews = df[df['bank'] == 'BoA Mobile Banking']
dashen_reviews = df[df['bank'] == 'Dashen Bank Super App']

# Verify counts
print(f"Original counts: CBE={len(cbe_reviews)}, BOA={len(boa_reviews)}, Dashen={len(dashen_reviews)}")

# Randomly downsample CBE and BOA to 449 reviews
if len(cbe_reviews) > 449:
    cbe_reviews = cbe_reviews.sample(n=449, random_state=42)  
if len(boa_reviews) > 449:
    boa_reviews = boa_reviews.sample(n=449, random_state=42)


# Combine the datasets
df = pd.concat([cbe_reviews, boa_reviews, dashen_reviews])



# Verify final counts
print(df.shape)


 

# Define is_english helper
def is_english(text):
    try:
        return detect(text) == 'en'
    except:
        return False  # Return False if language detection fails

# Drop non-English reviews
print(f"Total reviews before language filtering: {len(df)}")
df['is_english'] = df['review'].apply(is_english)
df = df[df['is_english'] == True]
df = df.drop(columns=['is_english'])  # Remove temporary column
'''


# Initialize the translator
translator = GoogleTranslator(source='am', target='en')

# Function to check for Amharic characters (Ethiopic Unicode range: U+1200–U+137F)
def has_amharic(text):
    if pd.isna(text) or not isinstance(text, str) or text.strip() == '':
        return False
    return bool(re.search(r'[\u1200-\u137F]', text))


# Function to detect language
def detect_language(text):
    if pd.isna(text) or not isinstance(text, str) or text.strip() == '':
        return 'unknown'
    try:
        lang = detect(text)
        # Force Amharic detection if Ethiopic characters are present
        if has_amharic(text):
            return 'am'
        return lang
    except LangDetectException:
        return 'am' if has_amharic(text) else 'unknown'


# Function to translate text if it's Amharic
def translate_if_amharic(text):
    if pd.isna(text) or not isinstance(text, str) or text.strip() == '':
        return ''
    lang = detect_language(text)
    print(f"Detected language for '{text[:30]}...': {lang}")
    if lang == 'am':  # Amharic
        for attempt in range(3):  # Retry up to 3 times
            try:
                translated = translator.translate(text)
                if translated:
                    print(f"Translated: {text} -> {translated}")
                    return translated
                return text
            except Exception as e:
                print(f"Attempt {attempt+1} failed for '{text}': {e}")
                time.sleep(1)
        print(f"Failed to translate '{text}' after 3 attempts")
        return text
    return text  # Return original text if not Amharic

# Apply translation to the review column
translated_reviews = []
for i, text in enumerate(df['review']):
    print(f"Processing review {i+1}/{len(df)}")
    translated_reviews.append(translate_if_amharic(text))
    time.sleep(0.5)  # Delay to avoid API rate limits

# Replace the 'review' column with translated reviews
df['review'] = translated_reviews
print(f"Processed reviews translation successfully. Total reviews: {len(df)}")


# Ensure column order
df_balanced = df[['review', 'rating', 'date', 'bank', 'source']]

# Save the processed DataFrame to CSV
output_file = 'data/processed/bank_app_reviews_processed.csv'
df_balanced.to_csv(output_file, index=False, encoding='utf-8')

# Print summary
print("\nSummary of processed reviews:")
for bank in df_balanced['bank'].unique():
    count = len(df_balanced[df_balanced['bank'] == bank])
    print(f"{bank}: {count} reviews")
print(f"Total: {len(df_balanced)} reviews saved to {output_file}.")


