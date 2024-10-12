# A library for Python lightweight multitasking

A missing piece of the Python multitask (both threads and processes) API: An extension that supports stateful worker pools &amp; size-aware iterators.

# terminology reminder

sized vs un-sized iterators

# pqdm (in) compatibility

Although we have a pqmd compatibility mode, for various reasons, we have decided to not make our code
100% compatible. There are a couple of crucial differences:

1. Additional features:

   i. Support for explicit initialization of **stateful** workers

   ii. Lazy memory-efficient iteration: supporting both size-providing iterables (e.g., over an array) and "unsized" ones.

   iii. Task timeouts 

   iv. Support for context management to make sure child processes won't be left running!

3. The 'direct' argument passing mode name is confusing and we called it a single-argument mode instead (and define a new constant). Fortunately, this is a default argument passing value, so we anticipate that no code change will be required.

4. Regarding the bounded execution flag, we set it to false by default. Moreover, we cannot support it for un-sized iterators. However, if the iterator is for the object with a known size, we simulate unbounded execution by setting the chunk size to be equal to the length of the input (and setting prefill ratio to 1).

5. We always start a thread/process for a worker even if n_jobs == 1.

6. Clarify on the default behavior of the exceptions, which is IGNORE


