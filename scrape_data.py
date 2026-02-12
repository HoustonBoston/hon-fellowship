#!/bin/.venv/python3

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

        # Helper function to click through pages and scrape data
        def start_scrape(soup):           
                primary_subject = soup.select('td.column-1')
                complaint_narrative = soup.select('td.column-2')
                scam_type = soup.select('td.column-3')
                website = soup.select('td.column-4')

                # # Save page source for debugging
                # with open("page_debug.html", "w") as f:
                #     f.write(soup.prettify())
                # print("Saved page source to page_debug.html for inspection")
                
                if not primary_subject:
                    print("No td.column-1 elements found. Check page_debug.html for page structure.")
                    return []
                if not complaint_narrative:
                    print("No td.column-2 elements found. Check page_debug.html for page structure.")
                    return []
                if not scam_type:
                    print("No td.column-3 elements found. Check page_debug.html for page structure.")
                    return []
                if not website:
                    print("No td.column-4 elements found. Check page_debug.html for page structure.")
                    return []

                for subject, complaint_narrative, scam, site in zip(primary_subject, complaint_narrative, scam_type, website):
                    data.append(
                        {
                            "primary_subject" : subject.get_text(strip=True),
                            "complaint_narrative" : complaint_narrative.get_text(strip=True),
                            "scam_type" : scam.get_text(strip=True),
                            "website" : site.get_text(strip=True)
                        }
                    )

                # Go to next page
                driver.find_element(By.CSS_SELECTOR, 'button.dt-paging-button.next').click()
                time.sleep(random.uniform(1, 2))  # Random sleep to mimic human behavior
                soup = BeautifulSoup(driver.page_source, 'html.parser')

        while(driver.find_element(By.CSS_SELECTOR, 'button.dt-paging-button.next')): 
            start_scrape(soup)

            if 'disabled' in driver.find_element(By.CSS_SELECTOR, 'button.dt-paging-button.next').get_attribute('class'):
                # Scrape one last time on the final page
                start_scrape(soup)
                break
        
        return data
    finally:
        driver.quit()

# Function to write data to CSV 
def write_to_csv(data):
    from pathlib import Path
    Path("data").mkdir(parents=True, exist_ok=True)
    keys = data[0].keys()

    with open('data/dfpi_crypto_scam_data.csv', 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
        
    print("Data written to data/dfpi_crypto_scam_data.csv")

if __name__ == '__main__':
    data = scrape_dfpi_data(URL)
    print(data)
    # write_to_csv(data)
