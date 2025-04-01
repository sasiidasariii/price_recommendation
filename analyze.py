import streamlit as st
import pandas as pd
import numpy as np
import os

import re
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from fuzzywuzzy import process  # Fuzzy string matching
import seaborn as sns

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob


# File to store data
DATA_FILE = "product_data.csv"

def save_data_to_csv(df):
    df.to_csv(DATA_FILE, index=False, mode='w')
    if os.path.exists(DATA_FILE):
        df.to_csv(DATA_FILE, mode='a', index=False, header=False)
    else:
        df.to_csv(DATA_FILE, index=False)

def preprocess_data():
    if not os.path.exists(DATA_FILE):
        return None

    df = pd.read_csv(DATA_FILE)

    # ✅ Replace unwanted text with NaN
    df.replace(["No Data", "No Rating", "Not Available"], np.nan, inplace=True)

    # ✅ Convert "Rating (⭐ out of 5)" to numeric, handling errors
    df["Rating (⭐ out of 5)"] = pd.to_numeric(df["Rating (⭐ out of 5)"], errors="coerce")

    # ✅ Ensure median rating calculation works
    median_rating = df["Rating (⭐ out of 5)"].dropna().median() if not df["Rating (⭐ out of 5)"].dropna().empty else 4.0
    df["Rating (⭐ out of 5)"].fillna(median_rating, inplace=True)

    # ✅ Convert "No. of Ratings" to integer safely
    df["No. of Ratings"] = pd.to_numeric(df["No. of Ratings"], errors="coerce").fillna(0).astype(int)

    # ✅ Normalize Price column (remove ₹ and commas)
    df["Price"] = df["Price"].replace({",": "", "₹": ""}, regex=True)

    # ✅ Convert Price to float, replacing errors with NaN
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

    # ✅ Remove rows where price is missing (if necessary)
    df.dropna(subset=["Price"], inplace=True)

    return df



def recommend_price(selected_product, cost_price):
    df = preprocess_data()
    if df is None or df.empty:
        st.error("⚠ No valid data available for analysis.")
        return None

    selected_product_lower = selected_product.lower().strip()

    # Exact match first
    exact_match = df[df["Product Title"].str.lower().str.strip() == selected_product_lower]
    if not exact_match.empty:
        best_match = selected_product
        score = 100
        df_filtered = exact_match[["Product Title", "No. of Ratings", "Rating (⭐ out of 5)", "Price"]]
    else:
        words = selected_product.split()
        brand_name = words[0]
        model_number = re.search(r"[\w\d\-]+$", selected_product)
        model_number = model_number.group(0) if model_number else ""

        df_filtered = df[df["Product Title"].str.contains(re.escape(brand_name), case=False, na=False)]
        if df_filtered.empty:
            st.error(f"❌ No products found for brand '{brand_name}'.")
            return None

        best_match = None
        score = 0

        if model_number:
            model_filtered = df_filtered[df_filtered["Product Title"].str.contains(re.escape(model_number), case=False, na=False)]
            if not model_filtered.empty:
                best_match = model_filtered["Product Title"].iloc[0]
                score = 95
                df_filtered = model_filtered

        if not best_match:
            keyword_filtered = df_filtered[df_filtered["Product Title"].str.contains(re.escape(" ".join(words[:3])), case=False, na=False)]
            if not keyword_filtered.empty:
                best_match = keyword_filtered["Product Title"].iloc[0]
                score = 90
                df_filtered = keyword_filtered

        if not best_match:
            product_names = df_filtered["Product Title"].tolist()
            matches = process.extractBests(selected_product, product_names, limit=5)
            if matches:
                best_match, score = matches[0]
                df_filtered = df_filtered[df_filtered["Product Title"] == best_match]

        if score < 85 or best_match is None:
            st.warning(f"⚠ No close match found (Best match: {best_match}, Confidence: {score}%)")
            return None

    st.info(f"🔍 Best match found: {best_match} (Confidence: {score}%)")

    df_filtered = df_filtered[["Product Title", "No. of Ratings", "Rating (⭐ out of 5)", "Price"]]

    if df_filtered.empty:
        st.error("❌ Product not found in dataset.")
        return None

    feature_columns = ["No. of Ratings", "Rating (⭐ out of 5)"]
    df_filtered["Log No. of Ratings"] = np.log1p(df_filtered["No. of Ratings"])  # ✅ Log transformation

    X = df_filtered[["Log No. of Ratings", "Rating (⭐ out of 5)"]]
    y = df_filtered["Price"]

    X.fillna(X.median(), inplace=True)
    y.fillna(y.median(), inplace=True)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=200, min_samples_split=5, random_state=42)
    model.fit(X_train, y_train)

    product_data = df[df["Product Title"] == best_match]
    if product_data.empty:
        st.error("❌ Best match not found in dataset for pricing.")
        return None

    product_features = product_data[["No. of Ratings", "Rating (⭐ out of 5)"]].copy()
    product_features["Log No. of Ratings"] = np.log1p(product_features["No. of Ratings"])
    product_features_scaled = scaler.transform(product_features[["Log No. of Ratings", "Rating (⭐ out of 5)"]])

    predicted_price = model.predict(product_features_scaled)[0]
    competitor_price = df_filtered["Price"].median()

    # Optimized final price (Weighted)
    recommended_price = (predicted_price * 0.5) + (competitor_price * 0.3) + (cost_price * 1.2 * 0.2)

    return round(recommended_price, 2)



