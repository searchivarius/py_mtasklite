import concurrent.futures
from time import sleep


import mtasklite.threads
from mtasklite.constants import ArgumentPassing, ExceptionBehaviour
from mtasklite.processes import pqdm
from mtasklite.utils import current_function_name, is_exception
from mtasklite import Pool
from mtasklite import delayed_init
from tqdm import tqdm

@delayed_init
class AlwaysThrows:
    def __call__(self, arg):
        raise Exception('AlwaysThrows')


def ret_args(a, b, c):
    return a, b, c


def ret_single_arg(a):
    return a

class DummyException(Exception):
    pass

@delayed_init
class SleeperThrowsOnce:
    def __init__(self, sleep_time):
        self.sleep_time = sleep_time
        self.thrown = False

    def __call__(self, arg):
        if not self.thrown:
            self.thrown = True
            raise DummyException
        else:
            sleep(self.sleep_time)

thrown_e = None


def test_queue_cleanup_after_exception_worker(sleep_time, n_items, n_workers):
    input_arr = [0] * n_items

    with pqdm(input_arr, SleeperThrowsOnce(sleep_time), n_workers,
                     bounded=False, # this is crucial to have it unbounded
                     exception_behaviour=ExceptionBehaviour.IMMEDIATE,
                     desc=f'Testing {current_function_name()}') as pbar:
        try:
            list(pbar)
        except DummyException as e:
            # Ignore DummyException
            pass

    assert pbar.pool_obj.parent_obj.exited,\
        f'Unexpected exit status after leaving with: {pbar.pool_obj.parent_obj.exited}'


def test_queue_cleanup_after_exception_1():
    # do not increase N much or else the unit test will take long time to terminate
    # **HOWEVER** we need N to be large enough:
    # In the case of NOT cleaning up the queue, we will wait no more than (N-N_WORKER) * SLEEP_TIME time.
    N_WORKERS = 4
    N = 20

    SLEEP_TIME = 0.1
    TIMEOUT_TIME = 2 * SLEEP_TIME
    assert N > 3 * N_WORKERS

    """
        We construct a test where bound == False, which will lead to loading all input into the queue.
        Then, we will use two workers:
        i. One just sleeps
        ii. Another throws an exception immediately.
    
        We will also have a very large number input items. Thus, if the queue is not cleaned up properly, we will wait
        very long time before the pool terminates.
        Then, we will stop the test after a timeout (much larger than sleep time). If the queue is cleaned up
        properly the workers should terminate swiftly after the first exception is generated.
    """
    executor = concurrent.futures.ThreadPoolExecutor()
    try:
        future = executor.submit(test_queue_cleanup_after_exception_worker,
                                 sleep_time=SLEEP_TIME,
                                 n_items=N,
                                 n_workers=N_WORKERS)
        # If the queue is not cleaned up, this will be an upper bound for the execution time
        future.result(timeout=TIMEOUT_TIME)
    except Exception as e:
        executor.shutdown(wait=False)
        raise e
    executor.shutdown()


def test_exceptions(exception_behavior: ExceptionBehaviour):
    N = 16
    N_JOBS = 4

    input_arr = [()] * N

    global thrown_e

    for use_threads in tqdm([False, True],
                        desc=f'Testing {current_function_name()} with {exception_behavior}'):
        with Pool([AlwaysThrows()] * N_JOBS,
                  argument_type='args', # also testing conversion from string to an ArgumentPassing type
                  use_threads=use_threads,
                  exception_behavior=exception_behavior) as pbar:
            try:
                thrown_e = None
                result = pbar(input_arr)
                assert len(result) == N
                for e in result:
                    assert is_exception(e)

            except Exception as e:
                thrown_e = e
            if ExceptionBehaviour == ExceptionBehaviour.IMMEDIATE:
                assert thrown_e is not None
                assert type(thrown_e) == Exception
                assert is_exception(thrown_e.args[0])
            if ExceptionBehaviour == ExceptionBehaviour.DEFERRED:
                assert thrown_e is not None
                assert type(thrown_e) == Exception
                except_arg1 = thrown_e.args[0]
                assert type(except_arg1) == list

                assert len(except_arg1) == N
                for e in except_arg1:
                    assert is_exception(e)


