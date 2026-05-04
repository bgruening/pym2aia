from .ImzMLReader import *
from .Generators import *
from .Dataset import *
from .utils import *
from .Library import get_library

import os
import logging
import platform


def validate_environment():
    search_path = pathlib.Path(os.environ['M2AIA_PATH'])
    if not (search_path.is_dir() and len([p for p in search_path.glob("**/*M2aiaCore*")])):
        raise ImportError("Loading M2aia was not possible!")

def prepare_environment():
    # os.environ["M2AIA_DEBUG"] = ""
    # default search path is pointing to packaged binaries
    if not "M2AIA_PATH" in os.environ:
        os.environ["M2AIA_PATH"] = str(pathlib.Path(os.path.abspath(__file__)).parent / "bin")



prepare_environment()
validate_environment()
get_library()


