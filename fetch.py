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

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



# Function to set up WebDriver
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    #options.add_argument('--headless')  # Uncomment to run in background
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
# Dictionary to store product URLs separately
flipkart_product_urls = {}

# Function to fetch product details from Flipkart
def fetch_flipkart_products(wd, url, title_xpath, price_xpath, rating_xpath, ratings_count_xpath, product_link_xpath, max_results=5):
    products = []
    wd.get(url)
    try:
        WebDriverWait(wd, 10).until(EC.presence_of_element_located((By.XPATH, title_xpath)))
        
        titles = wd.find_elements(By.XPATH, title_xpath)
        prices = wd.find_elements(By.XPATH, price_xpath)
        ratings = wd.find_elements(By.XPATH, rating_xpath)
        ratings_count = wd.find_elements(By.XPATH, ratings_count_xpath)
        product_links = wd.find_elements(By.XPATH, product_link_xpath)

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
            
            product_url = product_links[i].get_attribute("href") if i < len(product_links) else "URL Not Available"

            # Store the URL separately
            flipkart_product_urls[title] = product_url

            products.append((title, price, rating, ratings_count_text))
            count += 1
            if count >= max_results:
                break
    except Exception as e:
        products.append(("Error", "Not Available", f"Error: {str(e)}", "No Data"))
    
    return products


# Function to fetch product details from Croma without visiting product pages
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

            rating_text = "N/A"
            ratings_count_text = "N/A"

            if product_url:
                wd.execute_script("window.open('{}');".format(product_url))
                wd.switch_to.window(wd.window_handles[-1])  # Always switch to the last opened tab

                # Handle popups again on the product page
                handle_popup(wd)

                try:
                    WebDriverWait(wd, 10).until(EC.presence_of_element_located((By.XPATH, rating_xpath)))
                    full_rating_text = wd.find_element(By.XPATH, rating_xpath).text.strip()
                    rating_match = re.search(r'(\d+(\.\d+)?)', full_rating_text)
                    rating_text = rating_match.group(1) if rating_match else "N/A"

                    ratings_count_element = wd.find_elements(By.XPATH, ratings_count_xpath)
                    if ratings_count_element:
                        full_text = ratings_count_element[0].text.strip()
                        match = re.search(r'(\d+)', full_text)
                        ratings_count_text = match.group(1) if match else "N/A"
                except TimeoutException:
                    pass

                wd.close()

                # Ensure there is a main tab to switch back to
                if len(wd.window_handles) > 0:
                    wd.switch_to.window(wd.window_handles[0])

            products.append((title, price, rating_text, ratings_count_text))
    
    except Exception as e:
        products.append(("Error", "Not Available", f"Error: {str(e)}", "N/A"))

    return products

# Function to fetch reviews from a product page
def fetch_reviews(wd, url, review_xpath, max_reviews=3):
    """Fetches up to max_reviews from the given product page URL."""
    reviews = []
    wd.get(url)

    try:
        # Wait until the reviews section is loaded
        WebDriverWait(wd, 10).until(EC.presence_of_element_located((By.XPATH, review_xpath)))
        
        # Find review elements
        review_elements = wd.find_elements(By.XPATH, review_xpath)

        # Extract text from the first 'max_reviews' reviews
        for review in review_elements[:max_reviews]:  
            reviews.append(review.text.strip())

    except Exception as e:
        reviews.append(f"Error: {str(e)}")

    return reviews


