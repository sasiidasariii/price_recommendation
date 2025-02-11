import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from fetch import setup_driver, fetch_flipkart_products, fetch_croma_products, fetch_reliance_products
from analyze import save_data_to_csv, preprocess_data, recommend_price

# Streamlit UI
st.title("📌 Product Price & Rating Comparison")

# User input
product_name = st.text_input("🔍 Enter Product Name:", "")

if st.button("Find Prices", key="find_prices_btn"):
    if product_name.strip():
        st.write("🔗 Searching for product...")

        flipkart_url = f"https://www.flipkart.com/search?q={product_name.replace(' ', '+')}"
        reliance_url = f"https://www.reliancedigital.in/search?q={product_name.replace(' ', '%20')}:relevance"
        croma_url = f"https://www.croma.com/searchB?q={product_name.replace(' ', '%20')}%3Arelevance&text={product_name.replace(' ', '%20')}"

        # Flipkart XPaths
        flipkart_title_xpath = "//div[contains(@class, 'KzDlHZ')]"
        flipkart_price_xpath = "//div[contains(@class, 'Nx9bqj')]"
        flipkart_rating_xpath = "//div[contains(@class, 'XQDdHH')]"
        flipkart_ratings_count_xpath = "//span[contains(@class, 'Wphh3N')]/span/span[1]"

        # Croma & Reliance XPaths
        croma_title_xpath = "//h3[contains(@class, 'product-title')]"
        croma_price_xpath = "//span[contains(@class, 'amount')]"
        croma_product_link_xpath = "//div[contains(@class, 'product')]//a"
        croma_rating_xpath = "/html/body/main/div/div[3]/div/div[1]/div[2]/div[1]/div/div/div/div[3]/div/ul/li[1]/div[1]/span[1]/span"
        croma_ratings_count_xpath = '//span[contains(@class, "text scroll-to-review")]/span'

        reliance_title_xpath = "//p[contains(@class, 'sp__name')]"
        reliance_price_xpath = "//span[contains(@class, 'TextWeb__Text-sc-1cyx778-0')]/span[2]"
        reliance_product_link_xpath = "//div[contains(@class, 'grid')]//a"
        reliance_rating_xpath = "//span[contains(@class, 'TextWeb__Text-sc-1cyx778-0') and contains(text(), '/5')]"
        reliance_ratings_count_xpath = "//span[contains(@class, 'TextWeb__Text-sc-1cyx778-0 dzLzNm')]"

        # Set up WebDriver
        wd = setup_driver()

        # Fetch product data
        flipkart_data = fetch_flipkart_products(wd, flipkart_url, flipkart_title_xpath, flipkart_price_xpath, flipkart_rating_xpath, flipkart_ratings_count_xpath)
        croma_data = fetch_croma_products(wd, croma_url, croma_title_xpath, croma_price_xpath, croma_product_link_xpath, croma_rating_xpath, croma_ratings_count_xpath)
        reliance_data = fetch_reliance_products(wd, reliance_url, reliance_title_xpath, reliance_price_xpath, reliance_product_link_xpath, reliance_rating_xpath, reliance_ratings_count_xpath)

        wd.quit()

        # Convert fetched data into DataFrames
        df_flipkart = pd.DataFrame(flipkart_data, columns=["Product Title", "Price", "Rating (⭐ out of 5)", "No. of Ratings"])
        df_reliance = pd.DataFrame(reliance_data, columns=["Product Title", "Price", "Rating (⭐ out of 5)", "No. of Ratings"])
        df_croma = pd.DataFrame(croma_data, columns=["Product Title", "Price", "Rating (⭐ out of 5)", "No. of Ratings"])

        # Combine all data and save for analysis
        df_combined = pd.concat([df_flipkart, df_reliance, df_croma], ignore_index=True)
        save_data_to_csv(df_combined)  # Save for analysis

        # Display results
        st.subheader("🛒 Flipkart")
        st.table(df_flipkart)

        st.subheader("🛒 Reliance Digital")
        st.table(df_reliance)

        st.subheader("🛒 Croma")
        st.table(df_croma)
    else:
        st.warning("⚠️ Please enter a product name.")

# Button to analyze stored data
if st.button("Analyze Data", key="analyze_data_btn"):
    df_cleaned = preprocess_data()
    if df_cleaned is not None:
        st.success("✅ Data cleaned and stored successfully!")
    else:
        st.warning("⚠️ No valid data found for analysis.")

# Price Recommendation Section
st.subheader("💰 Recommend Selling Price")
cost_price = st.number_input("Enter Cost Price (₹)", min_value=1.0, format="%.2f")
selected_product = st.text_input("Enter Product Name for Prediction")

if st.button("Recommend Price", key="recommend_price_btn"):
    if selected_product.strip() and cost_price:
        recommended_price = recommend_price(selected_product, cost_price)
        if recommended_price:
            st.success(f"✅ Recommended Selling Price: ₹{recommended_price:.2f}")
    else:
        st.warning("⚠️ Please enter both cost price and product name.")
