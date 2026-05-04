import streamlit as st
import pandas as pd
from selenium import webdriver
from fetch import setup_driver, fetch_flipkart_products, fetch_croma_products, fetch_reliance_products, flipkart_product_urls, fetch_reviews
from analyze import analyze_sentiment
from analyze import save_data_to_csv, preprocess_data, recommend_price
from visualization import plot_price_analysis
from wordcloud import WordCloud
import time
import matplotlib.pyplot as plt

# 🎨 Streamlit UI - Page Config
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
model_name = st.sidebar.text_input("Enter Model Name (optional)")
color = st.sidebar.text_input("Enter Color (optional)")
price_range = st.sidebar.slider("Enter Price Range", 0, 1000000, (0, 1000000))

if st.sidebar.button("Find Prices", key="find_prices_btn"):
    if product_name.strip():
        # Combine the user inputs (product name, model name, color)
        search_query = product_name
        if model_name.strip():
            search_query += " " + model_name
        if color.strip():
            search_query += " " + color

        st.sidebar.write(f"⏳ Searching for products matching: {search_query}...")

        flipkart_url = f"https://www.flipkart.com/search?q={search_query.replace(' ', '+')}"
        reliance_url = f"https://www.reliancedigital.in/products?q={search_query.replace(' ', '%20')}&page_no=1&page_size=12&page_type=number"
        croma_url = f"https://www.croma.com/searchB?q={search_query.replace(' ', '%20')}%3Arelevance"

        # Set up WebDriver
        wd = setup_driver()

        # Flipkart XPaths
        # Flipkart XPaths
        flipkart_title_xpath = "//div[contains(@class,'RG5Slk')]"
        flipkart_price_xpath = "//div[contains(@class,'hZ3P6w')]"
        flipkart_rating_xpath = "//div[contains(@class,'MKiFS6')]"
        flipkart_ratings_count_xpath = "//span[contains(text(),'Ratings')]"
        product_link_xpath = "//a[contains(@class,'k7wcnx')]"


        # Croma XPaths
        croma_title_xpath = "//h3[contains(@class, 'product-title')]"
        croma_price_xpath = "//span[contains(@class, 'amount')]"
        croma_product_link_xpath = "//div[contains(@class, 'product')]//a"
        croma_rating_xpath = "//span[contains(@style, 'color')]"
        croma_ratings_count_xpath = "//a[contains(@class, 'pr-review')]"

        # Reliance XPaths
        reliance_title_xpath = "//div[contains(@class, 'product-card-title')]"
        reliance_price_xpath = "//div[contains(@class,'price-container')]//div[contains(@class,'price')]"
        reliance_product_link_xpath = "//div[contains(@class, 'grid')]//a"
        reliance_rating_xpath = "//span[contains(@class, 'rd-feedback-service-average-rating-total-count')]"
        reliance_ratings_count_xpath = "//span[contains(@class, 'rd-feedback-service-jds-desk-body-s.rd-feedback-service-jds-color-grey-80')]"

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
    # ✅ Button to trigger the dashboard
    if "show_analysis" not in st.session_state:
        st.session_state.show_analysis = False

    # if st.button("🔍 Show Price Analysis"):
    #     st.session_state.show_analysis = True

    if st.button("Show Price Analysis Graph"): 
        st.session_state.show_analysis = True  
    # 📊 Display dashboard if button was clicked

    if st.session_state.show_analysis:
        try:
            plot_price_analysis(product_name)
        except Exception as e:
            pass

    # if st.button("Show Price Analysis Graph"): 
    #     st.session_state.show_analysis = True   

    if st.session_state.show_analysis:    
        df = preprocess_data()
        if df is not None:
            plot_price_analysis()  # ✅ Pass df to the function
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

            for product, url in flipkart_product_urls.items():

                reviews = fetch_reviews(wd, url)

                sentiments = [analyze_sentiment(r) for r in reviews]

                for review, sentiment in zip(reviews, sentiments):
                    all_reviews.append({
                        "Product": product,
                        "Review": review,
                        "Sentiment": sentiment
                    })

            wd.quit()

            st.session_state.reviews_data = pd.DataFrame(all_reviews)

        if (
            st.session_state.reviews_data is not None
            and not st.session_state.reviews_data.empty
        ):

            st.success("✅ Reviews fetched successfully!")

            df_reviews = st.session_state.reviews_data

            st.dataframe(df_reviews)

            # 📊 Sentiment Bar Chart
            st.subheader("📊 Sentiment Distribution")

            sentiment_counts = df_reviews["Sentiment"].value_counts()

            st.bar_chart(sentiment_counts)

            # 🥧 Sentiment Pie Chart
            st.subheader("🥧 Sentiment Ratio")

            fig, ax = plt.subplots()
            ax.pie(
                sentiment_counts,
                labels=sentiment_counts.index,
                autopct="%1.1f%%",
                startangle=90
            )
            ax.axis("equal")

            st.pyplot(fig)
            plt.close(fig)

            # ☁️ WordCloud
            st.subheader("☁️ Word Cloud of Reviews")

            text = " ".join(df_reviews["Review"])

            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color="white"
            ).generate(text)

            fig_wc, ax_wc = plt.subplots(figsize=(10,5))
            ax_wc.imshow(wordcloud)
            ax_wc.axis("off")

            st.pyplot(fig_wc)
            plt.close(fig_wc)

        else:
            st.warning("⚠ No reviews found.")