# Exception processing

By default, both `mtasklite` and PQDM ignore exceptions: When a task terminates due to an exception this exception is returned **instead of** a return value.

You can check if exception happened using a convenience wrapper:
```
from mtasklite import is_exception

if is_exception(ret_val):
   do_something()
```