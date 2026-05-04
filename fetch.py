import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import re
import time
from wordcloud import WordCloud
import matplotlib.pyplot as plt


# -----------------------------
# Setup WebDriver
# -----------------------------
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    # options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-infobars')

    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


# -----------------------------
# POPUP HANDLERS
# -----------------------------

def wait_for_flipkart_popup_to_close(wd):
    """Wait until Flipkart login popup disappears automatically"""

    try:
        WebDriverWait(wd, 8).until(
            EC.invisibility_of_element_located(
                (By.XPATH, "//div[contains(text(),'Login')]")
            )
        )
        print("Flipkart popup disappeared")

    except TimeoutException:
        print("Flipkart popup not detected")


def close_reliance_location_popup(wd):
    """Close Reliance Allow Access popup"""

    try:
        close_btn = WebDriverWait(wd, 6).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@aria-label='Close Modal']")
            )
        )

        # JS click because SVG button sometimes not clickable normally
        wd.execute_script("arguments[0].click();", close_btn)

        print("Reliance location popup closed")

    except TimeoutException:
        print("Reliance popup not found")


def handle_popup(wd):
    """Generic popup handler"""

    possible_close_buttons = [
        "//button[contains(text(),'Close')]",
        "//button[contains(text(),'No Thanks')]",
        "//button[contains(@class,'close')]",
        "//span[contains(@class,'close')]"
    ]

    for xpath in possible_close_buttons:
        try:
            btn = WebDriverWait(wd, 2).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            btn.click()
            break
        except:
            pass


# -----------------------------
# FLIPKART SCRAPER
# -----------------------------

flipkart_product_urls = {}

def fetch_flipkart_products(wd, url, title_xpath, price_xpath, rating_xpath,
                           ratings_count_xpath, product_link_xpath, max_results=5):

    products = []

    wd.get(url)

    # wait for login popup to disappear
    wait_for_flipkart_popup_to_close(wd)

    try:

        WebDriverWait(wd, 10).until(
            EC.presence_of_element_located((By.XPATH, title_xpath))
        )

        titles = wd.find_elements(By.XPATH, title_xpath)
        prices = wd.find_elements(By.XPATH, price_xpath)
        ratings = wd.find_elements(By.XPATH, rating_xpath)
        ratings_count = wd.find_elements(By.XPATH, ratings_count_xpath)
        product_links = wd.find_elements(By.XPATH, product_link_xpath)

        count = 0

        for i in range(len(titles)):

            if "Sponsored" in titles[i].text:
                continue

            title = titles[i].text.strip() if titles[i].text else "N/A"
            price = prices[i].text.strip() if i < len(prices) else "Price not listed"
            rating = ratings[i].text.strip() if i < len(ratings) else "No Rating"

            ratings_count_text = "No Data"

            if i < len(ratings_count):
                full_text = ratings_count[i].text.strip()

                ratings_match = re.search(r'([\d,]+)', full_text)

                if ratings_match:
                    ratings_count_text = ratings_match.group(1).replace(",", "")

            product_url = product_links[i].get_attribute("href") if i < len(product_links) else ""

            flipkart_product_urls[title] = product_url

            products.append((title, price, rating, ratings_count_text))

            count += 1

            if count >= max_results:
                break

    except Exception as e:

        products.append(("Error", "Not Available", f"Error: {str(e)}", "No Data"))

    return products


# -----------------------------
# CROMA SCRAPER
# -----------------------------

