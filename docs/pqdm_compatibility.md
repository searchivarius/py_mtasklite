# PQDM (in)compatibility notes

Although we have a `pqdm` compatibility mode, it is not possible to be 100% compatible (for various reasons). Most importantly, we have to return an iterable rather than a list (for memory-efficient processing).

Here is the complete list of major interface/implementation differences:

1. We return an iterable, wrapped in a **context manager object** rather than a list. As a result, if you do not iterate through the items, worker processes or threads will not be terminated! Please see [this page for more details](docs/context_manager_and_resource_leakage.md).

2. Because we support a wider range of worker types, we changed the parameter name `function` to `worker_or_worker_arr`. An array of workers can include regular functions, objects with delayed initialization, or a mix of both. When a list of workers is specified, there is no need to provide the parameter `n_jobs` (because it should be equal to the number of workers in the list).

3. Likewise, because we support generic iterables rather than lists, the parameter name `array` was changed to `input_iterable`. However, the order of these arguments remains the same, so renaming should not cause any issues if the first two parameters are passed as **positional** arguments.

4. When `worker_or_worker_arr` accepts a list of workers, the argument `n_jobs` need not be specified because the number of jobs should be equal to the number of workers in the array.

5. The 'direct' argument passing mode name in `pqdm` is confusing. Thus, we renamed it to `single_arg`. However, this is a default argument passing value (in both `pqdm` and `mtasklite`). Thus, unless it is specified explicitly in the code that uses `pqdm` (which is unlikely), no additional changes are required when using the `mtasklite` variant of `pqdm`.

6. Regarding the bounded execution flag, we set it to `False` by default, which enables "lazy" iteration. 

8. We always start a thread/process for a worker even if `n_jobs` is set to one. In contrast, if `n_jobs = 1` `pqdm` runs a job in the same process/thread.

