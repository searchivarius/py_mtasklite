[![PyPI version](https://img.shields.io/pypi/v/mtasklite.svg)](https://pypi.python.org/pypi/mtasklite/)
[![Downloads](https://static.pepy.tech/badge/mtasklite)](https://pepy.tech/project/mtasklite)
[![Downloads](https://static.pepy.tech/badge/mtasklite/month)](https://pepy.tech/project/mtasklite)

# MultiTASKLite: A lightweight library for Python multitasking

This `mtasklite` library is inspired by the simplicity of the great [`pqdm` library](https://github.com/niedakh/pqdm), but it improves upon `pqdm` in several ways, in particular, by supporting object-based (stateful) workers, truly "lazy" iteration, and context managers (i.e., a support for `with-statement`). Stateful workers are implemented using the cool concept of delayed initialization, which is effortlessly enabled by adding `@delayed_init` decorator to a worker class definition.

This enables:
  1. Using different GPUs, models, or network connections in different workers.
  2. Efficient initialization of workers: If the worker needs to load a model (which often takes quite a bit of time), it will be done once (per process/thread)  **before** processing input items.(examples/mtasklite_pqdm_spacy_tokenization_demo.ipynb) for an example.
  3. Logging and bookkeeping: Each worker is represented by an object that "lives" as long as we have items to process (data can be stored in the object attributes). 
  
The `mtasklite` package provides **pqdm-compatibility** wrappers, which can be used as a (nearly) drop-in replacement of `pqdm`. For an overview of differences, and a list of features, please, refer to the documentation [in the GitHub repository](https://github.com/searchivarius/py_mtasklite).

This library is replacing [`py_stateful_map`](https://github.com/searchivarius/py_stateful_map). The objective **of this replacement** to provide a more convenient and user-friendly interface as well as to fix several issues.

# Credits

A **huge** shoutout to the creators for the [multiprocess library](https://github.com/uqfoundation/multiprocess), which is a drop-in replacement of the standard Python `multiprocessing` library, which resolves various pickling issues that arise on non-Unix platforms (when a standard multiprocessing library is used). Thanks to their effort, `mtasklite` works across Linux, Windows, and MacOS.

