import logging
from threading import Thread
from grab import Grab
from multiprocessing import Queue


log = logging.getLogger("PScrapper")


class URLsCollector(Thread):
    def __init__(self, conf=None):
        super(URLsCollector, self).__init__(name="URLsCollector")

        self._conf = conf.params["common"]
        self._categories = conf.catconf["categories"]
        self._noskip = conf.catconf["noskip"]

        self._sleeptime = 0.5

        self._web = Grab(timeout=50, connect_timeout=50)

        self.urlqueue = Queue()

    def run(self):
        log.info("Starting URL's collector.")

        if self._login():
            for url in self._categories:
                results = self._getMenuSubURLs(url)

                if results is not None:
                    for result in results:
                        self.urlqueue.put(result)

        log.info("Exiting URL's collector.")

    def _login(self):
        self._web.go(self._conf["loginurl"] + "/login")
        self._web.doc.set_input("_username", self._conf["username"])
        self._web.doc.set_input("_password", self._conf["password"])
        self._web.submit()

        if self._web.doc("//a[@class='dropdown-toggle username']").text() != self._conf["username"]:
            log.info("Login failed: {}".format(self._conf["loginurl"] + "/login"))
            return False

        log.info("Login successful: {}".format(self._conf["loginurl"] + "/login"))
        return True

    def _getMenuSubURLs(self, url):
        global noskip

        # Unknown stuff, need to check.
        if "tver/fladskaerm" in url:
            self._web.go(url + "?tb[stock]=allproducts")
        else:
            self._web.go(url + "?tb[limit]=96")

        listt = self._web.doc("//li[@class='lvl-childrens']/a/@href")
        lasturl = self._web.doc("//li[@class='last  ']/a/@href")

        urls = []

        for subcat in listt:
            results = self._getMenuSubURLs(subcat.text())

            if results is not None:
                for result in results:
                    # If not in translations config part ???
                    if result.split("?")[0] not in self._noskip:
                        # log.debug("Skip URL: {}.".format(result))
                        continue

                    self.urlqueue.put(self._conf["url"] + result)

        if len(lasturl) is not 0:
            maxpage = lasturl[1].text().split("page=")[1]
        else:
            maxpage = 1

        if len(listt) == 0:
            for page in range(1, int(maxpage) + 1):
                if "tver/fladskaerm" in url:
                    urls.append(url + "?page=" + str(page) + "&tb[stock]=allproducts")
                else:
                    urls.append(url + "?tb[limit]=96&page=" + str(page))

        if len(urls) is not 0:
            return urls

        return None
