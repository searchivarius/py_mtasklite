# Argument passing

By default, we assume (similar to `pqdm`) that the worker function has only a single argument. Thus, we read values from the input iterable and pass them to the function one by one. 

However, the library supports passing either an array of positional arguments or a dictionary of named arguments (kwargs). 

Here is an example of passing named arguments:

```
from mtasklite.processes import pqdm
# If you want threads instead:
# from mtasklite.threads import pqdm

args = [
    {'a': 1, 'b': 2},
    {'a': 2, 'b': 3},
    {'a': 3, 'b': 4},
    {'a': 4, 'b': 5}
]

def multiply(a, b):
    return a*b

result = list(pqdm(args, multiply, n_jobs=2, argument_type=ArgumentPassing.AS_KWARGS)))
# result is [2, 6, 12, 20]
```

and for the positional arguments:
```
from mtasklite.processes import pqdm
# If you want threads instead:
# from mtasklite.threads import pqdm

args = [[1, 2], [2, 3], [3, 4], [4, 5]],

def multiply(a, b):
    return a*b

result = list(pqdm(args, multiply, n_jobs=2, argument_type=ArgumentPassing.AS_ARGS))
# result is [2, 6, 12, 20]
```