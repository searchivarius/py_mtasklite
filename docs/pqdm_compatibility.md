# PQDM (in)compatibility notes

Although we have a `pqdm` compatibility mode, it is not possible to be 100% compatible (for various reasons). Most importantly, we have to return an iterable rather than a list (for memory-efficient processing).

Here is the complete list of major interface/implementation differences:

1. We return an iterable, wrapped in a **context manager object** rather than a list. In that, if you **not** use the `with-statement` and do not iterate through all input the items, worker processes/threads will not be terminated! Please see [this page for more details](docs/context_manager_and_resource_leakage.md).

2. Because we support a wider range of worker types, we changed the parameter name `function` to `worker_or_worker_arr`. An array of workers can include regular functions, objects with delayed initialization, or a mix of both. 

4. When `worker_or_worker_arr` accepts a list of workers, the argument `n_jobs` does not have to be specified because the number of jobs should be equal to the number of workers in the array.

5. Likewise, because we support generic iterables rather than lists, the parameter name `array` was changed to `input_iterable`. However, the order of these arguments remains the same, so renaming should not cause any issues if the first two parameters are passed as **positional** arguments.

5. The 'direct' argument passing mode name in `pqdm` is confusing. Thus, we renamed it to `single_arg`. However, this is a default argument passing value (in both `pqdm` and `mtasklite`). Thus, unless `direct` is specified explicitly in the code that uses `pqdm` (which is unlikely), no additional changes will be required due to this renaming.

6. Regarding the bounded execution flag, we set it to `False` by default, which enables "lazy" iteration with a bounded input/output queue.

8. We always start a thread/process for a worker even if `n_jobs` is set to one. In contrast, if `n_jobs = 1`, `pqdm` runs a job in the same process/thread.

