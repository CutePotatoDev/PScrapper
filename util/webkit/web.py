import logging
import signal
import queue
from functools import partial
from time import sleep, time
from multiprocessing import Queue
from threading import Thread, Event
from PyQt5.QtCore import QUrl, pyqtSignal, QThread, QTimer
from PyQt5.QtWebEngineWidgets import QWebEnginePage


log = logging.getLogger("potatowebkit")


class WebPage(QWebEnginePage):
    gosig = pyqtSignal(QUrl)

    def __init__(self):
        QWebEnginePage.__init__(self)

        self.loadFinished.connect(self.loadCompleted)
        self.gosig.connect(self.load)

        self._pipequeue = None

        self.free = True

        self.contentloadhandler = None
        self.checkktime = 400
        self.thread = None

        self.starttime = 0

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        pass

    def go(self, url):
        self.starttime = time()
        self.free = False
        self.gosig.emit(QUrl(url))

        # self.loadtimer = LoadTimer(self)
        # self.loadtimer.start()

    def loadCompleted(self, result):
        # self.loadtimer.stop()

        if self.contentloadhandler is not None:
            # keep checking or some extra JS content already loaded.
            if self.thread is None:
                self.thread = CheckContent(self)
                self.thread.finished.connect(self._clearThreadInfo)
                self.thread.start()
        else:
            self.free = True

    def _clearThreadInfo(self):
        loadtime = time() - self.starttime
        log.debug("Page load time: {:.2f} s.".format(loadtime))

        if loadtime > 60:
            log.warning("Page load time: {:.2f} s. [{}]".format(loadtime, self.url().toString()))

        self.thread = None
        self.free = True


# class LoadTimer(Thread):
#     def __init__(self, webpage):
#         super(LoadTimer, self).__init__(name="LoadTimer")
#         self.daemon = True
#         self.webpage = webpage
#         self._stop = Event()

#     def stop(self):
#         self._stop.set()

#     def run(self):
#         while not self._stop.wait(5):
#             loadtime = time() - self.webpage.starttime

#             if loadtime > 720:
#                 log.error("Load time to long: {}".format(self.webpage.url().toString()))


class CheckContent(QThread):
    def __init__(self, webpage):
        super(CheckContent, self).__init__()

        self.webpage = webpage
        self._counter = 0

    def run(self):
        while True:
            if self.webpage.contentloadhandler(Page(self.webpage)):
                break

            if self._counter > 720:
                log.warning("Page hangs.")
                log.warning(self.webpage.url().toString())

            self._counter += 1
            sleep(0.25)


class Page():
    def __init__(self, webpage):
        self.webpage = webpage

    @property
    def URL(self):
        return self.webpage.url().toString()

    @property
    def pipe(self):
        return self.webpage._pipequeue

    def _callback(self, func, signal, status):
        signal.put(func(self, status))

    def _runJSWithCallback(self, js, callback):
        signal1 = Queue()
        self.webpage.runJavaScript(js, partial(self._callback, callback, signal1))

        try:
            return signal1.get(timeout=6)
        except queue.Empty:
            return None

    # Check or element with defined name exists.
    def checkElementByName(self, name, callback=None):
        return self._runJSWithCallback("if(document.getElementsByName('{}').length != 0){{true;}} else {{false;}}".format(name), callback)

    # Check or element with defined id exists.
    def checkElementById(self, id, callback=None):
        return self._runJSWithCallback("if(document.getElementById('{}')){{true;}} else {{false;}}".format(id), callback)

    def checkElementByClassName(self, name, callback=None):
        return self._runJSWithCallback("if(document.getElementsByClassName('{}').length != 0){{true;}} else {{false;}}".format(name), callback)

    def countElementsByClassName(self, name, callback=None):
        return self._runJSWithCallback("document.getElementsByClassName('{}').length;".format(name), callback)

    # Click some element by id.
    def clickElementById(self, name):
        return self.webpage.runJavaScript("document.getElementById('{}').click()".format(name))

    # Set element value by name.
    def setElementByName(self, name, value):
        return self.webpage.runJavaScript("document.getElementsByName('{}')[0].value = '{}'".format(name, value))

    def toHtml(self, callback):
        signal1 = Queue()
        self.webpage.toHtml(partial(self._callback, callback, signal1))

        try:
            return signal1.get(timeout=6)
        except queue.Empty:
            return None
