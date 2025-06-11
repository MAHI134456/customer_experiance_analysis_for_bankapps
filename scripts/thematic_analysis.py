import pandas as pd
import os
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re

# Download NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

def load_data(input_file):
    """Load the sentiment-analyzed CSV file."""
    try:
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} reviews from {input_file}.")
        return df
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        return None

def preprocess_text(text):
    """Preprocess text for TF-IDF (tokenization, stopword removal)."""
    if pd.isna(text) or not isinstance(text, str):
        return ''
    # Tokenize
    tokens = word_tokenize(text.lower())
    # Remove stopwords and non-alphabetic tokens
    stop_words = set(stopwords.words('english'))
    tokens = [t for t in tokens if t.isalpha() and t not in stop_words]
    return ' '.join(tokens)

def extract_keywords(df, ngram_range=(1, 2), max_features=100):
    """Extract keywords and n-grams using TF-IDF for each bank."""
    keyword_dict = {}
    for bank in df['bank'].unique():
        bank_reviews = df[df['bank'] == bank]['processed_text']
        if len(bank_reviews) < 2:
            print(f"Skipping {bank}: insufficient reviews.")
            keyword_dict[bank] = []
            continue
        # Initialize TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            max_features=max_features,
            stop_words='english'
        )
        # Fit and transform
        tfidf_matrix = vectorizer.fit_transform(bank_reviews)
        feature_names = vectorizer.get_feature_names_out()
        # Get top keywords by mean TF-IDF score
        tfidf_scores = tfidf_matrix.mean(axis=0).A1
        keywords = [(feature_names[i], tfidf_scores[i]) for i in range(len(feature_names))]
        keywords = sorted(keywords, key=lambda x: x[1], reverse=True)[:20]  # Top 20
        keyword_dict[bank] = [kw[0] for kw in keywords]
        print(f"Extracted keywords for {bank}: {keyword_dict[bank][:10]}...")
    return keyword_dict

def cluster_keywords(keyword_dict):
    """Cluster keywords into 3-5 themes per bank using rule-based logic."""
    theme_dict = {}
    for bank, keywords in keyword_dict.items():
        themes = {
            'Account Access Issues': [],
            'Transaction Performance': [],
            'User Interface & Experience': [],
            'Customer Support': []
        }
        # Rule-based clustering logic
        for kw in keywords:
            kw_lower = kw.lower()
            # Account Access Issues
            if any(term in kw_lower for term in ['login', 'access', 'password', 'authentication', 'account', 'error']):
                themes['Account Access Issues'].append(kw)
            # Transaction Performance
            elif any(term in kw_lower for term in ['transfer', 'payment', 'transaction', 'slow', 'delay', 'failed']):
                themes['Transaction Performance'].append(kw)
            # User Interface & Experience
            elif any(term in kw_lower for term in ['interface', 'ui', 'design', 'easy', 'navigation', 'app']):
                themes['User Interface & Experience'].append(kw)
            # Customer Support
            elif any(term in kw_lower for term in ['support', 'service', 'help', 'response', 'customer']):
                themes['Customer Support'].append(kw)
        # Filter out empty themes
        themes = {k: v for k, v in themes.items() if v}
        theme_dict[bank] = themes
        print(f"\nThemes for {bank}:")
        for theme, kws in themes.items():
            print(f"{theme}: {kws}")
    return theme_dict

def assign_themes_to_reviews(df, theme_dict):
    """Assign themes to each review based on keyword presence."""
    df['themes'] = ''
    for bank in df['bank'].unique():
        if bank not in theme_dict:
            continue
        bank_mask = df['bank'] == bank
        for theme, keywords in theme_dict[bank].items():
            if not keywords:
                continue
            # Create regex pattern for keywords
            pattern = '|'.join(r'\b{}\b'.format(re.escape(kw)) for kw in keywords)
            # Assign theme if any keyword is present
            df.loc[bank_mask, 'themes'] = df.loc[bank_mask].apply(
                lambda row: row['themes'] + f"{theme};" 
                if isinstance(row['review'], str) and re.search(pattern, row['review'], re.IGNORECASE) 
                else row['themes'],
                axis=1
            )
    # Remove trailing semicolons and handle empty themes
    df['themes'] = df['themes'].str.rstrip(';').replace('', 'No Theme')
    return df

def save_data(df, output_file):
    """Save the DataFrame with thematic analysis results."""
    # Select relevant columns
    df_final = df[[
        'review_id', 'review', 'distilbert_label', 'distilbert_positive',
        'rating', 'date', 'bank', 'source', 'themes'
    ]]
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_final.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Saved thematic analysis results to {output_file}")

def print_summary(df):
    """Print summary of thematic analysis."""
    print("\nThematic Analysis Summary:")
    for bank in df['bank'].unique():
        print(f"\n{bank}:")
        theme_counts = df[df['bank'] == bank]['themes'].str.split(';', expand=True).stack().value_counts()
        print(theme_counts)
    print("\nSample Results (first 5 rows):")
    print(df[['review_id', 'bank', 'review', 'distilbert_label', 'themes']].head())

def main():
    """Main function for thematic analysis of bank app reviews."""
    input_file = 'data/processed/bank_app_reviews_sentiment.csv'
    output_file = 'data/processed/bank_app_reviews_thematic.csv'

    # Load data
    df = load_data(input_file)
    if df is None:
        return

    # Ensure review column is string type
    df['review'] = df['review'].fillna('').astype(str)

    # Add review_id
    df['review_id'] = range(1, len(df) + 1)

    # Preprocess text for TF-IDF
    df['processed_text'] = df['review'].apply(preprocess_text)

    # Extract keywords
    keyword_dict = extract_keywords(df)

    # Cluster keywords into themes
    theme_dict = cluster_keywords(keyword_dict)

    # Assign themes to reviews
    df = assign_themes_to_reviews(df, theme_dict)

    # Save results
    save_data(df, output_file)

    # Print summary
    print_summary(df)

if __name__ == "__main__":
    main()