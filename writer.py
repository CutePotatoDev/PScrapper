import logging
import os
import re
import json
import time
import queue
from threading import Thread
from grab import Grab
from grab.error import GrabTimeoutError, GrabConnectionError, GrabNetworkError, GrabCouldNotResolveHostError
from translate import Translator
from textblob import TextBlob
from os import path
from multiprocessing import Queue


log = logging.getLogger("PScrapper")


class Writer(Thread):
    def __init__(self, conf=None, name="Writer"):
        super(Writer, self).__init__(name=name)
        self._conf = conf

        self._params = conf.params["writer"]
        self._prices = conf.catconf["prices"]

        self.input = Queue()
        self.output = {}

        self._sleeptime = 0.5

        self._starttime = time.time()
        self._counter = 0
        self.rpm = 0

        self._web = Grab(timeout=50, connect_timeout=50)

        # Translation setup from Danish to Sweden.
        self._translate = Translator(from_lang="da", to_lang="sv", email=self._params["email"])

        # Expression for special danish alphabet symbols.
        self._regex = re.compile("[ÆØÅæøå]|sort|brun|hvid|kerner", flags=re.IGNORECASE)

        # Skip translation of these colors.
        self._colors = {
            "svart", "blå", "brun",
            "grå", "grön", "orange",
            "röd", "vit", "guld",
            "pink", "saddle brown", "silver",
            "white", "black", "gold",
            "yellow", "blue", "coral"
        }

        # Load dictionary.
        with open("dictionary.json", "r", encoding="UTF-8") as json_data:
            self._dictionary = json.load(json_data)

        # Create images folder.
        if not path.exists("images"):
            os.makedirs("images")

    def run(self):
        log.info("Starting writer.")

        transl = 0

        while True:
            try:
                item = self.input.get(timeout=self._sleeptime)

                # Set image location.
                if item.image is not None:
                    try:
                        name = item.image.split("/")[-1]

                        if path.exists("images/" + name) is False:
                            self._web.download(item.image, "images/" + name)

                        if self._conf.args.outputformat == "standart":
                            item.image = str(os.getcwd()) + "\\images\\" + name
                        elif self._conf.args.outputformat == "shopify":
                            item.image = "https://nordentobak.se/wp/wp-content/uploads/scraped/" + name

                    except GrabCouldNotResolveHostError:
                        log.error("Item image host not resolved. SKU: {}, image: {}".format(item.sku, item.image))

                for key, value in item.subcategory.items():
                    elements = key.split("|")

                    # Manage prices percentage by group.
                    for i in range(len(elements) - 1, -1, -1):
                        cat = elements[i]

                        if cat in self._prices:
                            item.price = "{:.2f}".format(float(item.price) * (1 + 0.01 * self._prices[cat]))
                            break

                # Translate menu names.
                item.subcategory = self._menuTranslates(item.subcategory)

                if item.itemshortname not in self._dictionary:
                    transl += 1
                    tmp = self._translates(item.itemshortname)
                    self._dictionary[item.itemshortname] = tmp
                    item.itemshortname = tmp
                else:
                    item.itemshortname = self._dictionary[item.itemshortname]

                # Save translations every 15'th one.
                if transl > 15:
                    transl = 0
                    json_data = open("dictionary.json", "w", encoding="UTF-8")
                    json.dump(self._dictionary, json_data, indent=4, ensure_ascii=False)
                    json_data.close()

                # Manufacturer name fix.
                if item.manufacturer == "Direct Computer Supplies":
                    item.manufacturer = "Mr.PC"

                item.itemshortname = item.itemshortname.replace("DCS", "")
                item.itemlongname = item.itemlongname.replace("DCS", "")

                itemcolor = None
                for color in self._colors:
                    if color in item.itemshortname.lower():
                        itemcolor = " " + color

                newname = self._search(item.eancode)
                if newname is None:
                    newname = self._search(item.manufacturernumber)
                    if newname is not None:
                        item.itemshortname = newname

                        if itemcolor is not None:
                            item.itemshortname += itemcolor
                    else:
                        pass
                        # log.debug("SKU: [{}] has not found on prisjakt.nu.".format(item.sku))
                else:
                    item.itemshortname = newname

                    if itemcolor is not None:
                        item.itemshortname += itemcolor

                # extra changes when scrapping for shopify engine.
                if self._conf.args.outputformat == "shopify":
                    for key, val in enumerate(item.subcategory.split("|")):

                        # set collection as main menu name.
                        if key == 0:
                            item.collection = val.strip()
                        else:
                            item.tags += val.strip() + ", "

                    # Remove excess symbols from items end.
                    item.tags = item.tags[:-2]

                if item.sku not in self.output:
                    self.output[item.sku] = item
                else:
                    self.output[item.sku].subcategory += " ||" + item.subcategory

                self._counter += 1
                time.sleep(self._sleeptime)

            except GrabTimeoutError as ex:
                log.error("Item image get timeout. SKU: {}, image: {}".format(item.sku, item.image))
            except queue.Empty:
                pass

            if (time.time() - self._starttime) >= 60:
                self._starttime = time.time()
                self.rpm = self._counter
                self._counter = 0

    # Set translates for menu-groups elements.
    # Also manage subgroups separator. It's not correct place do it here but it's comfortable.
    def _menuTranslates(self, txt):
        # txtout = txt
        tmp = ""

        for key, value in txt.items():
            elements = key.split("|")

            for i in range(len(elements)):
                try:
                    if self._conf.menudict[elements[i]] is not "":
                        tmp += self._conf.menudict[elements[i]] + " " + self._conf.args.subgroupssep + " "
                    else:
                        tmp += value.split("|")[i] + " " + self._conf.args.subgroupssep + " "
                except KeyError:
                    tmp += value.split("|")[i] + " " + self._conf.args.subgroupssep + " "

        if tmp is not "":
            txtout = tmp[:-3]

        return txtout

    def _translates(self, txt):
        txtout = txt

        if txt != "":
            lang = TextBlob(txt).detect_language()

            if lang == "en":
                if self._regex.search(txt) is None:
                    return txtout

            txtout = self._translate.translate(txt)

            if txtout is "":
                log.error("Translate fail for: ".format(txt))
                txtout = txt

        log.debug(txt + " <--> " + txtout)

        return txtout

    def _search(self, searchkey):
        if searchkey is None:
            return None

        try:
            self._web.go("https://search.prisjakt.nu/api?class=Search_Supersearch&method=search&market=se&skip_login=1&modes=product&limit=12&q=" + searchkey)
        except (GrabConnectionError, GrabNetworkError):
            log.error("Get timeout from prisjakt.nu.")
            return None

        itemdata = json.loads(self._web.doc.body)

        itemcount = len(itemdata["results"]["product"]["hits"])

        if itemcount is 0:
            return None
        else:
            itemname = itemdata["results"]["product"]["hits"][0]["item"]["name"]
            return itemname
