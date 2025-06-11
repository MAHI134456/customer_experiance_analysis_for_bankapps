import pandas as pd
import os
from transformers import pipeline
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
from statistics import mean

# Download NLTK resources for VADER
nltk.download('vader_lexicon', quiet=True)

def load_data(input_file):
    """Load the preprocessed CSV file."""
    try:
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} reviews from {input_file}.")
        return df
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        return None

def distilbert_sentiment_analysis(reviews):
    """Compute sentiment scores using DistilBERT."""
    classifier = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english",
        tokenizer="distilbert-base-uncased-finetuned-sst-2-english",
        truncation=True,
        max_length=512
    )
    sentiments = []
    for i, review in enumerate(reviews):
        if pd.isna(review) or not isinstance(review, str) or review.strip() == '':
            sentiments.append({'label': 'NEUTRAL', 'score': 0.0})
            continue
        print(f"Processing DistilBERT sentiment for review {i+1}/{len(reviews)}")
        try:
            result = classifier(review)[0]
            sentiments.append(result)
        except Exception as e:
            print(f"Error processing review {i+1}: {e}")
            sentiments.append({'label': 'NEUTRAL', 'score': 0.0})
    return sentiments

def vader_sentiment_analysis(reviews):
    """Compute sentiment scores using VADER."""
    sia = SentimentIntensityAnalyzer()
    sentiments = []
    for i, review in enumerate(reviews):
        if pd.isna(review) or not isinstance(review, str) or review.strip() == '':
            sentiments.append({'neg': 0.0, 'neu': 1.0, 'pos': 0.0, 'compound': 0.0})
            continue
        print(f"Processing VADER sentiment for review {i+1}/{len(reviews)}")
        scores = sia.polarity_scores(review)
        sentiments.append(scores)
    return sentiments

def aggregate_sentiments(df, distilbert_scores, vader_scores):
    """Aggregate sentiment scores by bank and rating."""
    df['distilbert_label'] = [s['label'] for s in distilbert_scores]
    df['distilbert_score'] = [s['score'] if s['label'] != 'NEUTRAL' else 0.0 for s in distilbert_scores]
    df['distilbert_positive'] = [s['score'] if s['label'] == 'POSITIVE' else 1.0 - s['score'] if s['label'] == 'NEGATIVE' else 0.5 for s in distilbert_scores]
    df['distilbert_negative'] = [1.0 - s['score'] if s['label'] == 'POSITIVE' else s['score'] if s['label'] == 'NEGATIVE' else 0.5 for s in distilbert_scores]
    df['vader_pos'] = [s['pos'] for s in vader_scores]
    df['vader_neg'] = [s['neg'] for s in vader_scores]
    df['vader_neu'] = [s['neu'] for s in vader_scores]
    df['vader_compound'] = [s['compound'] for s in vader_scores]

    # Aggregate by bank and rating
    aggregation = df.groupby(['bank', 'rating']).agg({
        'distilbert_positive': 'mean',
        'distilbert_negative': 'mean',
        'vader_pos': 'mean',
        'vader_neg': 'mean',
        'vader_neu': 'mean',
        'vader_compound': 'mean',
        'review': 'count'
    }).rename(columns={'review': 'review_count'}).reset_index()

    return df, aggregation

def save_data(df, aggregation, output_file, agg_output_file):
    """Save the DataFrame with sentiment scores and aggregations."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False, encoding='utf-8')
    aggregation.to_csv(agg_output_file, index=False, encoding='utf-8')
    print(f"Saved detailed results to {output_file}")
    print(f"Saved aggregated results to {agg_output_file}")

def print_summary(df, aggregation):
    """Print summary of sentiment analysis."""
    print("\nSentiment Analysis Summary:")
    print("\nDetailed Results (first 5 rows):")
    print(df[['bank', 'rating', 'distilbert_label', 'distilbert_positive', 'distilbert_negative', 'vader_compound']].head())
    print("\nAggregated Results (mean sentiment by bank and rating):")
    print(aggregation)

def main():
    """Main function for sentiment analysis of bank app reviews."""
    input_file = 'data/processed/bank_app_reviews_processed.csv'
    output_file = 'data/processed/bank_app_reviews_sentiment.csv'
    agg_output_file = 'data/processed/bank_app_reviews_sentiment_aggregated.csv'

    # Load data
    df = load_data(input_file)
    if df is None:
        return

    # Perform sentiment analysis
    distilbert_scores = distilbert_sentiment_analysis(df['review'])
    vader_scores = vader_sentiment_analysis(df['review'])

    # Aggregate results
    df, aggregation = aggregate_sentiments(df, distilbert_scores, vader_scores)

    # Save results
    save_data(df, aggregation, output_file, agg_output_file)

    # Print summary
    print_summary(df, aggregation)

if __name__ == "__main__":
    main()