# Etape 3 : scrapper le site Books To Scrape

# récupérer toutes les catégories
# créer un dossier et ensuite un fichier csv distinct pour chaque catégorie
# consulter la page de chaque catégorie
# extrait l'url de chaque produit
# extrais les informations produits (étape 1)
# Insérer les nouvelles données dans un CSV

import os
import stat
import random
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import shutil
import csv
import time
from slugify import slugify
import urllib.request

# random sleep mode
MIN_SLEEP = 0.1
MAX_SLEEP = 2

# remove scrappy_etape_4 before restart
shutil.rmtree('./scrappy_etape_4', ignore_errors=True)


def progressBar(iterable, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)
    # Progress Bar Printing Function

    def printProgressBar(iteration):
        percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                         (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()


def scrappy_products_category(soup):
    links = []

    products = soup.select('article.product_pod')

    for product in products:
        href = product.find('a')["href"]
        href = href.split('/')
        links.append("http://books.toscrape.com/catalogue/" +
                     href[-2] + "/" + href[-1])

    return links


def find_products_url_by_category(url_categ):
    # produit par page : 20
    response = requests.get(url_categ)
    links = []

    if response.ok:
        soup = BeautifulSoup(response.text, 'html.parser')

        is_pagination = soup.find("ul", {"class": "pager"})

        if is_pagination:
            nbPages = is_pagination.find(
                'li', {"class": "current"}).text.strip()
            nbPages = int(nbPages[-1:])

            if nbPages:
                for i in range(1, nbPages + 1):
                    url = url_categ.replace(
                        'index.html', 'page-' + str(i) + '.html')

                    response = requests.get(url)

                    if (response.ok):
                        soup = BeautifulSoup(response.text, 'html.parser')

                        links += scrappy_products_category(soup)

                    # Eviter l'IP blacklistée
                    time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        else:
            links = scrappy_products_category(soup)

    return links


def scrappy_product(url, upload_image, slug_categ):
    product_informations = {
        "product_page_url": url}

    response = requests.get(product_informations["product_page_url"])

    if response.ok:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Récupérer universal_product_code / price_excluding_taxe / price_including_tax (tableau d'information en bas de page produit)
        informations = soup.findAll("tr")

        for information in informations:
            information_label = information.find('th').text
            information_value = information.find('td').text

            target_dict = False

            if (information_label == "UPC"):
                target_dict = "universal_product_code"
            elif (information_label == "Price (excl. tax)"):
                target_dict = "price_excluding_tax"
            elif (information_label == "Price (incl. tax)"):
                target_dict = "price_including_tax"

            if target_dict:
                if "Â" in information_value:
                    information_value = information_value.replace("Â", "")

                product_informations[target_dict] = information_value

        # Récupérer image_url (id product_gallery)
        product_gallery = soup.find("div", {"id": "product_gallery"})
        product_informations["image_url"] = "http://books.toscrape.com/" + \
            product_gallery.find('img')["src"].replace('../../', '')

        # Récupérer category (breadcrumbs : dernier li avant class active)
        breadcrumb = soup.find('ul', {"class": "breadcrumb"})
        links = breadcrumb.select('li:not(.active)')
        product_informations["category"] = links[len(links) - 1].text.strip()

        # Récupérer title (titre H1)
        product_informations['title'] = soup.find('h1').text

        # Récupérer description (id product_description + selecteur css frère tag p)
        description = soup.find('div', {"id": 'product_description'})

        if description:
            product_informations["product_description"] = description.findNext(
                'p').text

        # Récupérer review_rating (class star-rating + class indiquant le nombre d'étoile)
        review_rating = soup.find('p', {"class": "star-rating"})
        if review_rating.has_attr('class'):
            review_rating = review_rating["class"][1]

            if review_rating == "One":
                review_rating = 1
            elif review_rating == "Two":
                review_rating = 2
            elif review_rating == "Three":
                review_rating = 3
            elif review_rating == "Four":
                review_rating = 4
            elif review_rating == "Five":
                review_rating = 5
            else:
                review_rating = 0
        else:
            review_rating = 0

        product_informations['review_rating'] = review_rating

        # Récupérer number_available (instock outofstock en dessous du prix du produit)
        availability = soup.select('p.availability.instock')

        if availability:
            availability = availability[0].text
            availability = availability.replace('In stock (', '')
            availability = availability.replace(' available)', '')
            availability = int(availability)

            product_informations["number_available"] = availability
        else:
            product_informations["number_available"] = 0

        # upload image product inside images directory
        if upload_image and slug_categ:
            title = slugify(product_informations["title"])
            image_url = product_informations["image_url"]
            image_ext = product_informations["image_url"].split(
                '.')[-1]

            urllib.request.urlretrieve(
                image_url, './scrappy_etape_4/' + slug_categ + '/images/' + title + '.' + image_ext)

    return product_informations


categories = []
response = requests.get('http://books.toscrape.com/')

if (response.ok):
    soup = BeautifulSoup(response.text, 'html.parser')

    # Récupérer toutes les catégories de livres
    for categorie in soup.select('.side_categories ul > li > ul > li > a'):
        categories.append(
            {"name": categorie.text.strip(), "url": "http://books.toscrape.com/" + categorie["href"]})

    # Create scrappy_etape_4 if not exist
    Path('./scrappy_etape_4').mkdir(parents=True, exist_ok=True)

    # Consulter la page de chaque catégorie
    for categorie in progressBar(categories, prefix='Scrapping Books...:', suffix='', length=50):
        name = slugify(categorie["name"])

        # create category folder
        Path('./scrappy_etape_4/' + name).mkdir(parents=True, exist_ok=True)

        # create images folder inside category
        Path('./scrappy_etape_4/' + name +
             '/images').mkdir(parents=True, exist_ok=True)

        print("Catégorie : " + categorie["name"])
        links = find_products_url_by_category(categorie["url"])

        # if links:
        products_informations = []
        i = 1

        for url in links:
            products_informations.append(scrappy_product(url, True, name))

            # Eviter l'IP blacklistée
            time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))

            print(str(i) + " produits scrappés sur " +
                  str(len(links)) + " produits")
            i += 1

        # Ecriture fichier csv
        if products_informations:
            with open('./scrappy_etape_4/' + name + '/' + name + '.csv', 'w') as file:
                writer = csv.writer(file)

                # En têtes
                writer.writerow(products_informations[0].keys())

                # Values
                for product_informations in products_informations:
                    writer.writerow(product_informations.values())
