"""Top-level package for hvcfinder."""

import logging
import sys

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s;%(levelname)s;%(message)s",
)
