import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

# Function to set up WebDriver
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    # options.add_argument('--headless')  # Uncomment to run in background
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--start-maximized')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_stable_element_text(driver, xpath, retries=2, wait_time=1):
    """Tries to get text from an element while handling stale element errors efficiently."""
    for attempt in range(retries):
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            if elements:
                return elements[0].text.strip() if elements[0].text else "No Rating"
            return "No Rating"  # No element found
        except StaleElementReferenceException:
            time.sleep(wait_time)  # Wait and retry
    return "No Rating"




# Function to fetch product details from Flipkart
def fetch_flipkart_products(wd, url, title_xpath, price_xpath, rating_xpath, ratings_count_xpath, max_results=5):
    products = []
    wd.get(url)
    try:
        WebDriverWait(wd, 10).until(EC.presence_of_element_located((By.XPATH, title_xpath)))
        
        titles = wd.find_elements(By.XPATH, title_xpath)
        prices = wd.find_elements(By.XPATH, price_xpath)
        ratings = wd.find_elements(By.XPATH, rating_xpath)
        ratings_count = wd.find_elements(By.XPATH, ratings_count_xpath)
        
        count = 0
        for i in range(len(titles)):
            if "Sponsored" in titles[i].text:
                continue  # Skip sponsored products
            
            title = titles[i].text.strip() if titles[i].text else "N/A"
            price = prices[i].text.strip() if i < len(prices) else "Price not listed"
            rating = ratings[i].text.strip() if i < len(ratings) else "No Rating"
            ratings_count_text = ratings_count[i].text.strip() if i < len(ratings_count) else "No Data"
            
            products.append((title, price, rating, ratings_count_text))
            count += 1
            if count >= max_results:
                break
    except Exception as e:
        products.append(("Error", "Not Available", f"Error: {str(e)}", "No Data"))
    
    return products

def fetch_croma_reliance_products(wd, url, title_xpath, price_xpath, product_link_xpath, rating_xpath, ratings_count_xpath, max_results=5):
    products = []
    wd.get(url)

    try:
        WebDriverWait(wd, 10).until(EC.presence_of_element_located((By.XPATH, title_xpath)))
        
        titles = wd.find_elements(By.XPATH, title_xpath)
        prices = wd.find_elements(By.XPATH, price_xpath)
        product_links = wd.find_elements(By.XPATH, product_link_xpath)

        for i in range(min(len(titles), max_results)):
            title = titles[i].text.strip() if titles[i].text else "N/A"
            price = prices[i].text.strip() if i < len(prices) else "Price not listed"
            product_url = product_links[i].get_attribute("href") if i < len(product_links) else ""

            rating_text = "No Rating"
            ratings_count_text = "No Data"

            if product_url:
                wd.execute_script("window.open('{}');".format(product_url))
                wd.switch_to.window(wd.window_handles[1])

                try:
                    # Extract Rating
                    WebDriverWait(wd, 10).until(EC.presence_of_element_located((By.XPATH, rating_xpath)))
                    rating_element = wd.find_element(By.XPATH, rating_xpath)
                    rating_text = rating_element.text.strip() if rating_element.text else "No Rating"

                    # Extract Ratings Count & Clean Formatting
                    ratings_count_element = wd.find_element(By.XPATH, ratings_count_xpath)
                    ratings_count_raw = ratings_count_element.text.strip() if ratings_count_element.text else "No Data"

                    # Remove "(" and extract only numeric ratings count
                    ratings_count_split = ratings_count_raw.replace("(", "").split(" Ratings")[0] if "Ratings" in ratings_count_raw else "No Data"

                    ratings_count_text = ratings_count_split.strip()

                except TimeoutException:
                    rating_text = "Rating not available"
                    ratings_count_text = "No Data"

                wd.close()
                wd.switch_to.window(wd.window_handles[0])

            products.append((title, price, rating_text, ratings_count_text))
    
    except Exception as e:
        products.append(("Error", "Not Available", f"Error: {str(e)}", "No Data"))

    return products


# Streamlit UI
st.title("📌 Product Price & Rating Comparison")

# User input
product_name = st.text_input("🔍 Enter Product Name:", "")

if st.button("Find Prices"):
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
        reliance_ratings_count_xpath = "/html/body/div[1]/main/div[3]/div/div[4]/div/div[1]/div/div[2]/div/div[1]/span[2]"

        wd = setup_driver()
        
        flipkart_data = fetch_flipkart_products(wd, flipkart_url, flipkart_title_xpath, flipkart_price_xpath, flipkart_rating_xpath, flipkart_ratings_count_xpath)
        croma_data = fetch_croma_reliance_products(wd, croma_url, croma_title_xpath, croma_price_xpath, croma_product_link_xpath, croma_rating_xpath, croma_ratings_count_xpath)
        reliance_data = fetch_croma_reliance_products(wd, reliance_url, reliance_title_xpath, reliance_price_xpath, reliance_product_link_xpath, reliance_rating_xpath, reliance_ratings_count_xpath)

        wd.quit()

        # Display results
        st.subheader("🛒 Flipkart")
        df_flipkart = pd.DataFrame(flipkart_data, columns=["Product Title", "Price", "Rating (⭐ out of 5)", "No. of Ratings"])
        st.table(df_flipkart)

        st.subheader("🛒 Reliance Digital")
        df_reliance = pd.DataFrame(reliance_data, columns=["Product Title", "Price", "Rating (⭐ out of 5)", "No. of Ratings"])
        st.table(df_reliance)

        st.subheader("🛒 Croma")
        df_croma = pd.DataFrame(croma_data, columns=["Product Title", "Price", "Rating (⭐ out of 5)", "No. of Ratings"])
        st.table(df_croma)
    else:
        st.warning("⚠️ Please enter a product name.")
