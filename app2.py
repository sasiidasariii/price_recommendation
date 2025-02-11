import requests
from bs4 import BeautifulSoup
import streamlit as st

# Replace these with your Oxylabs Web Unlocker credentials
oxylabs_username = "sasiidasariii_JLhQ7"
oxylabs_password = "Studentsasi+003"
proxy_url = f"http://{oxylabs_username}:{oxylabs_password}@unblock.oxylabs.io:60000"


# URL for Amazon and Flipkart
amazon_url = "https://www.amazon.in/s?k={}"
flipkart_url = "https://www.flipkart.com/search?q={}"

def fetch_product_data(query, platform='amazon'):
    query = query.replace(" ", "+")
    url = amazon_url.format(query) if platform == 'amazon' else flipkart_url.format(query)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }

    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }

    response = requests.get(url, headers=headers, proxies=proxies, verify=False)


    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract data (modify based on actual HTML structure)
        if platform == "amazon":
            product_titles = soup.find_all("span", {"class": "a-text-normal"})
            product_prices = soup.find_all("span", {"class": "a-price-whole"})
            product_ratings = soup.find_all("span", {"class": "a-icon-alt"})
        else:
            product_titles = soup.find_all("a", {"class": "IRpwTa"})
            product_prices = soup.find_all("div", {"class": "_30jeq3"})
            product_ratings = soup.find_all("div", {"class": "_3LWZlK"})

        product_data = []
        for title, price, rating in zip(product_titles, product_prices, product_ratings):
            product_data.append({
                "title": title.get_text(strip=True),
                "price": f"₹{price.get_text(strip=True)}",
                "rating": rating.get_text(strip=True) if rating else "No rating"
            })

        return product_data
    else:
        print(f"Error: {response.status_code}")
        return []

# Streamlit UI
st.title("🛒 Price Recommendation System using Oxylabs Web Unlocker")

search_query = st.text_input("🔍 Enter product name:")

if st.button("Search and Recommend"):
    if search_query:
        amazon_data = fetch_product_data(search_query, platform="amazon")
        flipkart_data = fetch_product_data(search_query, platform="flipkart")

        if not amazon_data and not flipkart_data:
            st.error("No matching products found. Try a different keyword.")
        else:
            st.write("### 📌 Amazon Products:")
            for product in amazon_data:
                st.write(f"**🛍️ Title:** {product['title']}")
                st.write(f"💰 **Price:** {product['price']}")
                st.write(f"⭐ **Rating:** {product['rating']}")
                st.write("-" * 50)

            st.write("### 📌 Flipkart Products:")
            for product in flipkart_data:
                st.write(f"**🛍️ Title:** {product['title']}")
                st.write(f"💰 **Price:** {product['price']}")
                st.write(f"⭐ **Rating:** {product['rating']}")
                st.write("-" * 50)
