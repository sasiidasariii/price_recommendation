import streamlit as st
import pandas as pd
from selenium import webdriver
from fetch import setup_driver, fetch_flipkart_products, fetch_croma_products, fetch_reliance_products, flipkart_product_urls, fetch_reviews
from analyze import analyze_sentiment
from analyze import save_data_to_csv, preprocess_data, recommend_price, plot_price_analysis

# 🎨 Streamlit UI 
st.set_page_config(page_title="Price & Rating Comparison", page_icon="📊", layout="wide")

# ✅ Initialize session state variables if they don't exist
if "df_flipkart" not in st.session_state:
    st.session_state.df_flipkart = None
if "df_reliance" not in st.session_state:
    st.session_state.df_reliance = None
if "df_croma" not in st.session_state:
    st.session_state.df_croma = None

# 🎯 Sidebar
st.sidebar.title("🔍 Search & Compare")
product_name = st.sidebar.text_input("Enter Product Name")

if st.sidebar.button("Find Prices", key="find_prices_btn"):
    if product_name.strip():
        st.sidebar.write("⏳ Searching for product...")

        flipkart_url = f"https://www.flipkart.com/search?q={product_name.replace(' ', '+')}"
        reliance_url = f"https://www.reliancedigital.in/products?q={product_name.replace(' ', '%20')}&page_no=1&page_size=12&page_type=number"
        croma_url = f"https://www.croma.com/searchB?q={product_name.replace(' ', '%20')}%3Arelevance"

        # Set up WebDriver
        wd = setup_driver()

        # Flipkart XPaths
        flipkart_title_xpath = "//div[contains(@class, 'KzDlHZ')]"
        flipkart_price_xpath = "//div[contains(@class, 'Nx9bqj')]"
        flipkart_rating_xpath = "//div[contains(@class, 'XQDdHH')]"
        flipkart_ratings_count_xpath = "//span[contains(@class, 'Wphh3N')]/span/span[1]"
        product_link_xpath = "//div[@class='tUxRFH']//a[@class='CGtC98']"


        # Croma XPaths
        croma_title_xpath = "//h3[contains(@class, 'product-title')]"
        croma_price_xpath = "//span[contains(@class, 'amount')]"
        croma_product_link_xpath = "//div[contains(@class, 'product')]//a"
        croma_rating_xpath = "//span[contains(@style, 'color')]"
        croma_ratings_count_xpath = "//a[contains(@class, 'pr-review')]"

        # Reliance XPaths
        reliance_title_xpath = "//div[contains(@class, 'product-card-title')]"
        reliance_price_xpath = "//div[contains(@class, 'price-container')]//div[contains(@class, 'price')]"
        reliance_product_link_xpath = "//div[contains(@class, 'grid')]//a"
        reliance_rating_xpath = "//span[contains(@class, 'rd-feedback-service-average-rating-total-count')]"
        reliance_ratings_count_xpath = "//span[contains(@class, 'rd-feedback-service-jds-desk-body-s')]"

        # ✅ Fetch product data
        st.session_state.df_flipkart = pd.DataFrame(
            fetch_flipkart_products(
                        wd, flipkart_url, flipkart_title_xpath, flipkart_price_xpath, 
                        flipkart_rating_xpath, flipkart_ratings_count_xpath, product_link_xpath
                    )
                    ,
            columns=["Product Title", "Price", "Rating (⭐ out of 5)", "No. of Ratings"]
        )
        if not st.session_state.df_flipkart.empty:
            st.session_state.df_flipkart["Source"] = "Flipkart"  # ✅ Add source column

        st.session_state.df_reliance = pd.DataFrame(
            fetch_reliance_products(wd, reliance_url, reliance_title_xpath, reliance_price_xpath, reliance_product_link_xpath, reliance_rating_xpath, reliance_ratings_count_xpath),
            columns=["Product Title", "Price", "Rating (⭐ out of 5)", "No. of Ratings"]
        )
        if not st.session_state.df_reliance.empty:
            st.session_state.df_reliance["Source"] = "Reliance Digital"  # ✅ Add source column

        st.session_state.df_croma = pd.DataFrame(
            fetch_croma_products(wd, croma_url, croma_title_xpath, croma_price_xpath, croma_product_link_xpath, croma_rating_xpath, croma_ratings_count_xpath),
            columns=["Product Title", "Price", "Rating (⭐ out of 5)", "No. of Ratings"]
        )
        if not st.session_state.df_croma.empty:
            st.session_state.df_croma["Source"] = "Croma"  # ✅ Add source column

        wd.quit()

        # Combine all data and save for analysis
        df_combined = pd.concat([st.session_state.df_flipkart, st.session_state.df_reliance, st.session_state.df_croma], ignore_index=True)
        if not df_combined.empty:
            save_data_to_csv(df_combined)
            st.sidebar.success("✅ Product Data Fetched!")
        else:
            st.sidebar.warning("⚠ No data found for the entered product.")
    else:
        st.sidebar.warning("⚠ Please enter a product name.")

