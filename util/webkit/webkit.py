import logging
import signal
from time import time
from multiprocessing import Queue
from multiprocessing import Process
from threading import Thread, current_thread, Event
from util.webkit.web import WebPage
from util.webkit.gui import MainWindow
from PyQt5.QtNetwork import QNetworkProxy
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView


log = logging.getLogger("potatowebkit")


# Thread to maintain all side interprocess signals, load of new URL's and other stuffs.
class SideThread(Thread):
    def __init__(self, main):
        super(SideThread, self).__init__(name="WebKitST")

        self.main = main
        self._stop = Event()

        self._starttime = time()
        self._counter = 0
        self._rpm = 0

    def stop(self):
        self._stop.set()

    def run(self):
        while not self._stop.wait(0.15):

            if not self.main._reqqueue.empty():
                func = self.main._reqqueue.get()

                if func == "rpm":
                    self.main._respqueue.put(self._rpm)
                elif callable(func):
                    for web in self.main._pool:
                        web.contentloadhandler = func

            for web in self.main._pool:
                if web.free:
                    # print(self.main.urlqueue.qsize())
                    if not self.main.urlqueue.empty():
                        url = self.main.urlqueue.get()
                        log.debug("Load URL: {}".format(url))
                        self._counter += 1
                        web.go(url)

            if (time() - self._starttime) >= 60:
                self._starttime = time()
                self._rpm = self._counter
                self._counter = 0


class WebKitProcess(Process):
    def __init__(self, proxy=None):
        super(WebKitProcess, self).__init__(name="WebKit")

        self.proxy = proxy
        self.gui = False
        self.daemon = True

        self.poolsize = 1
        self._pool = []

        self.urlqueue = Queue()
        self._reqqueue = Queue()
        self._respqueue = Queue()
        self._pipequeue = Queue()

    def run(self):
        current_thread().name = "WebKit"
        # signal.signal(signal.SIGINT, signal.SIG_DFL)

        app = QApplication([])
        signal.signal(signal.SIGINT, self.onExit)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Helps to handle Ctrl+C action.
        self.timer = QTimer()
        self.timer.start(1000)
        self.timer.timeout.connect(lambda: None)

        #  Setup proxy for browser elements.
        if self.proxy is not None:
            url, port = self.proxy.split(":")

            proxy = QNetworkProxy()
            proxy.setType(QNetworkProxy.HttpProxy)
            proxy.setHostName(url)
            proxy.setPort(int(port))
            QNetworkProxy.setApplicationProxy(proxy)

        for i in range(self.poolsize):
            renderer = WebPage()
            renderer._pipequeue = self._pipequeue
            self._pool.append(renderer)

        # Hmm... QThread blocks GUI, this, python one not blocks.
        self.sidethread = SideThread(self)
        self.sidethread.daemon = True
        self.sidethread.start()

        # Load GUI if it's needed.
        if self.gui:
            self.mv = MainWindow()
            self.mv.show()

            for web in self._pool:
                view = QWebEngineView()
                view.setPage(web)
                self.mv.addTab(view, web.title())

        app.exec_()

    # Exit signal function.
    def onExit(self, signum, frame):
        for web in self._pool:
            if web.thread is not None:
                web.thread.quit()

        self.sidethread.stop()
        self.timer.stop()

        if self.gui:
            self.mv.close()
        # # sleep(2)

        QApplication.quit()


class WebKit(WebKitProcess):
    def __init__(self, proxy=None, gui=False, join=False):
        super().__init__(proxy)

        self.join = join
        self.gui = gui

    def init(self):
        super().start()

        if self.join:
            super().join()

    @property
    def pipe(self):
        return self._pipequeue

    @property
    def rpm(self):
        self._reqqueue.put("rpm")
        return self._respqueue.get()

    def go(self, url):
        self.urlqueue.put(url)

    def registerContentLoadHandler(self, func):
        self._reqqueue.put(func)
