# List of `mtasklite.Pool` arguments 

Here is a full list of `mtasklite.Pool` arguments that can be passed through `pqdm` function:

* `input_iterable` Iterable to be processed in parallel (1st positional argument).
* `worker_or_worker_arr` A single worker function/object or a list of worker functions/objects (2d positional argument).
* `n_jobs` Number of worker processes/threads to create (3rd positional argument). It is ignored if `worker_or_worker_arr` is a list.
* `argument_type` Specifies how arguments are passed to workers (4th positional argument). For a description of argument-passing methods, please see [this page](../docs/argument_passing.md).
* `bounded` Whether to use bounded execution mode, which is `True` by default (5th  positional argument). The bounded execution mode is memory efficient.  In the unbounded execution mode, all input items are loaded into memory.
* `exception_behavior` Defines how exceptions are handled (6th  positional argument). For a description of other exception-processing modes, please, see [this page](../docs/exception_processing.md).
* `chunk_size` Size of chunks in the processing queue (kwarg-only).
* `chunk_prefill_ratio` Prefill ratio for chunks in the processing queue (kwarg-only).
* `is_unordered` Whether results can be returned in any order (kwarg-only).
* `task_timeout` Timeout for individual tasks (kwarg-only).
* `join_timeout` Timeout for joining workers (kwarg-only).