# 🏷 Main Title
st.title("📊 Product Price & Rating Comparison")

# 🔹 Tabs for better organization
tab1, tab2, tab3, tab4 = st.tabs(["🛍 Compare Prices", "📈 Price Analysis", "💰 Recommend Price", "📝 Review Analysis"])

# 📌 Tab 1 - Display Prices from Different Retailers
with tab1:
    st.header("🛒 Product Prices from Online Retailers")

    if product_name:
        st.subheader("🛒 Flipkart")
        if st.session_state.df_flipkart is not None:
            st.table(st.session_state.df_flipkart)
        else:
            st.info("🔍 Search for a product to see Flipkart results.")

        st.subheader("🛒 Reliance Digital")
        if st.session_state.df_reliance is not None:
            st.table(st.session_state.df_reliance)
        else:
            st.info("🔍 Search for a product to see Reliance results.")

        st.subheader("🛒 Croma")
        if st.session_state.df_croma is not None:
            st.table(st.session_state.df_croma)
        else:
            st.info("🔍 Search for a product to see Croma results.")

# 📌 Tab 2 - Analyze Data & Visualize Prices
# 📌 Tab 2 - Analyze Data & Visualize Prices
with tab2:
    st.header("📈 Price & Rating Analysis")

    if st.button("Analyze Data", key="analyze_data_btn"):
        df_cleaned = preprocess_data()
        if df_cleaned is not None:
            st.success("✅ Data cleaned and stored successfully!")
        else:
            st.warning("⚠ No valid data found for analysis.")

    # Show Price Analysis Graphs
    if st.button("Show Price Analysis Graph"):
        df = preprocess_data()
        if df is not None:
            plot_price_analysis(df)  # ✅ Pass df to the function
        else:
            st.warning("⚠ No data found for visualization.")



# 📌 Tab 3 - Recommend Price Based on Analysis
with tab3:
    st.header("💰 Recommend Optimal Selling Price")

    cost_price = st.number_input("Enter Cost Price (₹)", min_value=1.0, format="%.2f")
    selected_product = st.text_input("Enter Product Name for Prediction")

    if st.button("Recommend Price", key="recommend_price_btn"):
        if selected_product.strip() and cost_price:
            recommended_price = recommend_price(selected_product, cost_price)  # ✅ Fix: Removed extra 'df' argument

            if recommended_price:
                st.success(f"✅ Recommended Selling Price: ₹{recommended_price:.2f}")
        else:
            st.warning("⚠ Please enter both cost price and product name.")
            
            
# New session state for storing review data
if "reviews_data" not in st.session_state:
    st.session_state.reviews_data = None
    
    
# 📌 Tab 4 - Review Sentiment Analysis
with tab4:
    st.header("📝 Sentiment Analysis of Product Reviews")

    if st.button("Fetch & Analyze Reviews", key="fetch_reviews_btn"):
        if st.session_state.df_flipkart is not None:
            wd = setup_driver()

            all_reviews = []
            
            # Iterate over stored URLs and fetch reviews
            for product, url in flipkart_product_urls.items():
                reviews = fetch_reviews(wd, url, "//div[@class='ZmyHeo']//div[contains(@class, '')]")
                sentiments = [analyze_sentiment(review) for review in reviews]

                for review, sentiment in zip(reviews, sentiments):
                    all_reviews.append({"Product": product, "Review": review, "Sentiment": sentiment})

            wd.quit()

            # Convert to DataFrame and store in session state
            st.session_state.reviews_data = pd.DataFrame(all_reviews)

        if st.session_state.reviews_data is not None and not st.session_state.reviews_data.empty:
            st.success("✅ Reviews fetched and analyzed successfully!")
            st.dataframe(st.session_state.reviews_data)

            # 📊 Show Sentiment Distribution
            st.subheader("📊 Sentiment Distribution")
            sentiment_counts = st.session_state.reviews_data["Sentiment"].value_counts()
            st.bar_chart(sentiment_counts)
        else:
            st.warning("⚠ No reviews found for analysis.")

