import logging
import queue
import re
import traceback
from threading import Thread
from grab import Grab, error
from multiprocessing import Queue
from time import sleep, time

log = logging.getLogger("PScrapper")


class Tag():
    def __init__(self):
        self.groupurl = None
        self.name = None

        self.values = []


class TagsCollector(Thread):
    def __init__(self, conf=None, name="TagsCollector"):
        super(TagsCollector, self).__init__(name=name)
        self.daemon = True

        self._conf = conf.params["common"]

        self._sleeptime = 2

        self._starttime = time()
        self._counter = 0
        self.rpm = 0

        self._web = Grab(timeout=50, connect_timeout=50, user_agent="Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0")

        self.type = {
            "checkbox": "{}?filters={{\"{}\":[\"{}\"]}}",  #&tb[limit]=48",
            "checkboxmerge": "{}?filters={{\"{}\":{{\"range\":[\"{}\"]}}}}",  #&tb[limit]=48",
            "checkboxrange": "{}?filters={{\"{}\":{{\"eq\":[\"{}\"]}}}}",  #&tb[limit]=48"
        }

        self.pattern = re.compile(r"document\.write\(Convert\.convert\((.*), \'(.*)\'\)\);")

        self.input = Queue()
        self.output = []

    def run(self):
        log.info("Starting tags collector.")

        try:
            if self._login():
                while True:
                    try:
                        tag = self.input.get(timeout=self._sleeptime)

                        if tag is not None:
                            try:
                                self._getTagData(tag)
                                self._counter += 1
                            except Exception as ex:
                                # traceback.print_exc()
                                log.error(ex)
                                sleep(40)

                    except queue.Empty:
                        pass

                    if (time() - self._starttime) >= 60:
                        self._starttime = time()
                        self.rpm = self._counter
                        self._counter = 0

                    sleep(self._sleeptime)
        except Exception as ex:
            print(ex)

        log.debug("Exiting items data collector.")

    def _login(self):
        self._web.go(self._conf["url"] + "/login")
        self._web.doc.set_input("_username", self._conf["username"])
        self._web.doc.set_input("_password", self._conf["password"])
        self._web.submit()

        if self._web.doc("//a[@class='dropdown-toggle username']").count() != 2:
            log.error("Login failed: {}".format(self._conf["url"] + "/login"))
            return False

        log.info("Login successful: {}".format(self._conf["url"] + "/login"))
        return True

    def _getTagData(self, tag):
        for val in tag.values:
            # print(self.type[val[2]].format(tag.groupurl, val[1], val[0]))
            self._web.go(self.type[val[2]].format(tag.groupurl, val[1], val[0]))

            skus = []
            for item in self._web.doc("//div[@class='product-grid-item-content']"):
                skus.append(item.select("ul/li/i[@itemprop='sku']").text())

            match = self.pattern.match(val[3])
            if match:
                # print(tag.groupurl + "->" + val[3])
                val[3] = self._convertto(match.group(1), match.group(2))

            val.append(skus)
            sleep(self._sleeptime)

        self.output.append(tag)

    def _convertto(self, bytes, to, bsize=1024):
        a = {"MB/s": 0, "Watt": 0, "spm": 0, "g/m²": 0, "": 0, "KB": 1, "MB": 2, "GB": 3, "TB": 4}
        b = {"tommer": 0, "Hz": 0, "MHz": 2, "GHz": 3}
        c = {"timer": 2}
        r = float(bytes)

        if to in a:
            for i in range(a[to]):
                r = r / bsize
        elif to in b:
            for i in range(b[to]):
                r = r / 1000
        elif to in c:
            for i in range(c[to]):
                r = r / 60

        return int(r)


def loadTags(tags, items):
    tagnames = {}

    # Fill up names list.
    for tag in tags:
        if tag.name not in tagnames:
            tagnames[tag.name] = ""

    for tag in tags:
        for value in tag.values:
            val = value[3]

            for sku in value[4]:
                if sku in items:
                    items[sku].tagsdict[tag.name] = val

    for key in items.keys():
        items[key].tags = []

        for tagkey in tagnames.keys():
            if tagkey in items[key].tagsdict:
                items[key].tags.append(items[key].tagsdict[tagkey])
            else:
                items[key].tags.append("")

    return items, list(tagnames.keys())
