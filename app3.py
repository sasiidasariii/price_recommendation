import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Function to fetch product price
def fetch_price(url, site_name, xpath):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--headless')  # Runs in background without opening browser
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    wd = webdriver.Chrome(service=service, options=options)
    
    try:
        st.write(f"Fetching price from {site_name}...")
        wd.get(url)
        WebDriverWait(wd, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        price = wd.find_element(By.XPATH, xpath).text
        st.success(f"Price retrieved successfully from {site_name}: {price}")
        return price
    except Exception as e:
        st.error(f"Failed to retrieve price from {site_name}: {e}")
        return "N/A"
    finally:
        wd.quit()

# Streamlit UI
st.title("Product Price Comparison")

st.write("Enter product page URLs for Flipkart, Reliance Digital, and Croma to compare prices.")

# User input fields for URLs
flipkart_url = st.text_input("Enter Flipkart URL:", "")
reliance_url = st.text_input("Enter Reliance Digital URL:", "")
croma_url = st.text_input("Enter Croma URL:", "")

# XPaths for extracting price (These may need adjustments based on site structure)
flipkart_xpath = "//div[@id='container']//div[contains(text(), '₹')]"
reliance_xpath = "//*[@id='root']/main/div[2]/div/section[1]/div[2]/div[2]/div[2]/div[1]/ul/li[1]"
croma_xpath = "//span[contains(@class, 'amount')]"

# Button to trigger price fetching
if st.button("Fetch Prices"):
    if flipkart_url:
        flipkart_price = fetch_price(flipkart_url, "Flipkart", flipkart_xpath)
    else:
        flipkart_price = "N/A"

    if reliance_url:
        reliance_price = fetch_price(reliance_url, "Reliance Digital", reliance_xpath)
    else:
        reliance_price = "N/A"

    if croma_url:
        croma_price = fetch_price(croma_url, "Croma", croma_xpath)
    else:
        croma_price = "N/A"

    # Display results
    st.subheader("Price Comparison Results")
    st.write(f"**Flipkart Price:** {flipkart_price}")
    st.write(f"**Reliance Digital Price:** {reliance_price}")
    st.write(f"**Croma Price:** {croma_price}")
