import pandas as pd
import os
import re
import time
import emoji
import unicodedata
from langdetect import detect, DetectorFactory, LangDetectException
from deep_translator import GoogleTranslator
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk

# Set seed for reproducibility
DetectorFactory.seed = 42

# Download NLTK resources
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)

def load_data(input_file):
    """Load the raw CSV file and validate its existence."""
    try:
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} reviews from {input_file}.")
        return df
    except FileNotFoundError:
        print(f"Error: {input_file} not found. Please ensure the raw data exists.")
        exit(1)

def remove_duplicates(df):
    """Remove duplicate reviews based on specified columns."""
    initial_count = len(df)
    df = df.drop_duplicates(subset=['review', 'rating', 'date', 'bank', 'source'], keep='first')
    print(f"Removed {initial_count - len(df)} duplicate reviews. {len(df)} reviews remain.")
    return df

def handle_missing_data(df):
    """Handle missing data in the DataFrame."""
    initial_count = len(df)
    df['review'] = df['review'].fillna('').astype(str)
    df['rating'] = df['rating'].fillna(0).astype(int)
    df['source'] = df['source'].fillna('Google Play').astype(str)
    df = df.dropna(subset=['date', 'bank'])
    print(f"Dropped {initial_count - len(df)} rows with missing date or bank. {len(df)} reviews remain.")
    return df

def normalize_dates(df):
    """Normalize date column to YYYY-MM-DD format."""
    try:
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    except ValueError as e:
        print(f"Error normalizing dates: {e}. Dropping rows with invalid dates.")
        df = df[df['date'].apply(lambda x: pd.to_datetime(x, errors='coerce').notna())]
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        print(f"Dropped additional rows with invalid dates. {len(df)} reviews remain.")
    return df

def balance_reviews(df, target_count=400):
    """Balance the number of reviews per bank to the target count."""
    balanced_dfs = []
    for bank in df['bank'].unique():
        bank_reviews = df[df['bank'] == bank]
        if len(bank_reviews) > target_count:
            bank_reviews = bank_reviews.sample(n=target_count, random_state=42)
        elif len(bank_reviews) < target_count:
            print(f"Warning: {bank} has only {len(bank_reviews)} reviews, less than {target_count}.")
        balanced_dfs.append(bank_reviews)
        print(f"{bank}: {len(bank_reviews)} reviews after balancing.")
    return pd.concat(balanced_dfs)

def detect_language(text):
    """Detect the language of the text, prioritizing Amharic if Ethiopic characters are present."""
    if pd.isna(text) or not isinstance(text, str) or text.strip() == '':
        return 'unknown'
    try:
        if bool(re.search(r'[\u1200-\u137F]', text)):
            return 'am'
        return detect(text)
    except LangDetectException:
        return 'am' if bool(re.search(r'[\u1200-\u137F]', text)) else 'unknown'

def translate_amharic(text, translator):
    """Translate text if detected as Amharic."""
    if pd.isna(text) or not isinstance(text, str) or text.strip() == '':
        return ''
    lang = detect_language(text)
    print(f"Detected language for '{text[:30]}...': {lang}")
    if lang == 'am':
        for attempt in range(3):
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
    return text

def translate_reviews(df):
    """Apply translation to all reviews."""
    translator = GoogleTranslator(source='am', target='en')
    translated_reviews = []
    for i, text in enumerate(df['review']):
        print(f"Processing review {i+1}/{len(df)}")
        translated_reviews.append(translate_amharic(text, translator))
        time.sleep(0.5)
    df['review'] = translated_reviews
    print(f"Processed reviews translation successfully. Total reviews: {len(df)}")
    return df

def clean_text(text):
    """Clean text by removing emojis, punctuation, and stopwords, and converting to lowercase."""
    if pd.isna(text) or not isinstance(text, str):
        return ''
    # Step 1: Remove emojis using emoji library
    text = emoji.replace_emoji(text, replace='')
    # Step 2: Remove any remaining emoji-like Unicode characters
    text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002700-\U000027BF]', '', text)
    # Step 3: Normalize Unicode to remove combining characters
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    # Step 4: Remove punctuation and convert to lowercase
    text = re.sub(r'[^\w\s]', '', text.lower())
    # Step 5: Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = text.split()
    cleaned = ' '.join(word for word in tokens if word not in stop_words)
    return cleaned

def tokenize_text(text):
    """Tokenize text into words."""
    if pd.isna(text) or not isinstance(text, str):
        return []
    return word_tokenize(text)

def process_reviews(df):
    """Apply text cleaning and tokenization to reviews, overwriting review column."""
    df['review'] = df['review'].apply(clean_text)
    df['tokens'] = df['review'].apply(tokenize_text)
    return df

def save_data(df, output_file):
    """Save the processed DataFrame to CSV."""
    df_final = df[['review', 'tokens', 'rating', 'date', 'bank', 'source']]
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_final.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Saved {len(df_final)} reviews to {output_file}.")

def print_summary(df):
    """Print summary of processed reviews by bank."""
    print("\nSummary of processed reviews:")
    for bank in df['bank'].unique():
        count = len(df[df['bank'] == bank])
        print(f"{bank}: {count} reviews")
    print(f"Total: {len(df)} reviews.")

def main():
    """Main function to preprocess bank app reviews."""
    input_file = 'data/raw/bank_app_reviews.csv'
    output_file = 'data/processed/bank_app_reviews_processed.csv'

    # Pipeline
    df = load_data(input_file)
    df = remove_duplicates(df)
    df = handle_missing_data(df)
    df = normalize_dates(df)
    df = balance_reviews(df, target_count=400)
    df = translate_reviews(df)
    df = process_reviews(df)
    save_data(df, output_file)
    print_summary(df)

if __name__ == "__main__":
    main()