def fetch_croma_products(wd, url, title_xpath, price_xpath,
                         product_link_xpath, rating_xpath,
                         ratings_count_xpath, max_results=5):

    products = []

    wd.get(url)

    try:

        WebDriverWait(wd, 10).until(
            EC.presence_of_element_located((By.XPATH, title_xpath))
        )

        titles = wd.find_elements(By.XPATH, title_xpath)
        prices = wd.find_elements(By.XPATH, price_xpath)
        product_links = wd.find_elements(By.XPATH, product_link_xpath)

        for i in range(min(len(titles), max_results)):

            title = titles[i].text.strip() if titles[i].text else "N/A"
            price = prices[i].text.strip() if i < len(prices) else "Price not listed"
            product_url = product_links[i].get_attribute("href")

            rating_text = "No Rating"
            ratings_count_text = "No Data"

            if product_url:

                wd.execute_script("window.open('{}');".format(product_url))
                wd.switch_to.window(wd.window_handles[1])

                try:

                    WebDriverWait(wd, 10).until(
                        EC.presence_of_element_located((By.XPATH, rating_xpath))
                    )

                    rating_text = wd.find_element(By.XPATH, rating_xpath).text.strip()

                    ratings_count_raw = wd.find_element(By.XPATH, ratings_count_xpath).text.strip()

                    ratings_count_text = ratings_count_raw.replace("(", "").split(" Ratings")[0]

                except TimeoutException:
                    pass

                wd.close()

                wd.switch_to.window(wd.window_handles[0])

            products.append((title, price, rating_text, ratings_count_text))

    except Exception as e:

        products.append(("Error", "Not Available", f"Error: {str(e)}", "No Data"))

    return products


# -----------------------------
# RELIANCE SCRAPER
# -----------------------------

def fetch_reliance_products(wd, url, title_xpath, price_xpath,
                            product_link_xpath, rating_xpath,
                            ratings_count_xpath, max_results=5):

    products = []

    wd.get(url)

    time.sleep(2)
    close_reliance_location_popup(wd)
    handle_popup(wd)

    try:

        WebDriverWait(wd, 10).until(
            EC.presence_of_element_located((By.XPATH, title_xpath))
        )

        titles = wd.find_elements(By.XPATH, title_xpath)
        prices = wd.find_elements(By.XPATH, price_xpath)
        product_links = wd.find_elements(By.XPATH, product_link_xpath)

        for i in range(min(len(titles), max_results)):

            title = titles[i].text.strip() if titles[i].text else "N/A"
            price = prices[i].text.strip() if i < len(prices) else "Price not listed"

            product_url = product_links[i].get_attribute("href")

            rating_text = "N/A"
            ratings_count_text = "N/A"

            if product_url:

                wd.execute_script("window.open('{}');".format(product_url))
                wd.switch_to.window(wd.window_handles[-1])

                close_reliance_location_popup(wd)

                try:

                    WebDriverWait(wd, 10).until(
                        EC.presence_of_element_located((By.XPATH, rating_xpath))
                    )

                    full_rating_text = wd.find_element(By.XPATH, rating_xpath).text

                    rating_match = re.search(r'(\d+(\.\d+)?)', full_rating_text)

                    rating_text = rating_match.group(1) if rating_match else "N/A"

                    ratings_count_element = wd.find_elements(By.XPATH, ratings_count_xpath)

                    if ratings_count_element:

                        full_text = ratings_count_element[0].text

                        match = re.search(r'(\d+)', full_text)

                        ratings_count_text = match.group(1) if match else "N/A"

                except TimeoutException:
                    pass

                wd.close()

                wd.switch_to.window(wd.window_handles[0])

            products.append((title, price, rating_text, ratings_count_text))

    except Exception as e:

        products.append(("Error", "Not Available", f"Error: {str(e)}", "N/A"))

    return products


# -----------------------------
# FETCH REVIEWS
# -----------------------------

def fetch_reviews(wd, product_url, max_reviews=40):

    reviews = []

    # Open all reviews page
    review_url = product_url.replace("/p/", "/product-reviews/")
    wd.get(review_url)

    time.sleep(3)

    # Scroll to load more reviews
    for _ in range(5):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)

    review_elements = wd.find_elements(By.XPATH, "//span[contains(@class,'css-1qaijid')]")

    for review in review_elements[:max_reviews]:
        text = review.text.strip()
        if text:
            reviews.append(text)

    return reviews