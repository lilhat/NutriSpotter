import re

import requests
from bs4 import BeautifulSoup
import pandas as pd
import concurrent.futures


# Initialize variables
NUM_RETRIES = 5
NUM_THREADS = 50
products = []
urls = []

# Scrape categories
def get_categories():
    # Loop for number of retries
    for _ in range(NUM_RETRIES):
        # Make GET request to ScrapingBee API
        response = requests.get(
            url='https://api.scrapingdog.com/scrape',
            params={
                'api_key': '64878f84d0570f4a16b3fd95',
                'url': 'https://www.bulk.com/uk',
                'dynamic': 'false',
            },

        )
        # Check response success
        if response.status_code == 200:
            # Parse the content with BeautifulSoup
            body = response.content
            soup = BeautifulSoup(body, 'html.parser')
            # Target specific li elements
            product_elements = soup.find_all('a', {'class': 'navigation__inner-link'})
            links = []
            # Extract href of hyperlink elements within each li
            for product_element in product_elements:
                links.append(product_element['href'])
            # Filter to only contain department links
            department_links = [link for link in links if '/' in link]
            print(department_links)
            # Append to global urls list
            for j in range(0, len(department_links)):
                urls.append(department_links[j])
            # Break out of retry loop if successful
            print(urls)
            break
        else:
            print("Error: " + str(response.status_code))


# Send request for HTML content of provided URL
def send_request(url):
    # Loop for number of retries
    for _ in range(NUM_RETRIES):
        # Make GET request to ScrapingBee API
        response = requests.get(
            url='https://api.scrapingdog.com/scrape',
            params={
                'api_key': '64878f84d0570f4a16b3fd95',
                'url': url,
                'dynamic': 'false',
            },

        )
        # Check response success
        if response.status_code == 200:
            # Call function to extract data using response content
            scrape_url(response.content)
            break
        else:
            print("Error: " + str(response.status_code))
            print("Url: " + url)


# Send request for HTML content of provided URL
def single_request(url):
    # Loop for number of retries
    for _ in range(NUM_RETRIES):
        # Make GET request to ScrapingBee API
        response = requests.get(
            url='https://api.scrapingdog.com/scrape',
            params={
                'api_key': '64878f84d0570f4a16b3fd95',
                'url': url,
                'dynamic': 'false',
            },

        )
        # Check response success
        if response.status_code == 200:
            # Call function to extract description and image using response content
            description = scrape_desc(response.content)
            return description
        else:
            print("Error: " + str(response.status_code))
            print("Url: " + url)


# Extract relevant data from response content
def scrape_url(body):
    try:
        # Parse content with BeautifulSoup
        soup = BeautifulSoup(body, 'html.parser')
        # Find each product component in the content
        product_titles = soup.find_all('a', {'class': 'product-item-link'})
        product_prices = soup.find_all('span', {'class': 'price'})
        category_title_element = soup.find('h1', {'class': 'page-title'})
        product_images = soup.find_all('img', {'class': 'product-image-photo'})
        # Check if category title exists
        category_title = "N/A"
        if category_title_element is not None:
            category_title = category_title_element.text.strip()

        product_list = []
        price_list = []
        link_list = []
        image_list = []
        desc_list = []

        # Extract text of each product title and append into list
        for product_title in product_titles:
            link = product_title['href']
            link_list.append(link)
            # Call function to scrape deeper product page level
            desc = single_request(link)
            # Append returned description and image into lists
            desc_list.append(desc)
            title_element = re.sub('^[\s]+|[\s]+$', '', product_title.text.strip())
            if title_element:
                product_list.append(title_element)

        # Extract text of each product price and append into list
        for product_price in product_prices:
            text = ""
            text += product_price.get_text(strip=True)
            if text.strip() == "":
                text = "N/A"
            else:
                price_list.append(text)

        for product_image in product_images:
            image = product_image['src']
            image_list.append(image)


        # Zip all lists together to create a list of dictionaries containing the information for a single product
        # Print each dictionary and add it to the products list
        for product, price, link, image, description in zip(product_list, price_list, link_list, image_list, desc_list):
            print({'Name': product, 'Price': price, 'Category': category_title, 'Link': link, 'Image': image, 'Description': description})
            products.append({'Name': product, 'Price': price, 'Category': category_title, 'Link': link, 'Image': image, 'Description': description})

    except KeyError:
        print("Key Error occurred")
    except:
        print("Error occurred")


# Extract description and image from product level response content
def scrape_desc(body):
    try:
        # Parse content with BeautifulSoup
        soup = BeautifulSoup(body, 'html.parser')
        # Target product description and image in the content
        product_desc = soup.find('div', {'id': 'description'})


        # Extract description text if exists
        if product_desc:
            description = re.sub('^[\s]+|[\s]+$', ' ', product_desc.text)
            description = description.replace('\n', ' ').replace('\xa0', ' ').replace('1\xa0', ' ').replace('\r', '')
        else:
            description = "N/A"


        # Return description and image
        return description

    except KeyError:
        print("Key Error occurred")
    except:
        print("Error occurred")


# Call initial function to scrape categories
get_categories()

# Use categories inside urls list to concurrently send up to 50 requests at a time
with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
    executor.map(send_request, urls)


# Write products into csv file
df = pd.DataFrame(products)
df.to_csv('bulkProducts.csv', index=False)
