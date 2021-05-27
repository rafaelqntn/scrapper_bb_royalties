import logging
import sys

logging.basicConfig(
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s.%(msecs)03d|%(levelname)s|%(module).s%(funcName)s|L%(lineno)d|%(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    level=logging.INFO  # May be modified by command line arguments.
)
