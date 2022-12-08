from .ImageIO import *
from .Generators import *
from .Dataset import *
from .utils import *
from .Library import get_library

import os
import logging
import platform

def validate_environment():
    search_path = pathlib.Path(os.environ['M2AIA_PATH'])
    if search_path.is_dir() and (len([p for p in search_path.glob("**/*M2aiaCoreIO*")])):
        logging.debug("os.environ['M2AIA_PATH'] = " + os.environ["M2AIA_PATH"])
    else:
        logging.error("os.environ['M2AIA_PATH'] = " + os.environ["M2AIA_PATH"])
        logging.error("Variable: M2AIA_PATH; Description: Binary search path for M2aia's libraries.")
        if not search_path.exists():
            logging.error("\t- does not exist!")
        
        if search_path.is_file():
            logging.error("\t- is not a directory!")
        
        # if not search_path.joinpath("MitkCore").exists():
        #     logging.error("\t- does not contain a folder called MitkCore!")

        if not len([p for p in search_path.glob("**/*M2aiaCoreIO*")]):
            logging.error("\t- missing library libM2aiaCoreIO.so or M2aiaCoreIO.dll!")
        
        logging.error("You can fix this problem by adding 'M2AIA_PATH' to your system environment variables. To do so, download the latest M2aia binaries from https://m2aia.github.io/m2aia.")
        raise ImportError("Loading M2aia was not possible!")


def prepare_environment():
    # os.environ["M2AIA_DEBUG"] = ""
    logging.basicConfig(format='%(levelname)s: %(message)s')
    if "M2AIA_DEBUG" in os.environ:
        logging.basicConfig(format='%(levelname)s:%(message)s', level = logging.DEBUG)

    # default search path is pointing to packaged binaries
    if not "M2AIA_PATH" in os.environ:
        if "Linux" in platform.platform():
            platform_name = "linux"
        else:
            platform_name = "windows"

        os.environ["M2AIA_PATH"] = str(pathlib.Path(os.path.abspath(__file__)).parent.joinpath("bin",platform_name))

        logging.debug("Default library search path: " + os.environ["M2AIA_PATH"])
    else:
        logging.debug("Manually defined library search path: " + os.environ["M2AIA_PATH"])


prepare_environment()
validate_environment()

# dry-load M2aia binary libraries
get_library()



