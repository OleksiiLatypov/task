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

BASE_URL = 'https://realtylink.org'

URL = 'https://realtylink.org/en/properties~for-rent?uc=2'

# Set a User-Agent header to simulate a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def scrape_rental_links(url: str, max_links: int = 60) -> dict:
    soup = None
    name_link_item = {}
    counter = 0
    driver = webdriver.Chrome()

    try:
        while True:
            driver.get(URL)
            # Stay on the page for 5 seconds (you can adjust this as needed)
            time.sleep(5)

            response = requests.get(URL, headers=headers)

            print(response.status_code)

            # If the request is successful (status code 200), proceed with parsing the HTML
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                print('success')
            else:
                print("Failed to retrieve the content. Check if the website allows scraping and adjust headers/"
                      " accordingly.")

            link_to_items = soup.find_all('a', class_='a-more-detail')

            for link in link_to_items:
                href_value = link.get('href')
                if href_value:
                    name_link_item[f'ad_{counter}'] = urljoin(BASE_URL, href_value)
                    counter += 1

            # Click on the element with class 'next'
            next_button = driver.find_element(By.CLASS_NAME, 'next')
            if 'inactive' in next_button.get_attribute('class') or counter >= max_links:
                print("No more pages or reached maximum links. Exiting.")
                break  # No more pages or reached maximum links, break out of the loop

            next_button.click()

            time.sleep(3)  # Optional: Add a delay to wait for the next page to load

        return name_link_item

    except Exception as e:
        print("Error occurred:", e)
        return {}

    finally:
        # Add a delay or user input to keep the browser window open
        if len(name_link_item) == 60:
            print('60 ads were successfully found')
            # Close the browser window
            driver.quit()


def check(data: dict) -> list:
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

            result_entry['date'] = str(datetime.now())

            if price_div:
                price_text = price_div.get_text(strip=True)[2:]
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
                result_entry['area'] = area

            result_data.append(result_entry)
        else:
            print(f"{key}: {link} - Failed to retrieve the content")
    return result_data


def main():
    rental_links = scrape_rental_links(url=URL, max_links=60)
    with open('result_data.json', 'w') as json_file:
        json.dump(check(rental_links), json_file, indent=2)
    print("Data saved to 'result_data.json'")


if __name__ == '__main__':
    main()
