
import streamlit as st
import pandas as pd
import plotly.express as px
import time  # corrected import

# 🛑 Load Data with Dynamic Refresh
@st.cache_data(ttl=60)  # Refresh data every 60 seconds
def load_data():
    df = pd.read_csv("product_data.csv")
    df["Rating"] = df["Rating (⭐ out of 5)"].copy()
    df["Price"] = df["Price"].str.replace("₹", "").str.replace(",", "").astype(float)
    df["Rating"] = df["Rating"].fillna(df["Rating"].median())
    
    return df.dropna(subset=["Price", "Rating", "Product Title"])

def plot_price_analysis(product=None):
    df = load_data()  # Load fresh data
    try:
        # 🎯 Sidebar Filters
        # st.sidebar.header("🔍 Filters")

        # ✅ Ensure session state is initialized only once
        if "filters_initialized" not in st.session_state:
            st.sidebar.header("🔍 Filters")
            st.session_state["price_range"] = (int(df["Price"].min()), int(df["Price"].max()))
            st.session_state["source_filter"] = list(df["Source"].unique())
            st.session_state["rating_filter"] = 4.0
            st.session_state["filters_initialized"] = True  # Mark as initialized

        # 🎚 Sidebar Widgets with Stable Keys
        # Generate unique key using time() for each session

        price_range_key = f"price_slider"
        source_filter_key = f"source_multiselect"
        rating_filter_key = f"rating_slider"

        # Clear previous instance of the widget from the session state (if needed)
        if "price_range_key" in st.session_state:
            del st.session_state["price_range_key"]
        if "source_filter_key" in st.session_state:
            del st.session_state["source_filter_key"]
        if "rating_filter_key" in st.session_state:
            del st.session_state["rating_filter_key"]

        price_range = st.sidebar.slider(
            "💰 Select Price Range",
            min_value=int(df["Price"].min()),
            max_value=int(df["Price"].max()),
            value=st.session_state["price_range"],
            key=price_range_key
        )

        source_filter = st.sidebar.multiselect(
            "🏬 Select Source",
            options=df["Source"].unique(),
            default=st.session_state["source_filter"],
            key=source_filter_key
        )

        rating_filter = st.sidebar.slider(
            "⭐ Select Minimum Rating",
            0.0, 5.0,
            st.session_state["rating_filter"], 0.1,
            key=rating_filter_key
        )

        # ✅ Update session state only if changed
        if price_range != st.session_state["price_range"]:
            st.session_state["price_range"] = price_range
        if source_filter != st.session_state["source_filter"]:
            st.session_state["source_filter"] = source_filter
        if rating_filter != st.session_state["rating_filter"]:
            st.session_state["rating_filter"] = rating_filter

        # 🔍 Apply Filters to Data
        df_filtered = df[(
            df["Price"] >= st.session_state["price_range"][0]) & 
            (df["Price"] <= st.session_state["price_range"][1]) & 
            (df["Source"].isin(st.session_state["source_filter"])) & 
            (df["Rating"] >= st.session_state["rating_filter"])
        ]

        # 🏷 Main Title
        st.title("📱 "+product+" Product Dashboard")

        # 🚨 Handle case when no data matches filters
        if df_filtered.empty:
            st.warning("⚠ No products match the selected filters. Try adjusting your criteria.")
            return  # Stop execution if no data

        # # 📋 Show Filtered Product Data
        # st.subheader("📋 Filtered Product Data")
        # st.dataframe(df_filtered)

        # 📊 Price Distribution
        st.subheader("💰 Price Distribution")
        fig_price = px.scatter(
            df_filtered, 
            x="Product Title", 
            y="Price", 
            title="Price Distribution by Product Name", 
            color="Product Title",
            hover_data=["Rating","Source"],
            size_max=20  # Increases the max size of markers

        )
        fig_price.update_traces(marker=dict(size=10))  # Sets a fixed marker size
        st.plotly_chart(fig_price, use_container_width=True)

        # 📋 Show Filtered Product Data
        st.subheader("📋 Filtered Product Data")
        st.dataframe(df_filtered)

    except Exception as e:
        pass
