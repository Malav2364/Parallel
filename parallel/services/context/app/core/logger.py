import logging
import sys

from pythonjsonlogger.json import JsonFormatter

logger = logging.getLogger("context")

logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)

formatter = JsonFormatter("%(asctime)s %(levelname)s %(message)s")

handler.setFormatter(formatter)

logger.addHandler(handler)
