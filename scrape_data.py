# Copyright Roshan Karthik Rajesh 2026
# Script to scrape data from DFPI website

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import csv
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC

URL = "https://dfpi.ca.gov/consumers/crypto/crypto-scam-tracker/"

def scrape_dfpi_data(url):

    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    
    driver = uc.Chrome(version_main=144, headless=False, use_subprocess=True)
    
    try:
        driver.get(url)
        # Wait for page to fully load and pass Cloudflare
        time.sleep(5)

        # Wait up to 10s for the table cells to appear
        try:
            print("Waiting for data to load...")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "td.column-1"))
            )
        except Exception:
            # Still save debug page and exit gracefully
            with open("page_debug.html", "w") as f:
                soup_debug = BeautifulSoup(driver.page_source, 'html.parser')
                f.write(soup_debug.prettify())
            print("Timed out waiting for data. Saved page source to page_debug.html for inspection")
            return []

        # Select dropdown to show 100 entries 
        select_element = driver.find_element(By.CLASS_NAME, 'dt-input')
        select = Select(select_element)
        select.select_by_value('100')
        time.sleep(random.uniform(1, 2))  # Random sleep to mimic human behavior

        # Initial load
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        data = []

        while(driver.find_element(By.CSS_SELECTOR, 'button.dt-paging-button.next')):            
            primary_subject = soup.select('td.column-1')

            # # Save page source for debugging
            # with open("page_debug.html", "w") as f:
            #     f.write(soup.prettify())
            # print("Saved page source to page_debug.html for inspection")
            
            if not primary_subject:
                print("No td.column-1 elements found. Check page_debug.html for page structure.")
                return []

            print("Primary Subjects:")
            for subject in primary_subject:
                print(subject.get_text(strip=True))
                data.append(subject.get_text(strip=True))

            # Go to next page
            driver.find_element(By.CSS_SELECTOR, 'button.dt-paging-button.next').click()
            time.sleep(random.uniform(1, 2))  # Random sleep to mimic human behavior
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            if 'disabled' in driver.find_element(By.CSS_SELECTOR, 'button.dt-paging-button.next').get_attribute('class'):
                break
        
        return data
    finally:
        driver.quit()

if __name__ == '__main__':
    scrape_dfpi_data(URL)
