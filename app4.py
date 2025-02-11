import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Function to set up WebDriver
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--start-maximized')
   # options.add_argument('--headless')  # Uncomment to run in background
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# Function to fetch price from a website
def fetch_price(url, site_name, xpath):
    wd = setup_driver()
    try:
        wd.get(url)
        WebDriverWait(wd, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        price = wd.find_element(By.XPATH, xpath).text
        wd.quit()
        return price
    except Exception as e:
        wd.quit()
        return f"Not Available ({str(e)})"

# Streamlit UI
st.title("📌 Product Price Comparison")

# User input
product_name = st.text_input("🔍 Enter Product Name:", "")

if st.button("Find Prices"):
    if product_name.strip():
        st.write("🔗 Searching for product...")

        # Manually set product URLs (Replace with a search function if needed)
        flipkart_url = f"https://www.flipkart.com/search?q={product_name.replace(' ', '+')}"
        reliance_url = f"https://www.reliancedigital.in/search?q={product_name.replace(' ', '%20')}"
        croma_url = f"https://www.croma.com/search?q={product_name.replace(' ', '%20')}"

        # XPaths for extracting price
        flipkart_xpath = "(//div[contains(@class, 'Nx9bqj')])[1]"
        reliance_xpath = "//span[contains(@class, 'TextWeb__Text-sc-1cyx778-0')]/span[2]"
        croma_xpath = "//span[contains(@class, 'amount')]"

        # Fetch prices
        flipkart_price = fetch_price(flipkart_url, "Flipkart", flipkart_xpath)
        reliance_price = fetch_price(reliance_url, "Reliance Digital", reliance_xpath)
        croma_price = fetch_price(croma_url, "Croma", croma_xpath)

        # Display results
        st.write("💰 **Price Comparison Results**")
        st.write(f"**Flipkart Price:** {flipkart_price}")
        st.write(f"**Reliance Digital Price:** {reliance_price}")
        st.write(f"**Croma Price:** {croma_price}")
    else:
        st.warning("⚠️ Please enter a product name.")

