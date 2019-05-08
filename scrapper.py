# -*- coding: UTF-8 -*-

import logging
import re
import signal
import util.csv
import argparse
import json
import os
import psutil
from multiprocessing import Queue
from time import sleep
import configparser
from urlscollector import URLsCollector
from util.webkit import WebKit
from grab.document import Document
from items import Item
from itemsdatacollector import IDCollector
# from tagsdatacollector import TagsCollector, loadTags
from writer import Writer

log = logging.getLogger("PScrapper")
log.setLevel(logging.INFO)

# logging.getLogger("potatowebkit").setLevel(logging.DEBUG)s

fformatter = logging.Formatter("%(asctime)s %(threadName)-13s %(levelname)-7s %(message)s")
fhandler = logging.FileHandler("scrapper.log")
fhandler.setFormatter(fformatter)
fhandler.setLevel(logging.DEBUG)
log.addHandler(fhandler)

sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(threadName)-13s %(levelname)-7s %(message)s")
sh.setFormatter(formatter)
log.addHandler(sh)


class Config():
    def __init__(self, args=None):
        self.args = args
        self.params = configparser.ConfigParser()
        self.params.read("./params.conf")

        self.menudict = {
            "/sv/category": "Hem"
        }

        self.catconf = self.categoriesConfLoad()

    def categoriesConfLoad(self):
        out = {}

        log.debug("Load categories url's configuration file.")

        with open("categories.json", "r", encoding="UTF-8") as json_data:
            tmp = json.loads(re.sub("^ *//.*", "", json_data.read(), flags=re.MULTILINE))

            out["categories"] = tmp["categories"]
            out["noskip"] = [*tmp["translations"]]
            out["prices"] = tmp["prices"]

            for url in out["categories"]:
                log.debug("Load URL: {}".format(url))

            log.info("Loaded {} categories url's.".format(len(out["categories"])))

            self.menudict.update(tmp["translations"])
        return out


parser = argparse.ArgumentParser(description="Potato scrapper.", formatter_class=argparse.ArgumentDefaultsHelpFormatter, add_help=False)
parser.add_argument("-sgs", "--subgroups_sep", default="|", dest="subgroupssep", help="Set separator for subgroups in output file.")
parser.add_argument("-o", "--out", default="data.csv", metavar="FILENAME", dest="filename", help="Name of output file.")
parser.add_argument("-h", "--help", action="help", default=argparse.SUPPRESS, help="Show this help message and exit.")
args = parser.parse_args()


conf = Config(args)


