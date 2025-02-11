import streamlit as st
import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# File to store data
DATA_FILE = "product_data.csv"

# Function to save fetched data to CSV
def save_data_to_csv(df):
    if os.path.exists(DATA_FILE):
        df.to_csv(DATA_FILE, mode='a', index=False, header=False)  # Append without headers
    else:
        df.to_csv(DATA_FILE, index=False)  # Create new file with headers

# Function to clean and preprocess data
def preprocess_data():
    if not os.path.exists(DATA_FILE):
        return None

    df = pd.read_csv(DATA_FILE)

    # Drop rows with missing values
    df.replace("No Data", np.nan, inplace=True)
    df.dropna(inplace=True)

    # Convert columns to numeric types
    df["No. of Ratings"] = df["No. of Ratings"].astype(int)
    df["Rating (⭐ out of 5)"] = df["Rating (⭐ out of 5)"].astype(float)
    df["Price"] = df["Price"].replace("[^0-9]", "", regex=True).astype(float)  # Remove non-numeric chars

    return df

# Function to train RandomForest model and predict price
def recommend_price(selected_product, cost_price):
    df = preprocess_data()
    if df is None or df.empty:
        st.error("⚠️ No valid data available for analysis.")
        return None

    # Extract features and target
    X = df[["No. of Ratings", "Rating (⭐ out of 5)"]]
    y = df["Price"]

    # Normalize data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    # Train RandomForest model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Get product details for prediction
    product_data = df[df["Product Title"].str.contains(selected_product, case=False, na=False)]

    if product_data.empty:
        st.error("❌ Product not found in dataset. Try another name.")
        return None

    product_features = product_data.iloc[0][["No. of Ratings", "Rating (⭐ out of 5)"]].values.reshape(1, -1)
    product_features_scaled = scaler.transform(product_features)

    # Predict price
    predicted_price = model.predict(product_features_scaled)[0]

    # Adjust recommendation to ensure profit
    recommended_price = max(cost_price * 1.2, predicted_price)  # Ensure at least 20% profit

    return recommended_price

# Streamlit UI
st.title("📊 Analyze & Recommend Price")

# Button to store the latest data
if st.button("Analyze Data"):
    df = preprocess_data()
    if df is not None:
        save_data_to_csv(df)
        st.success("✅ Data cleaned and stored successfully!")
    else:
        st.warning("⚠️ No data found to analyze.")

# Price recommendation
st.subheader("💰 Recommend Selling Price")
cost_price = st.number_input("Enter Cost Price (₹)", min_value=1.0, format="%.2f")
product_name = st.text_input("Enter Product Name for Prediction")

if st.button("Recommend Price"):
    if product_name.strip() and cost_price:
        recommended_price = recommend_price(product_name, cost_price)
        if recommended_price:
            st.success(f"✅ Recommended Selling Price: ₹{recommended_price:.2f}")
    else:
        st.warning("⚠️ Please enter both cost price and product name.")
