# Customer Experience Analytics for Fintech Apps

A data-driven project analyzing customer reviews from Ethiopian banks' mobile apps to uncover insights about user satisfaction, pain points, and feature requests.

---

## Overview

This project supports **Omega Consultancy**, a firm advising banks on improving their mobile applications. The goal is to help **Commercial Bank of Ethiopia (CBE)**, **Bank of Abyssinia (BOA)**, and **Dashen Bank** improve their digital banking experiences using real user feedback from the **Google Play Store**.

We analyze:
- Sentiment (positive/negative/neutral)
- Common themes and complaints
- Feature suggestions
- App performance issues (e.g., crashes, slow loading)

The output includes:
- Cleaned datasets
- Visualizations
- Actionable recommendations

---

## Features

Scrapes Google Play Store reviews  
Analyzes sentiment using NLP  
Extracts key themes and topics  
Visualizes trends across banks  
Stores cleaned data in Oracle database  
Includes GitHub Actions CI pipeline  

---

# Folder structure

customer_experience_analytics/
├── data/
│ ├── raw/ # Raw scraped reviews
│ └── processed/ # Cleaned review data
├── reports/
│ └── figures/ # Sentiment charts, word clouds
├── notebooks/ # Exploratory analysis and visualization
├── scripts/
│ ├── scraper.py # Scrapes reviews from Google Play
│ ├── sentiment_analysis.py # Analyzes tone of reviews
│ └── theme_extractor.py # Extracts common topics and complaints
├── .github/workflows/
│ └── ci.yml # Runs tests automatically
├── requirements.txt # Libraries used in the project
├── README.md # You're here!

