'''Settings for the game.'''

import logging
import coloredlogs

__version__ = "0.0.0 PT"

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG' if True else 'LOG', logger=logger,fmt="%(asctime)s %(name)s %(levelname)s: %(message)s")
logging.basicConfig(filename="logs/latest.log")
logger.debug(f"app script loaded! version: {__version__}")