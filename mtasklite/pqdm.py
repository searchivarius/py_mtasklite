from tqdm import tqdm as tqdm_type
from tqdm.auto import tqdm as tqdm_auto
from .constants import ExceptionBehaviour, ArgumentPassing
from .utils import divide_kwargs
from .pool import Pool

NO_EXPLICIT_POOL_KWARGS = ['bounded', 'exception_behaviour', 'worker_or_worker_arr', 'n_jobs', 'use_threads']


# Do not use directly, but rather import pqdm from threads or processes
def _pqdm(
    input_iterable,
    worker_or_worker_arr,
    n_jobs: int = None,
    argument_type:ArgumentPassing = ArgumentPassing.AS_SINGLE_ARG,
    bounded: bool = True,
    exception_behaviour: ExceptionBehaviour = ExceptionBehaviour.IGNORE,
    use_threads: bool = False,
    tqdm_class: tqdm_type = tqdm_auto,
    **kwargs
):
    add_pool_kwargs, tqdm_kwargs = divide_kwargs(kwargs, Pool)
    for arg in add_pool_kwargs:
        if arg in NO_EXPLICIT_POOL_KWARGS:
            raise Exception(f'Do not specify Pool argument {arg} as kwarg!')

    return tqdm_class(Pool(worker_or_worker_arr=worker_or_worker_arr, n_jobs=n_jobs, use_threads=use_threads,
                           bounded=bounded, argument_type=argument_type, exception_behavior=exception_behaviour,
                           **add_pool_kwargs)(input_iterable), **tqdm_kwargs)