from functools import partial
from .pqdm import _pqdm

pqdm = partial(_pqdm, use_threads=False)