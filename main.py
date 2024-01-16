from datetime import datetime
import time
from pprint import pprint
from urllib.parse import urljoin
import json
import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL: str = 'https://realtylink.org'

URL: str = 'https://realtylink.org/en/properties~for-rent?uc=2'

NUMBER_OF_LINKS: int = 60

# Set a User-Agent header to simulate a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)\
     Chrome/91.0.4472.124Safari/537.36'
}


def scrape_rental_links(url: str, max_links: int) -> dict:
    """
    The scrape_rental_links function takes an url and max_links as input.
    It then scrapes the page for links to rental ads, and returns a dictionary of {ad_number: link} pairs.
    The function will stop scraping when it has reached the maximum number of links or if there are no more pages.

    :param url: str: Specify the url of the page to be scraped
    :param max_links: int: Limit the number of links that are scraped
    :return: A dictionary with keys as 'ad_0', 'ad_2' and so on
    :doc-author: Trelent
    """
    name_link_item = {}
    unique_links = set()
    counter = 0

    try:
        driver = webdriver.Chrome()

        while True:

            driver.get(url)

            # Wait for the "Next" button to be clickable
            next_button = WebDriverWait(driver, timeout=10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'next'))
            )
            time.sleep(5)
            # If the "Next" button is inactive or if the counter has reached the limit, exit the loop
            if 'inactive' in next_button.get_attribute('class') or counter == max_links:
                print("No more pages or reached maximum links. Exiting.")
                break

            # Click on the "Next" button
            next_button.click()

            # Extract links from the current page
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            link_to_items = soup.find_all('a', class_='a-more-detail')

            for link in link_to_items:
                href_value = BASE_URL + link.get('href')
                if href_value not in unique_links:
                    name_link_item[f'ad_{counter}'] = href_value
                    unique_links.add(href_value)
                    counter += 1

                    if counter == max_links:
                        print("Reached maximum links. Exiting.")
                        return name_link_item

    except Exception as e:
        print("Error occurred:", e)
        return {}

    finally:
        print('60 ads were successfully found')
        print('Wait 40-50 seconds to write data to json')
        time.sleep(20)
        driver.quit()


def check(data: dict) -> list:
    """
    The check function takes a dictionary of links as input and returns a list of dictionaries.
    Each dictionary contains the following keys: link, title, address, region, description, img_urls (a list),\
     date (the current date), price and rooms.
    The function uses BeautifulSoup to parse the HTML content from each link in order to extract the relevant information.

    :param data: dict: Pass the dictionary of links to the check function
    :return: The list of dictionaries
    """
    result_data = []
    for key, link in data.items():
        response = requests.get(link, headers=headers)
        if response.status_code == 200:
            page_soup = BeautifulSoup(response.text, 'html.parser')

            div_tag = page_soup.find('div', {'itemprop': 'description'})
            h2_tag = page_soup.find('h2', {'itemprop': 'address', 'class': 'pt-1'})
            span_tag = page_soup.find('span', {'data-id': 'PageTitle'})
            price_div = page_soup.find('div', {'itemprop': 'offers', 'itemtype': 'http://schema.org/Offer'})
            bathrooms_div = page_soup.find('div', class_='col-lg-3 col-sm-6 sdb')
            bedrooms_div = page_soup.find('div', class_='col-lg-3 col-sm-6 cac')
            array_of_photos = page_soup.find('div', class_='thumbnail last-child first-child')
            area_div = page_soup.find('div', class_="carac-value")

            result_entry = {'link': link}

            if span_tag:
                title = span_tag.text
                result_entry['title'] = title

            if h2_tag:
                address = h2_tag.get_text(strip=True)
                result_entry['address'] = ', '.join(address.split(',')[:-1])
                result_entry['region'] = ', '.join(address.split(',')[-2:])

            if div_tag:
                description = div_tag.get_text(strip=True)
            else:
                description = 'no description'
            result_entry['description'] = description

            if array_of_photos:
                links_for_photos = array_of_photos.find('script').get_text(strip=True)
                img_urls = re.findall(r'https://[^"]+', links_for_photos)
                result_entry['img_urls'] = img_urls
            else:
                img_urls = 'no images'
            result_entry['img_urls'] = img_urls

            result_entry['date'] = datetime.now().strftime("%d.%m.%Y")

            if price_div:
                price_text = price_div.get_text(strip=True)[2:]
            else:
                price_text = 'no price'
            result_entry['price'] = price_text

            if bathrooms_div:
                bathrooms_number = bathrooms_div.get_text(strip=True)
            else:
                bathrooms_number = 'no bathrooms'

            if bedrooms_div:
                bedrooms_text = bedrooms_div.get_text(strip=True)
            else:
                bedrooms_text = 'no bedrooms'

            result_entry['rooms'] = f'Num of rooms: {bathrooms_number}, {bedrooms_text}'

            if area_div:
                area = area_div.find('span').get_text(strip=True)

            else:
                area = 'no area'
            result_entry['area'] = area

            result_data.append(result_entry)
        else:
            print(f"{key}: {link} - Failed to retrieve the content")
    return result_data


def main():
    """
    The main function is the entry point of the program.
    It scrapes rental links from a given URL and saves them to a JSON file.


    :return: A dictionary with the rental links as keys and a list of dictionaries as values
    """
    rental_links = scrape_rental_links(url=URL, max_links=NUMBER_OF_LINKS)
    with open('result_data.json', 'w') as json_file:
        json.dump(check(rental_links), json_file, indent=2)
    print("Data saved to 'result_data.json'")


if __name__ == '__main__':
    main()
