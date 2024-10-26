[![PyPI version](https://img.shields.io/pypi/v/mtasklite.svg)](https://pypi.python.org/pypi/mtasklite/)
[![Downloads](https://static.pepy.tech/badge/mtasklite)](https://pepy.tech/project/mtasklite)
[![Downloads](https://static.pepy.tech/badge/mtasklite/month)](https://pepy.tech/project/mtasklite)

# MultiTASKLite: A lightweight library for Python multitasking

The `mtasklite` library provides enjoyable parallelization of iterating through an iterable with or without a progress bar. It is inspired by the simplicity of the great [`pqdm` library](https://github.com/niedakh/pqdm), but it improves upon `pqdm` in several ways, in particular, by supporting object-based (stateful) workers, truly "lazy" iteration (see a [detailed list of features](#features--advantages-over-pqdm)), and context managers (i.e., a support for `with-statement`). Object-based workers are implemented using the cool concept of delayed initialization, which is effortlessly enabled by adding `@delayed_init` decorator to a worker class definition.

Supporting object-based workers enables:
  1. Using different GPUs, models, or network connections in different workers.
  2. Efficient initialization of workers: If the worker needs to load a model (which often takes quite a bit of time), it will be done once (per process/thread)  **before** processing input items. See the [Spacy-based tokenization notebook](examples/mtasklite_pqdm_spacy_tokenization_demo.ipynb) for an example.
  3. Logging and bookkeeping: Each worker is represented by an object that "lives" as long as we have items to process (data can be stored in the object attributes). 
  
The `mtasklite` package provides **pqdm-compatibility** wrappers, which can be used as a (nearly) drop-in replacement of `pqdm`. For an overview of differences, please refer to the [pqdm-compatibility notes](docs/pqdm_compatibility.md). Despite this, we would encourage using the class [mtasklite.Pool](mtasklite/pool.py) directly and with the `with-statement` (see a [sample notebook](examples/mtasklite_pool_square_demo.ipynb)).

This library is replacing [`py_stateful_map`](https://github.com/searchivarius/py_stateful_map). The objective **of this replacement** to provide a more convenient and user-friendly interface as well as to fix several issues.

To contribute please [refer to the guidelines](docs/contributing.md).

# Install & Use

To install:

```pip install mtasklite```

## Use via pqdm-compatibility wrappers
  
This library provides convenience wrappers that largely mimic `pqdm` behavior and parameters, in particular, in terms passing arguments to (function) workers and handling exceptions:

```
from mtasklite.processes import pqdm

def square(a):
    return a*a

input_arr = [1, 2, 3, 4, 5]

n_jobs = 4 
with pqdm(input_arr, square, n_jobs) as pbar:
    result = list(pbar)

result
# Should be equal to [1, 4, 9, 16, 25]
```

However, **unlike** `pqdm`, which returns all results as an array, `mtasklite` supports a truly lazy processing of results where both the input and output queues are bounded by default. To make this possible, `mtasklite` returns an **iterable** wrapped inside a context manager object. For the sake of simplicity, in this example we explicitly converted this iterable to an array.

Another difference here is the use of the `with-statement`. Although this is not mandatory, not consuming the complete input (due to, e.g., an exception) will lead to resource leakage in the form of "hanging" processes and threads. Not using the `with-statement` is safe to do **only** in the exception-ignoring mode when you ensure that the whole input is "consumed". Please, see [this page for more details](docs/context_manager_and_resource_leakage.md).

By default, we assume (similar to `pqdm`) that the worker function has only a single argument. Thus, we read values from the input iterable and pass them to the function one by one. However, we also support arbitrary positional or keyword (kwarg) arguments. For a description of argument-passing methods, please see [this page](docs/argument_passing.md).
      
By default `mtasklite` (and `pqdm`) uses `tqdm` to display the progress. For arrays and other size-aware iterables, one will see a progress bar moving from 0% to 100. For unsized iterables, one will see a dynamically updated number of processed items. 

Also note that by default both `mtasklite` and PQDM ignore exceptions: When a task terminates due to an exception this exception is returned **instead of** returning a value. For a description of other exception-processing modes, please, see [this page](docs/exception_processing.md).


To make the library initialize object-based (with a given set of parameters) workers, you need to:

1. Implement a class with a ``__call__`` function and an optional constructor.
2. Decorate the class definition used `@delayed_init`. 

This decorator "wraps" the actual object inside a shell object, which only memorizes object's initialization parameters. An actual instantiation is delayed till a worker process (or thread) starts. Here is an example of this approach:

```
from mtasklite import delayed_init
from mtasklite.processes import pqdm

@delayed_init
class Square:
    def __init__(self, proc_id):
        # It is important to import the module here (when using from the notebook)
        import multiprocess as mp
        print(f'Initialized process {mp.current_process()} with argument = {proc_id}\n')
    def __call__(self, a):
        return a*a

input_arr = [1, 2, 3, 4, 5]

# Four workers with different initialization arguments
with pqdm(input_arr, [Square(0), Square(1), Square(2), Square(3)])  as pbar:
    result = list(pbar) 

result
# Should be equal to [1, 4, 9, 16, 25]
```

# Features & Advantages over PQDM

`mtasklite` extends the functionality of `pqdm` and provides painless `map-style` parallelization with both stateless and object-based (stateful) workers. Like `pqdm` this library allows enjoyable parallelization with a progress bar, but with the following advantages (`pqdm` shortcomings are illustrated by [this sample notebook](examples/pqdm_example.ipynb)):

* `mtasklite` permits initialization of each worker using worker-specific parameters via a cool delayed initialization trick.
* `mtasklite` supports truly lazy processing of results where both the input and output queues are bounded (great for huge inputs).
* Thanks to building on top of the [multiprocess library](https://github.com/uqfoundation/multiprocess) it has a better cross-platform support, whereas `pqdm` requires setting `multiprocessing.set_start_method('fork')` when running on MacOS from, e.g., a Jupyter Notebook.


A more detailed overview of features:
* Just import `processes.pqdm` or `threads.pqdm` for a (nearly) drop-in replacement of the `pqdm` code. By default, this code uses the `tqdm.auto.tqdm_auto` class that chooses an appropriate `tqdm` representation depending on the environment (e.g., a terminal vs a Jupyter notebook). Alternatively, multitasking can be used separately from tqdm (via `mtasklite.Pool`) and/or `tqdm` can be applied explicitly to the output iterable (for improved code clarity). See [this notebook](examples/mtasklite_pool_square_demo.ipynb) or an example.
* The library supports any input iterable and passing worker arguments as individual elements (for single-argument functions), keyword-argument dictionaries, or tuples (for multiple positional arguments).
* Like `pqdm`, additional `tqdm` parameters can be passed as keyword-arguments. With this, you can, e.g., disable `tqdm`, change the description, or use a different `tqdm` class.
* In that, the code supports automatic parsing of `pqdm` kwargs and separating between the process pool class `mtasklite.Pool` args and `tqdm` args. For a full-list of "passable" arguments, please [see this page](docs/pool_arguments.md).
* Support for **both unordered** and ordered execution.
* The input queue is bounded by default. Setting `bounded` to False enables an unbounded input queue, which can result in faster processing at the expense of using more memory. **Caution**: If you read from a huge input file, setting `bounded` to False will cause loading the whole file into memory and potentially crashing your process.


# Credits

A **huge** shoutout to the creators of the [multiprocess library](https://github.com/uqfoundation/multiprocess), which is a drop-in replacement of the standard Python `multiprocessing` library, which resolves various pickling issues that arise on non-Unix platforms (when a standard multiprocessing library is used). Thanks to their effort, `mtasklite` works across Linux, Windows, and MacOS.