def main():
    global conf

    fields = [
        'Name', 'Long name', 'Product price', 'Quantity', "Product ID",
        'modelnr', 'EAN', 'Manufacturer name', 'Weight',
        'Product image', "Description", 'Categories name'
    ]

    csvwriter = util.csv.CSVWriter(conf.args.filename, fieldnames=fields)

    try:

        signal.signal(signal.SIGINT, signal.SIG_DFL)
        kit = WebKit(gui=False)
        kit.poolsize = int(conf.params["webkit"]["threads"])
        kit.init()

        kit.go(conf.params["common"]["url"] + "/login")
        kit.registerContentLoadHandler(contentLoad)
        kit.pipe.get()

        urlcollector = URLsCollector(conf)
        urlcollector.daemon = True
        urlcollector.urlqueue = kit.urlqueue
        urlcollector.start()

        outpipe = Queue()
        collectors = []

        for i in range(int(conf.params["itemsdatacollector"]["threads"])):
            itemsdatacollector = IDCollector(conf, name="IDCollector-" + str(i))
            itemsdatacollector.input = kit.pipe
            itemsdatacollector.output = outpipe
            itemsdatacollector.start()
            collectors.append(itemsdatacollector)

        result = {}
        writers = []

        for i in range(int(conf.params["writer"]["threads"])):
            writer = Writer(conf, name="Writer-" + str(i))
            writer.input = outpipe
            writer.output = result
            writer.start()
            writers.append(writer)

        tagsdata = []
        tags = []

        # for i in range(16):
        #     tag = TagsCollector(conf, name="TgCollector-" + str(i))
        #     tag.input = urlcollector.tagsqueue
        #     tag.output = tagsdata
        #     tag.start()
        #     tags.append(tag)

        while True:
            sleep(60)
            log.info("Pages URL's queue size: {}".format(urlcollector.urlqueue.qsize()))
            log.info("Tags queue size: {}".format(urlcollector.tagsqueue.qsize()))

            rpm2 = 0
            for col in tags:
                rpm2 += col.rpm

            log.info("Tags RPM: {}".format(rpm2))
            log.info("Initial items read Page/min.: {}".format(kit.rpm))
            log.info("Items input queue size: {}".format(kit.pipe.qsize()))

            rpm = 0
            for col in collectors:
                rpm += col.rpm

            log.info("Items read RPM: {}".format(rpm))
            log.info("Items output queue size: {}".format(outpipe.qsize()))

            rpm1 = 0
            for wr in writers:
                rpm1 += wr.rpm

            log.info("Items write RPM: {}".format(rpm1))

            # result = loadTags(tagsdata, result)
            csvwriter.overwriteCSV(result.copy())

            if urlcollector.urlqueue.qsize() == 0 and kit.rpm == 0 and kit.pipe.qsize() == 0 and rpm == 0 and outpipe.qsize() == 0 and rpm1 == 0:
                # Really bad variant just kill everything. But web kit have some bugs and not want exit easy.
                # And now i don't have much time to fix it nicely.
                # TODO: Fix web kit when it's be possible.

                parent = psutil.Process(os.getpid())
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()

    except KeyboardInterrupt:
        log.warning("Oh my, keyboard interrupt. Exiting.")

    log.info("Done.")


login = False


def contentLoad(page):
    global login

    if "/login" in page.URL and not login:
        page.checkElementById("login_form", loginResult)
        login = True

    elif "/da/home" in page.URL:
        page.pipe.put(None)
        return True

    elif "/category/" in page.URL:
        items = page.countElementsByClassName("product-grid-item-content", checkRez)

        if items == page.countElementsByClassName("dot", checkRez):
            if page.countElementsByClassName("price-novat", checkRez) > 0:
                page.toHtml(toHTMLStockParse)
                return True
    return False


# Initial parsing of items. Only item object are created and item url, stock data extracted.
def toHTMLStockParse(page, html):
    doc = Document()
    doc._grab_config = {
        "content_type": "html",
        "fix_special_entities": True,
        "lowercased_tree": False,
        "strip_null_bytes": True
    }

    doc.body = html.encode("UTF-8")
    doc.parse()

    for item in doc.select("//div[@class='product-grid']"):
        itemobj = Item()

        itemobj.url = item.select("./div[@class='product-grid-item-content']/h2[@itemprop='name']/a/@href").text()
        itemobj.sku = item.select("./div[@class='product-grid-item-content']/ul//i[@itemprop='sku']").text()

        green = item.select("./div[@class='stockstatus']/span[@class='dot']/i[@class='inventory inventory-green']").count()

        if green == 0:
            itemobj.stockvalue = 0
        else:
            stkvalue = item.select("./div[@class='stockstatus']/ul[@class='list-unstyled stocktext']/li")[0].text().strip().split(" stk")[0]

            if "+" in stkvalue:
                itemobj.stockvalue = stkvalue.replace("+", "")
            elif "." in stkvalue:
                itemobj.stockvalue = stkvalue.replace(".", "")
            else:
                itemobj.stockvalue = stkvalue

            page.pipe.put(itemobj)


def checkRez(page, rez):
    return rez


def loginResult(page, status):
    log.info("Start login.")
    global conf

    if status:
        page.setElementByName("_username", conf.params["common"]["username"])
        page.setElementByName("_password", conf.params["common"]["password"])
        page.clickElementById("_submit")
        log.info("Login done.")


if __name__ == "__main__":
    main()
