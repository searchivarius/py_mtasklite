# A library for Python lightweight multitasking

A missing piece of the Python multitask (both threads and processes) API: An extension that supports stateful worker pools &amp; size-aware iterators.

# terminology reminder

sized vs un-sized iterators

# pqdm (in) compatibility

Although we have a pqmd compatibility mode, for various reasons, we have decided to not make our code
100% compatible. There are a couple of crucial differences:

1. We return an iterable, not a list.

2. Because semantics of the worker parameter is extended (it can be a list including both functions and statefull class objects) we changed the parameter name `function` to `worker_or_worker_arr`. Likewise, because we support generic iterables rather than lists, the parameter name `array` was changed into `input_iterable`. However, the order of these arguments remains the same, so renaming should matter little in practice.

3. The 'direct' argument passing mode name is confusing and we called it a single-argument mode instead (and define a new constant). Fortunately, this is a default argument passing value, so we anticipate that no code change will be required.

4. Regarding the bounded execution flag, we set it to false by default. Moreover, we cannot support it for un-sized iterators. However, if the iterator is for the object with a known size, we simulate unbounded execution by setting the chunk size to be equal to the length of the input (and setting prefill ratio to 1).

5. We always start a thread/process for a worker even if n_jobs == 1.

6. Clarify on the default behavior of the exceptions, which is IGNORE

Additional features:

1. Support for explicit initialization of **stateful** workers. This can be useful for quite a few things such as:
   
    i. Using different GPUs, models, or network connections in different workers.

    ii. Efficient initialization of workers: If the worker needs to load a model (which often takes quite a bit of time) it will be done only once before processing input items.

    iii. Logging and bookkeeping: Each worker is represented by an object that lives as long as we have items to process. Thus, object's state can be used to save important information.

2. Lazy memory-efficient iteration: supporting both size-providing iterables (e.g., over an array) and "unsized" ones (pqdm only accepts arrays as input).

3. Unordered execution: If you do not need return values to be ordered the order will not be enforced if the argument `is_unordered` is set `False`.

4. Task timeouts.

5. Can be used separately from tqdm, or tqdm can be called explicitly to improve code clarity.

6. Support for context management to make sure child processes won't be left running!

