import logging
import queue
from threading import Thread
from time import time
from grab import Grab
from multiprocessing import Queue
from weblib.error import DataNotFound


log = logging.getLogger("PScrapper")


class IDCollector(Thread):
    def __init__(self, conf=None, name="IDCollector"):
        super(IDCollector, self).__init__(name=name)
        self.daemon = True

        self._conf = conf.params["common"]

        self._sleeptime = 0.5

        self._starttime = time()
        self._counter = 0
        self.rpm = 0

        self._web = Grab(timeout=50, connect_timeout=50)

        self.input = Queue()
        self.output = Queue()

    def run(self):
        log.info("Starting items data collector.")

        if self._login():
            while True:
                try:
                    item = self.input.get(timeout=self._sleeptime)

                    if item is not None:
                        self._web.go(item.url)
                        self.parseItemData(item)
                        self._counter += 1

                except queue.Empty:
                    pass

                if (time() - self._starttime) >= 60:
                    self._starttime = time()
                    self.rpm = self._counter
                    self._counter = 0

                # sleep(self._sleeptime)

        log.debug("Exiting items data collector.")

    def _login(self):
        self._web.go(self._conf["url"] + "/login")
        self._web.doc.set_input("_username", self._conf["username"])
        self._web.doc.set_input("_password", self._conf["password"])
        self._web.submit()

        if self._web.doc("//a[@class='dropdown-toggle username']").text() != self._conf["username"]:
            log.info("Login failed: {}".format(self._conf["url"] + "/login"))
            return False

        log.info("Login successful: {}".format(self._conf["url"] + "/login"))
        return True

    def parseItemData(self, item):
        try:
            tvs = self._web.doc("//ol[@class='breadcrumb']/li/a[contains(@href, '/sv/category/fototelefonigps/audioogvideo/tver/')]/@href").text()
        except (DataNotFound, IndexError):
            tvs = ""

        if item.stockvalue == 0:
            log.warn("SKU: [{}] not in stock.".format(item.sku))

        if "tver/fladskaerm" in tvs or item.stockvalue != 0:

            itemshortname = self._web.doc("//h1[@itemprop='name']")
            if itemshortname.count() != 0:
                item.itemshortname = itemshortname.text()

            itemlongname = self._web.doc("//div[@class='description']")
            if itemlongname.count() != 0:
                item.itemlongname = itemlongname.text().strip()

            try:
                item.sku = self._web.doc("//i[@itemprop='sku']").text()
            except DataNotFound as ex:
                item.sku = ""

            try:
                item.price = self._web.doc("//div[@class='desc']//span[@class='price']").text().strip().replace(" ", "").split(",")[0] + ".00"
            except DataNotFound as ex:
                log.warning("SKU: [{}] has no price.".format(item.sku))

            item.manufacturernumber = self._web.doc("//i[@itemprop='model']").text()

            eancode = self._web.doc("//i[@itemprop='ean']/@title")
            if eancode.count() != 0:
                item.eancode = eancode.text()

            try:
                item.manufacturer = self._web.doc("//i[@itemprop='brand']/@title").text()
            except DataNotFound as ex:
                log.warning("SKU: [{}] has no manufacturer.".format(item.sku))

            weight = self._web.doc("//i[@itemprop='weight']")
            if weight.count() != 0:
                item.weight = weight.text().replace(" kg", "")

            try:
                image = self._web.doc("//div[@class='images']//li[@data-id='0']/@data-original-url")
                if image.count() == 0:
                    tag = self._web.doc("//div[@class='images']//div[@class='mainimage']/href")

                    if tag.count() == 0:
                        tag = self._web.doc("//div[@class='images']//div[@class='product-lightbox-carousel']//img/@src")

                        if tag.count() == 0:
                            item.image = "https://cdn.cnetcontent.com/a9/c5/a9c59a19-56a8-43f6-bdf6-b33a703a328f.jpg"

                    if tag.text().startswith("https://") or tag.text().startswith("http://"):
                        item.image = tag.text()
                    else:
                        item.image = "https://dev.dcs.dk" + tag.text()
                else:
                    item.image = image.text()

            except DataNotFound as ex:
                log.warning("SKU: [{}] has no image.".format(item.sku))

            try:
                descriptiontable = self._web.doc("//div[@id='tab_2']")

                # Check or description have table structure. If not ignore it.
                if descriptiontable.select("./table[contains(@class, 'table')]").count() != 0:
                    item.description = descriptiontable.inner_html().replace("\n", "")
                else:
                    log.debug("SKU: [{}] has no table style description.".format(item.sku))

            except DataNotFound as ex:
                log.warning("SKU: [{}] has no description.".format(item.sku))

            data = ""
            path = ""
            for el in self._web.doc("//ol[@class='breadcrumb']/li/a"):
                url = el.select("./@href").text()

                if url != "/sv/category":
                    data += el.text().strip() + "|"
                    path += url + "|"

            item.subcategory = {path[:-1]: data[:-1]}

            self.output.put(item)
