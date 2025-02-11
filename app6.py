import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoAlertPresentException
import pandas as pd
import re  # Import regular expressions for text extraction


# Function to set up WebDriver
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    # options.add_argument('--headless')  # Uncomment to run in background
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-notifications')  # Prevents popups
    options.add_argument('--disable-popup-blocking') # Disables all popups
    options.add_argument('--disable-infobars') # Disables Chrome's "info bars"
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

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
            ratings_count_text = "No Data"
            if i < len(ratings_count):
                full_text = ratings_count[i].text.strip()
                ratings_match = re.search(r'([\d,]+)', full_text)  # Extract numbers with commas
                if ratings_match:
                    ratings_count_text = ratings_match.group(1).replace(",", "")  # Remove commas

            
            products.append((title, price, rating, ratings_count_text))
            count += 1
            if count >= max_results:
                break
    except Exception as e:
        products.append(("Error", "Not Available", f"Error: {str(e)}", "No Data"))
    
    return products

# Function to fetch product details from Croma
def fetch_croma_products(wd, url, title_xpath, price_xpath, product_link_xpath, rating_xpath, ratings_count_xpath, max_results=5):
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
                    WebDriverWait(wd, 10).until(EC.presence_of_element_located((By.XPATH, rating_xpath)))
                    rating_text = wd.find_element(By.XPATH, rating_xpath).text.strip()

                    # Extract and clean Ratings Count
                    ratings_count_raw = wd.find_element(By.XPATH, ratings_count_xpath).text.strip()
                    ratings_count_text = ratings_count_raw.replace("(", "").split(" Ratings")[0] if "Ratings" in ratings_count_raw else "No Data"

                except TimeoutException:
                    pass

                wd.close()
                wd.switch_to.window(wd.window_handles[0])

            products.append((title, price, rating_text, ratings_count_text))
    
    except Exception as e:
        products.append(("Error", "Not Available", f"Error: {str(e)}", "No Data"))

    return products

# Function to fetch product details from Reliance Digital

from selenium.common.exceptions import TimeoutException, NoSuchElementException, UnexpectedAlertPresentException

def handle_popup(wd):
    """Handles unexpected popups dynamically"""
    try:
        # Check for browser alerts (JavaScript popups)
        WebDriverWait(wd, 2).until(EC.alert_is_present())
        alert = wd.switch_to.alert
        print("Alert found! Dismissing...")
        alert.dismiss()  # or alert.accept()
    except TimeoutException:
        pass  # No alert found, continue

    # Try closing modal popups
    possible_close_buttons = [
        "//button[contains(text(), 'Close')]", 
        "//button[contains(text(), 'No Thanks')]", 
        "//div[contains(@class, 'close')]//button"
    ]

    for xpath in possible_close_buttons:
        try:
            close_button = WebDriverWait(wd, 2).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            close_button.click()
            print(f"Popup closed using {xpath}!")
            break  # Exit loop once a popup is closed
        except (TimeoutException, NoSuchElementException):
            pass  # No popup found, continue

def fetch_reliance_products(wd, url, title_xpath, price_xpath, product_link_xpath, rating_xpath, ratings_count_xpath, max_results=5):
    products = []
    wd.get(url)

    # Wait a bit to allow all elements (including potential popups) to load
    WebDriverWait(wd, 5)

    # Handle any popups dynamically
    handle_popup(wd)

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

                # Handle popups again on the product page
                handle_popup(wd)

                try:
                    WebDriverWait(wd, 10).until(EC.presence_of_element_located((By.XPATH, rating_xpath)))
                    full_rating_text = wd.find_element(By.XPATH, rating_xpath).text.strip()
                    rating_match = re.search(r'(\d+(\.\d+)?)', full_rating_text)  # Extract decimal number like 4.7
                    rating_text = rating_match.group(1) if rating_match else "0.0"  # Default to 0.0 if not found
                    ratings_count_element = wd.find_elements(By.XPATH, ratings_count_xpath)
                    if ratings_count_element:
                        full_text = ratings_count_element[0].text.strip()
                        match = re.search(r'(\d+)', full_text)  # Extract the first number found
                        ratings_count_text = match.group(1) if match else "0"  # Default to 0 if no number is found
                except TimeoutException:
                    pass

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
        reliance_ratings_count_xpath = "//span[contains(@class, 'TextWeb__Text-sc-1cyx778-0 dzLzNm')]"

        wd = setup_driver()
        
        flipkart_data = fetch_flipkart_products(wd, flipkart_url, flipkart_title_xpath, flipkart_price_xpath, flipkart_rating_xpath, flipkart_ratings_count_xpath)
        croma_data = fetch_croma_products(wd, croma_url, croma_title_xpath, croma_price_xpath, croma_product_link_xpath, croma_rating_xpath, croma_ratings_count_xpath)
        reliance_data = fetch_reliance_products(wd, reliance_url, reliance_title_xpath, reliance_price_xpath, reliance_product_link_xpath, reliance_rating_xpath, reliance_ratings_count_xpath)

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
