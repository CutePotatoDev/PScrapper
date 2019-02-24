import logging
from util.webkit.webkit import WebKit


log = logging.getLogger("potatowebkit")
log.setLevel(logging.WARNING)

sh = logging.StreamHandler()

formatter = logging.Formatter("%(asctime)s %(threadName)-13s %(levelname)-7s %(message)s")
sh.setFormatter(formatter)

log.addHandler(sh)