def plot_price_analysis(df):
    """
    Plot three separate bar graphs for Flipkart, Reliance Digital, and Croma.
    Each graph represents product prices for that source.
    """
    if df is None or df.empty:
        st.warning("⚠ No data available for visualization.")
        return

    # Ensure the column names are correct
    if "Source" not in df.columns or "Product Title" not in df.columns or "Price" not in df.columns:
        st.error("🚨 Missing required columns in the dataset!")
        return

    # Convert "Price" column to numeric for plotting
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

    # Shorten product names for better readability
    df["Short Product Title"] = df["Product Title"].apply(lambda x: " ".join(x.split()[:3]) + "...")

    # Filter data for each source
    sources = ["Flipkart", "Reliance Digital", "Croma"]

    for source in sources:
        st.subheader(f"📊 {source} Price Analysis")
        source_data = df[df["Source"] == source]

        if source_data.empty:
            st.info(f"🔍 No data available for {source}.")
            continue

        # Create a figure and axis object explicitly
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(x="Short Product Title", y="Price", data=source_data, palette="viridis", ax=ax)
        
        ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha="center", fontsize=10)  # ✅ Labels straight
        ax.set_ylabel("Price (₹)")
        ax.set_xlabel("Product Title")
        ax.set_title(f"{source} - Product Prices", fontsize=12)
        plt.tight_layout()

        # Display the plot in Streamlit
        st.pyplot(fig)  # ✅ Explicitly pass figure





st.title("📊 Price Analysis & Recommendation")

if st.button("Analyze Data"):
    df = preprocess_data()
    if df is not None:
        save_data_to_csv(df)
        st.success("✅ Data cleaned and stored successfully!")
    else:
        st.warning("⚠ No data found to analyze.")

st.subheader("💰 Recommend Selling Price")
cost_price = st.number_input("Enter Cost Price (₹)", min_value=1.0, format="%.2f")
product_name = st.text_input("Enter Product Name for Prediction")

if st.button("Recommend Price"):
    if product_name.strip() and cost_price:
        recommended_price = recommend_price(product_name, cost_price)
        if recommended_price:
            st.success(f"✅ Recommended Selling Price: ₹{recommended_price:.2f}")
    else:
        st.warning("⚠ Please enter both cost price and product name.")

if st.button("Show Price Analysis Graph"):
    plot_price_analysis()
    
    
analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    if not text.strip():
        return "Neutral"

    vader_score = analyzer.polarity_scores(text)['compound']
    blob_score = TextBlob(text).sentiment.polarity

    combined_score = (vader_score + blob_score) / 2  # Averaging both

    return "Positive" if combined_score > 0.2 else "Negative" if combined_score < -0.2 else "Neutral"