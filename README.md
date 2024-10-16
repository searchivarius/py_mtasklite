# MultiTASKLite: A lightweight library for Python lightweight multitasking

This `mtasklite` is inspired by simplicity of [PQDM](https://github.com/niedakh/pqdm), but it improves upon PQDM several ways, in particular, by supporting object-based (stateful) workers, truly "lazy" iteration (see a more [detailed list of features](#features)), and task timeouts. Stateful workers are implemented using a cool concept of the delayed initialization, which is effortlessly enabled by adding `@delayed_init` decorator to a worker class definition.

This enables:
  1. Using different GPUs, models, or network connections in different workers.
  2. Efficient initialization of workers: If the worker needs to load a model (which often takes quite a bit of time) it will be done only once before processing input items.
  3. Logging and bookkeeping: Each worker is represented by an object that lives as long as we have items to process. Thus, object's state can be used to save important information.

The `mtasklite` package provides **pqdm-compatibility** wrappers, which can be used as a (nearly) drop-in replacement of `pqdm`. For an overview of differences, please, refer to the [pqdm-compatability notes](docs/pqdm_compatibility.md)

# Install & Use

To install:

```pip install mtasklite```

## Use via pqdm-compatibility wrappers
  
`mtasklite` provides convenience wrappers that (with a few exceptions) mimic `pqdm` behavior and parameters, in particular, in terms passing arguments to (function) workers and handling exceptions:

```
from mtasklite.processes import pqdm

def square(a):
    return a*a

input_arr = [1, 2, 3, 4, 5]

n_jobs = 4 
result = pqdm(input_arr, square, n_jobs)

list(result)
```

However, **unlike** `pqdm`, which returns all results as an array, `mtasklite` supports a truly lazy processing of results where both the input and output queues are bounded by default. To make this possible, `mtasklite` returns an **iterable**. For the sake of simplicity, in this example we explicitly converted this iterable to an array.
      
By default `mtasklite` (and `pqdm`) uses `tqdm` to display the progress. For arrays and other  size-aware iterables, one will see an actual progress bar going from 0% to 100. For un-sized iterables, one will see a dynamically updated number of processed items. 

Also note that by default both `mtasklite` and PQDM ignore exceptions: When a task terminates due to an exception this exception is returned **instead of** a return value. You can check if exception happened using a convenience wrapper:
```
from mtasklite import is_exception

if is_exception(ret_val):
   do_something()
```

For a description of other exception-processing modes, please, see [this page](docs/exception_processing.md).

To make the library initialize object-based (with a given set of parameters) workers, one needs to:

1. Implement a class with a ``__call_`` function an an optional constructor.
2. Decorate the class definition used `@delayed_init`. 

This decorator "wraps" the actual object inside a shell object, which only memorizes object's initialization parameters. An actual instantiation is delayed till a worker process (or thread) starts. Here is an example of this approach:

```
from mtasklite import delayed_init
from mtasklite.processes import pqdm

@delayed_init
class Square:
    def __init__(self, proc_id):
        # It is important to import multiprocessing here (when using from the notebook)
        import multiprocessing as mp
        print(f'Initialized process ' + str(mp.current_process()) + ' with argument = {proc_id}\n')
    def __call__(self, a):
        return a*a

input_arr = [1, 2, 3, 4, 5]

# Four workers with different arguments
result = pqdm(input_arr, [Square(0), Square(1), Square(2), Square(3)])

list(result)
```

For a more detailed discussion, including the usage with a `with-statement` (which can help prevent resource leakage), please, the the [following page](docs/usage.md).

# Features

`mtasklite` extends the functionality of `pqdm` and has the following features:

* A painless `map-style` parallelization with both stateless and object-based (stateful) workers. Unlike `pqdm`, `mtasklite` permits initialization of each worker using worker-specific parameter via a cool delayed initialization trick. 
* Support for unordered execution and task timeouts.
* Support for any iterable and passing worker arguments as individual elements (for single-argument functions), keyword-argument dictionaries, or tuples (for multiple positional arguments) .
* Supports for truly lazy processing of results where both the input and outpu Logging and bookkeeping: Each worker is represented by an object that lives as long as we have items to process. Thus, object's state can be used to save important information.     t queues are bounded by default (setting `bounded` to True enables unbounded input queues).
* Just import `processes.pqdm` or `threads.pqdm` for a (nearly) drop-in replacement of the `pqdm` code. By default, this code uses the `tqdm.auto.tqdm_auto` class that choose an appropriate `tqdm` representation depending on the environment (most notably in Jupyter notebooks). Alternatively, multitasking can be used separately from tqdm (via `mtasklite.Pool`) and/or `tqdm` can be applied explicitly to the output iterable (for improved code clarity).
* Like `pqdm`, additional `tqdm` parameters can be passed as keyword-arguments. With this, you can, e.g., disable `tqdm`, change the description, or use a different `tqdm` class. 
* If you use `pqdm` in some contexts on MacOS, e.g., noteably in Jupyter notebooks, you have to set the process start type to `fork`, or you will have pickling errors:
`multiprocessing.set_start_method('fork')`.

# Credits

A **huge** shoutout to the creators for the [multiprocess library](https://github.com/uqfoundation/multiprocess), which is a drop-in replacement of the standard Python `multiprocessing` library, which has various pickling issues that arise on non-Unix platforms. Thanks to their effort, `mtasklite` works on Linux, Windows, and MacOS.

