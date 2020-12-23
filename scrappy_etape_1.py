# Etape 1 : scrapper une page produit

# récupérer :
# product_page_url OK
# universal_ product_code (upc) Ok
# title
# price_including_tax OK
# price_excluding_tax OK
# number_available OK
# product_description
# category
# review_rating
# image_url

# Insérer les nouvelles données dans un CSV

import requests
from bs4 import BeautifulSoup


class Product:
    def __init__(self, **product_informations):
        for information_name, information_value in product_informations.items():
            setattr(self, information_name, information_value)


product_informations = {"product_page_url": "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html", "universal_product_code": 0, "title": "", "price_including_tax": "£0",
                        "price_excluding_tax": "£0", "number_available": 0, "product_description": "", "category": "", "review_rating": 0, "image_url": ""}

response = requests.get(product_informations["product_page_url"])

if response.ok:
    soup = BeautifulSoup(response.text, 'html.parser')

    # Récupérer universal_product_code / price_excluding_taxe / price_including_tax / number_available (tableau d'information en bas de page produit)
    informations = soup.findAll("tr")

    for information in informations:
        information_label = information.find('th').text
        information_value = information.find('td').text

        target_dict = ""

        if (information_label == "UPC"):
            target_dict = "universal_product_code"
        if (information_label == "Price (excl. tax)"):
            target_dict = "price_excluding_tax"
        if (information_label == "Price (incl. tax)"):
            target_dict = "price_including_tax"
        if (information_label == "Availability"):
            target_dict = "number_available"

        if "Â" in information_value:
            information_value = information_value.replace("Â", "")

        product_informations[target_dict] = information_value

    # Récupérer image_url (id product_gallery)
    product_gallery = soup.find("div", {"id": "product_gallery"})
    product_informations["image_url"] = "http://books.toscrape.com/" + \
        product_gallery.find('img')["src"]

    # Récupérer category (breadcrumbs : dernier li avant class active)
    breadcrumb = soup.find('ul', {"class": "breadcrumb"})
    links = soup.select('li:not(.active)')
    product_informations["category"] = links[len(links) - 1].text

    # Récupérer title (titre H1)
    product_informations['title'] = soup.find('h1').text

    # Récupérer description (id product_description + selecteur css frère tag p)
    # Récupérer review_rating (class star-rating + class indiquant le nombre d'étoile)

# print(product_informations)
