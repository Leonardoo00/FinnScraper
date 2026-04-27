# TODO
# - Notify for any request fail with status code
# - Add some soup error handling
# - Add User-Agent or any other headers attribute 
# - Error handilign for the webhook notification
# - Add notify for ERROR via webhook
# - Currently only one image of the two available per ad are used

import requests
from bs4 import BeautifulSoup as bs
from pathlib import Path
import json 
import time
from dotenv import load_dotenv
import os 

# Load .env file. See README.md for further information
load_dotenv()


URL             = os.getenv("URL")
WEBHOOK_URL     = os.getenv("WEBHOOK_URL")
STATE_FILE      = Path("seen_ads.json")
SCAN_INTERVAL   = os.getenv("SCAN_INTERVAL")  # seconds between scrape runs
REQUEST_TIMEOUT = os.getenv("REQUEST_TIMEOUT") # seconds of timeout for request

def get_response():
    res = requests.get(URL, timeout=REQUEST_TIMEOUT)
    res.raise_for_status()  
    return res

def get_soup(res):
    return  bs(res.content, features="html.parser")

def get_all_elements(soup) -> list:
    return list(soup.find_all("article"))

def get_ad_dict(ad) -> dict:
    ad_dict = {}

    # The ID is formatted as search-ad-XXXXX
    ad_id_raw  = ad.find("div", {"class":"absolute"})["aria-owns"]
    ad_id      = ad_id_raw.split("-")[2]

    # Two images should be avaiable for ad
    img_raw   = ad.find_all("div", {"class":"aspect-16/9"})
    # Smth like <div class: "...", alt = "Bilde X" <img src = ".."

    ad_images = []

    #NOTE: manage the case where no image is provided
    try:
        for img in img_raw:
            ad_image = img.find("img")["src"]
            ad_images.append(ad_image)
    except:
        ad_images.append("https://www.immobiliareandromeda.it/wp-content/uploads/a-casa-dos-flintstones.jpg")

    # Missing the prefix: https://www.finn.no/
    ad_link  = ad.find("a", {"class":"sf-search-ad-link"})["href"]
    ad_title = ad.find("a", {"class":"sf-search-ad-link"}).get_text()
    ad_address = ad.find("div", {"class":"sf-realestate-location"}).get_text()

    # Price & Sqm
    quant_data = list(ad.find("div", {"class":"justify-between"}).find_all("span"))
    ad_sqm     = quant_data[0].get_text()
    ad_price   = quant_data[1].get_text()

    # Type of ad (i.e. Apartment w/ 4 bedrooms)
    ad_type = ad.find("div", {"class":"sm:items-baseline"}).get_text()
    

    # Fill the dict
    ad_dict = {
        "ID"     : ad_id,
        "LINK"   : "https://www.finn.no/" + ad_link,
        "TITLE"  : ad_title, 
        "ADDRESS": ad_address,
        "SQM"    : ad_sqm,
        "PRICE"  : ad_price, 
        "TYPE"   : ad_type, 
        "IMAGES" : ad_images, # List of images    
    }

    return ad_dict


def load_state() -> set:
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()    # empty state in case of STATE_FILE is empty 

def save_state(state:set) -> None: 
    STATE_FILE.write_text(json.dumps(list(state), indent=2))
    
def check_once(elements) -> None: 
    state = load_state()
    # loop for each ad available from soup
    for ad in elements:
        ad_dict = get_ad_dict(ad)
        if ad_dict["ID"] not in state: 
            notify(ad_dict, "NEW AD")
            state.add(ad_dict["ID"])
    
    save_state(state)

def notify(ad_dict:dict, n_type:str) -> None:

    # NEW AD
    if n_type == "NEW AD": 
        color = 5814783
    # FAIL 
    #else:
        # color = RED COLOR
        
    embed = {
        "title":  ad_dict["TITLE"],
        "url":    ad_dict["LINK"],
        "color":  color,
        "fields": [                     
            {"name": "Price",   "value": ad_dict["PRICE"],   "inline": True},
            {"name": "Address", "value": ad_dict["ADDRESS"], "inline": False},
            {"name": "SQM",     "value": ad_dict["SQM"],     "inline": False},
            {"name": "Type",    "value": ad_dict["TYPE"],    "inline": False},
        ],
        "image": {"url": ad_dict["IMAGES"][0]},
    }

    # Send the POST request to Discord
    data = {
        "username": "Real Estate Monitor",
        "embeds": [embed]  # Discord requires embeds as a list
    }

    response = requests.post(WEBHOOK_URL, json=data)    

                                      
if __name__ == "__main__":

    # INITIAL LOG
    print(f"Monitoring {URL}")
    print(f"Scraping every {SCAN_INTERVAL} | Current state saved to {STATE_FILE}\n")

    # START THE "INFINITE" LOOP 
    while True: 
        res = get_response()
        soup = get_soup(res)
        elements = get_all_elements(soup)
        check_once(elements)
        time.sleep(SCAN_INTERVAL)
