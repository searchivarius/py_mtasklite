# Ensuring termination of processes and threads

Our `mtasklite` library explicitly starts a specified number of processes or threads, which need to be terminated when all work is done. This is handled by our code automatically in two cases:

1. When it detects the end of input (i.e., all input items are read).
2. When the object is created using the `with-statement` and the respective `with-block` finishes.

Let us consider an example without the context manager:

```
from mtasklite.processes import pqdm

def do_something_else(x):
    # some code goes here

def worker_func(a):
    return a*a

input_arr = [1, 2, 3, 4, 5]

n_jobs = 4 

result = []

for ret in pqdm(input_arr, worker_func, n_jobs):
    result.append(do_something_else(ret))
```

If the iteration finishes completely, all worker processes (or threads) will be terminated. However, if `do_something_else` raises an exception, worker processes remain "hanging". Likewise, a worker function may throw an exception and the workers will not be terminated either. 

By default, an exception processing mode is `ExceptionBehaviour.IGNORE`. Thus, these exceptions will not be re-raised and this will not interrupt the iteration. However, if the exception behavior is `ExceptionBehaviour.IMMEDIATE`, the input loop will  be "broken" and the processes will not be terminated. To prevent this, one can catch all the exceptions happening in the loop:

```
result = []

for ret in pqdm(input_arr, worker_func, n_jobs):
    try:
        result.append(do_something_else(ret))
    except:
        # do something
```

However, in many cases we may want to terminate the iteration right after receiving the exception (imagine you query the network resource and your credentials have expired). To cover this and other similar use cases, it is easier to **always** use the `with-statement`:

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