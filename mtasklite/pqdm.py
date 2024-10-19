from tqdm import tqdm as tqdm_type
from tqdm.auto import tqdm as tqdm_auto
from .constants import ExceptionBehaviour, ArgumentPassing
from .utils import divide_kwargs
from .pool import Pool

NO_EXPLICIT_POOL_KWARGS = ['bounded', 'exception_behaviour', 'worker_or_worker_arr', 'n_jobs', 'use_threads']


class CustomContextManager:
    """
    A custom context manager that combines tqdm and pool objects.

    This class allows for simultaneous management of a tqdm progress bar and a processing pool,
    ensuring proper setup and teardown of both objects.

    :param tqdm_obj: A tqdm object for progress tracking.
    :param pool_obj: A Pool object for parallel processing.
    """
    def __init__(self, tqdm_obj, pool_obj):
        self.tqdm_obj = tqdm_obj
        self.pool_obj = pool_obj

    def __enter__(self):
        self.tqdm_obj = self.tqdm_obj.__enter__()
        self.pool_obj.__enter__()
        return self

    def __exit__(self, type, value, tb):
        self.tqdm_obj.__exit__(type, value, tb)
        self.pool_obj.__exit__(type, value, tb)

    def __iter__(self):
        return self.tqdm_obj.__iter__()


def _pqdm(
    input_iterable,
    worker_or_worker_arr,
    n_jobs: int = None,
    argument_type: ArgumentPassing = ArgumentPassing.AS_SINGLE_ARG,
    bounded: bool = True,
    exception_behaviour: ExceptionBehaviour = ExceptionBehaviour.IGNORE,
    use_threads: bool = False,
    tqdm_class: tqdm_type = tqdm_auto,
    **kwargs
):
    """
     Internal function to create a parallel processing queue with progress tracking.

     This function should not be used directly. Instead, import pqdm from threads or processes.

     :param input_iterable: Iterable to be processed in parallel.
     :param worker_or_worker_arr: A single worker function/object or a list of worker functions/objects
     :param n_jobs: Number of worker processes/threads to create (ignored if worker_or_worker_arr is a list)
     :param argument_type: Type of argument passing. Defaults to ArgumentPassing.AS_SINGLE_ARG.
     :param bounded: Whether to use bounded execution mode: The bounded execution mode is memory efficient.
                     In the unbounded execution mode, all input items are loaded into memory.
     :param exception_behaviour: How to handle exceptions. Defaults to ExceptionBehaviour.IGNORE.
     :param use_threads: Whether to use threads instead of processes. Defaults to False.
     :param tqdm_class: The tqdm class to use for progress tracking. Defaults to tqdm_auto.
     :param kwargs: Additional keyword arguments for mtasklite.Pool and tqdm. Do not include arguments,
                    which this function includes explicitly!

     :return: A CustomContextManager instance combining tqdm and pool functionality.
     :raises Exception: Several arguments mtasklite.Pool, e.g., n_jobs, are explict arguments of this function.
                        If they are specified in kwargs, an exception will be thrown.
     """
    add_pool_kwargs, tqdm_kwargs = divide_kwargs(kwargs, Pool)
    for arg in add_pool_kwargs:
        if arg in NO_EXPLICIT_POOL_KWARGS:
            raise Exception(f'Do not specify Pool argument {arg} as kwarg!')

    pool_obj = Pool(worker_or_worker_arr=worker_or_worker_arr, n_jobs=n_jobs, use_threads=use_threads,
                           bounded=bounded, argument_type=argument_type, exception_behavior=exception_behaviour,
                           **add_pool_kwargs)(input_iterable)
    tqdm_obj = tqdm_class(pool_obj, **tqdm_kwargs)
    return CustomContextManager(tqdm_obj, pool_obj)