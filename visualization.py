import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

def display_price_histogram(df, product):
    # Convert price column to numerical values
    df['Price'] = df['Price'].replace({'₹': '', ',': ''}, regex=True).astype(float)

    # Determine dynamic bin size based on price range
    price_range = df['Price'].max() - df['Price'].min()
    bin_size = max(5000, price_range // 10)  # At least 5000, but adjusts based on range
    bins = np.arange(min(df['Price']), max(df['Price']) + bin_size, bin_size)
    df['Price Range'] = pd.cut(df['Price'], bins, right=False).astype(str)

    # Group products by price range and source
    grouped = df.groupby(['Price Range', 'Source']).agg(
        Count=('Price', 'count'),
        Sample_Product=('Product Title', 'first'),  # Select first product in each bin and source
        All_Products=('Product Title', lambda x: '<br>'.join(x))  # All products in bin and source
    ).reset_index()

    # Generate colors for sources
    unique_sources = grouped['Source'].unique()
    colors = px.colors.qualitative.Set3[:len(unique_sources)]
    color_map = {source: colors[i] for i, source in enumerate(unique_sources)}

    # Create interactive histogram
    fig = px.bar(
        grouped, 
        x='Price Range', 
        y='Count', 
        color='Source', 
        text='Count',
        labels={'Price Range': 'Price (₹)', 'Count': 'Frequency', 'Source': 'Retailer'},
        title='Histogram of ' + product ,
        hover_data={'Sample_Product': True, 'All_Products': True},
        color_discrete_map=color_map
    )

    # Streamlit integration
    st.header("📊 Price Distribution of " + product )
    st.plotly_chart(fig, use_container_width=True)

    # Show details of products in selected bin
    selected_bin = st.selectbox("Select a Price Range to view all products", grouped['Price Range'].unique())
    selected_group = grouped[grouped['Price Range'] == selected_bin]

    st.markdown(f"### Products in {selected_bin}")
    for source in selected_group['Source'].unique():
        st.markdown(f"#### Source: {source}")
        source_products = selected_group[selected_group['Source'] == source]['All_Products'].values[0]
        st.markdown(source_products.replace('<br>', '\n'))


# 🛑 Load Data with Dynamic Refresh
@st.cache_data(ttl=60)  # Refresh data every 60 seconds
def load_data():
    df = pd.read_csv("product_data.csv")
    df["Rating"] = df["Rating (⭐ out of 5)"].copy()
    df = df.drop(columns=["Rating (⭐ out of 5)"])
    df["Rating"] = pd.to_numeric(df["Rating"], errors='coerce')
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
        df_filtered["Product Title"] = df_filtered["Product Title"].apply(lambda x: x[:32] + "..." if len(x) > 10 else x)
        
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

        display_price_histogram(df_filtered, product)
        
        #st.markdown("Developed with ❤ using Streamlit and Plotly")
    except Exception as e:
        pass