import logging
from time import sleep
from threading import Thread
from grab import Grab
from multiprocessing import Queue
from tagsdatacollector import Tag


log = logging.getLogger("PScrapper")


class URLsCollector(Thread):
    def __init__(self, conf=None):
        super(URLsCollector, self).__init__(name="URLsCollector")

        self._conf = conf.params["common"]
        self._categories = conf.catconf["categories"]
        self._noskip = conf.catconf["noskip"]

        self._sleeptime = 0.8

        self._web = Grab(timeout=70, connect_timeout=70, user_agent="Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0")

        self.urlqueue = Queue()
        self.tagsqueue = Queue()

    def run(self):
        log.info("Starting URL's collector.")

        try:
            if self._login():
                for url in self._categories:
                    try:
                        results = self._getMenuSubURLs(url)

                        if results is not None:
                            for result in results:
                                self.urlqueue.put(result)
                    except Exception as ex:
                        log.error(ex)
                        sleep(40)

        except Exception as ex:
            log.error(ex)

        log.info("Exiting URL's collector.")

    def _login(self):
        self._web.go(self._conf["url"] + "/en/login")
        self._web.doc.set_input("_username", self._conf["username"])
        self._web.doc.set_input("_password", self._conf["password"])
        self._web.submit()

        if self._web.doc("//a[@class='dropdown-toggle username']").count() != 2:
            log.error("Login failed: {}".format(self._conf["url"] + "/login"))
            return False

        log.info("Login successful: {}".format(self._conf["url"] + "/login"))
        return True

    def _getMenuSubURLs(self, url):
        global noskip

        # Unknown stuff, need to check.
        # if "tver/fladskaerm" in url:
        #     self._web.go(url + "?tb[stock]=allproducts")
        # else:
        self._web.go(url + "?tb[limit]=96")

        listt = self._web.doc("//li[@class='lvl-childrens']/a/@href")
        lasturl = self._web.doc("//li[@class='last  ']/a/@href")

        urls = []

        for subcat in listt:
            results = self._getMenuSubURLs(subcat.text())
            sleep(self._sleeptime)

            if results is not None:
                for result in results:
                    # If not in translations config part ???
                    if result.split("?")[0] not in self._noskip:
                        log.debug("Skip URL: {}.".format(result))
                        continue

                    self.urlqueue.put(self._conf["url"] + result)

        if len(lasturl) is not 0:
            maxpage = lasturl[1].text().split("page=")[1]
        else:
            maxpage = 1

        if url.replace("https://dcs.dk", "") not in self._noskip:
            log.info("Skip URL: {}.".format(url))
        else:
            if len(listt) == 0:
                for page in range(1, int(maxpage) + 1):
                    # if "tver/fladskaerm" in url:
                    #     urls.append(url + "?page=" + str(page) + "&tb[stock]=allproducts")
                    # else:
                    urls.append(url + "?tb[limit]=96&page=" + str(page))

            log.debug("Loded URL: {}".format(url))

            for name in self._web.doc("//div[@class='check']"):
                tag = Tag()
                tag.groupurl = url
                tag.name = name.select("./h4").text()

                for t in name.select("./ul[@class='list-unstyled']/li/span/label"):
                    value = t.select("input/@data-value").text()
                    filter = t.select("input/@data-filter").text()
                    type = t.select("input/@data-type").text()
                    name = t.select("span").text()

                    tag.values.append([value, filter, type, name])

                log.debug("Tags URL: {} -> {}".format(url, tag.name))
                self.tagsqueue.put(tag)

        if len(urls) is not 0:
            return urls

        return None