def test_single_arg():
    input_arr = list(range(20))

    # Here we also test the case of having more workers than inputs
    result = list(pqdm(input_arr, [ret_single_arg]*7,
                       argument_type=ArgumentPassing.AS_SINGLE_ARG,
                       desc=f'Testing {current_function_name()} '))

    assert len(result) == len(input_arr), f'Unexpected result size: {len(result)}'
    assert result == input_arr, f'Unexpected result: {result}'


def test_args(iterable_arg_passing: ArgumentPassing):
    input_dict = {
        'a': 1,
        'b': 2,
        'c': 3
    }
    if iterable_arg_passing == ArgumentPassing.AS_ARGS:
        input_arr = [list(input_dict.values())]
    elif iterable_arg_passing == ArgumentPassing.AS_KWARGS:
        input_arr = [input_dict]
    else:
        raise Exception(f'Unsupported argument passing type: {iterable_arg_passing}')

    # Here we also test the case of having more workers than inputs
    result = list(pqdm(input_arr, [ret_args]*4,
                       argument_type=iterable_arg_passing,
                       desc=f'Testing {current_function_name()} with {iterable_arg_passing}'))
    assert len(result) == 1, f'Unexpected result size: {len(result)}'
    out_tuple = tuple(input_dict.values())
    assert result[0] == out_tuple, f'Unexpected result tuple: {result[0]}'


def test_exited_1():
    input_arr = [1, 2, 3, 4]

    for use_threads in tqdm([False, True], desc=f'Testing {current_function_name()}'):
        with Pool(ret_single_arg, 4, use_threads=use_threads) as pbar1:
            result = pbar1(input_arr)
            assert not result.parent_obj.exited, \
                f'Unexpected exit status before leaving with: {result.parent_obj.exited}'
        assert result.parent_obj.exited, \
            f'Unexpected exit status after leaving with: {result.parent_obj.exited}'

        if use_threads:
            pqdm_func = mtasklite.threads.pqdm
        else:
            pqdm_func = mtasklite.processes.pqdm

        with pqdm_func(input_arr, ret_single_arg, 4) as pbar2:
            assert not pbar2.pool_obj.parent_obj.exited, \
                f'Unexpected exit status after leaving with: {pbar2.pool_obj.parent_obj.exited}'

        assert pbar2.pool_obj.parent_obj.exited, \
            f'Unexpected exit status after leaving with: {pbar2.pool_obj.parent_obj.exited}'

        pbar3 = Pool([ret_single_arg] * 4, use_threads=use_threads)
        result = pbar3(input_arr)
        list(result) # forces reading and terminating the workers
        # despite workers are terminated the __exit__ function was not called
        assert not result.parent_obj.exited, \
            f'Unexpected exit status when context manager is not used: {result.parent_obj.exited}'


def test_exited_2():
    input_arr = [1, 2, 3, 4]

    # Test termination even though the input is not read
    for use_threads in tqdm([False, True], desc=f'Testing {current_function_name()}'):
        with Pool(ret_single_arg, 4, use_threads=use_threads) as pbar:
            pass


def test_misc_1():
    try:
        test_queue_cleanup_after_exception_1()
    except Exception as e:
        print('Unexpected exception in test_queue_cleanup_after_exception_1:', type(e), e)
        return False

    try:
        test_exited_1()
    except Exception as e:
        print('Unexpected exception in test_exited_1:', type(e), e)
        return False

    try:
        test_exited_2()
    except Exception as e:
        print('Unexpected exception in test_exited_1:', type(e), e)
        return False

    try:
        test_exceptions(ExceptionBehaviour.DEFERRED)
        test_exceptions(ExceptionBehaviour.IMMEDIATE)
        test_exceptions(ExceptionBehaviour.IGNORE)
    except Exception as e:
        print('Unexpected exception in test_exceptions:', type(e), e)
        return False

    try:
        test_single_arg()
    except Exception as e:
        print('Unexpected exception in test_single_arg:', type(e), e)
        return False

    try:
        test_args(ArgumentPassing.AS_ARGS)
        test_args(ArgumentPassing.AS_KWARGS)
    except Exception as e:
        print('Unexpected exception in test_args:', type(e), e)
        return False

    return True
