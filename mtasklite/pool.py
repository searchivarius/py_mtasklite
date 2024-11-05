import concurrent.futures
import multiprocess as mp
import inspect
import logging

from heapq import heappush, heappop

from .constants import ExceptionBehaviour, ArgumentPassing
from .delayed_init import ShellObject

from .utils import is_sized_iterator, is_exception


def is_valid_worker(worker):
    return inspect.isfunction(worker) or type(worker) == ShellObject,


class WorkerWrapper:
    def __init__(self, worker, timeout):
        self.worker = worker
        self.timeout = timeout

    def __call__(self, in_queue, out_queue, argument_type: ArgumentPassing):

        with concurrent.futures.ThreadPoolExecutor() as executor:
            while True:
                packed_arg = in_queue.get()
                if packed_arg is None:
                    break

                obj_id, worker_arg = packed_arg

                # If a worker is an object with a delayed initialization (inside a shell object),
                # then it will be created the first time it is used here.
                try:
                    if argument_type == ArgumentPassing.AS_KWARGS:
                        future = executor.submit(self.worker, **worker_arg)
                        ret_val = future.result(timeout=self.timeout)
                    elif argument_type == ArgumentPassing.AS_ARGS:
                        future = executor.submit(self.worker, *worker_arg)
                        ret_val = future.result(timeout=self.timeout)
                    elif argument_type == ArgumentPassing.AS_SINGLE_ARG:
                        future = executor.submit(self.worker, worker_arg)
                        ret_val = future.result(timeout=self.timeout)
                    else:
                        raise Exception(f'Invalid argument passing type: {argument_type}')
                except Exception as e:
                    ret_val = e

                out_queue.put((obj_id, ret_val))

            #
            # This resource clean-up is key. Quite interesting, we pass test_queue_cleanup_after_exception_worker
            # which checks termination due to an exception (with 'immediate') in the unbounded model
            # Yet on some real tasks, the function __call_ terminates properly, but the process does not finish
            # due to queue threads being active.
            #
            in_queue.cancel_join_thread()
            out_queue.cancel_join_thread()



class SortedOutputHelper:
    """
        The processed results may come in (somewhat) unordered, but we need to output them using the original order.
        This class maintains a priority queue to achieve this. An important assumption: all objects will be
        enumerated from 0 to <number of objects - 1> without gaps and repetitions.
    """
    def __init__(self):
        self.last_obj_out = -1
        self.out_queue = []

    def add_obj(self, obj_id, obj_ref):
        heappush(self.out_queue, (obj_id, obj_ref))

    def yield_results(self):
        while self.out_queue and self.out_queue[0][0] == self.last_obj_out + 1:
            self.last_obj_out, result = heappop(self.out_queue)
            yield result

    def empty(self):
        return not self.out_queue


class WorkerPoolResultGenerator:
    def __init__(self, parent_obj, input_iterable,
                 bounded,
                 is_unordered,
                 chunk_size, chunk_prefill_ratio):
        self.parent_obj = parent_obj
        self.input_iter = iter(input_iterable)
        self.is_unordered = is_unordered
        self.bounded = bounded
        self.chunk_size = chunk_size
        self.chunk_prefill_ratio = chunk_prefill_ratio

        assert self.chunk_size >= 1
        assert self.chunk_prefill_ratio >= 1

        # If the length is None, then TQDM will not know the total length and will not display the progress bar:
        # See __len__ function https://github.com/tqdm/tqdm/blob/master/tqdm/std.py
        if is_sized_iterator(input_iterable):
            self._length = len(input_iterable)  # Store the length of the iterable
        else:
            self._length = None
        self._iterator = self._generator()  # Create the generator

    def __len__(self):
        return self._length

    def __iter__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.parent_obj.__exit__(exc_type, exc_val, exc_tb)

    def __next__(self):
        return next(self._iterator)

    def _generator(self):
        submitted_qty = 0
        received_qty = 0

        assert type(self.chunk_size) == int
        if self.is_unordered:
            assert type(self.chunk_prefill_ratio) == int and self.chunk_prefill_ratio >= 1
            curr_batch_size = self.chunk_size * self.chunk_prefill_ratio
        else:
            curr_batch_size = self.chunk_size

        finished_input = False

        exceptions_arr = []

        sorted_out_helper = SortedOutputHelper()

        while not finished_input or received_qty < submitted_qty:
            try:
                curr_submit_qty = 0
                while True:
                    self.parent_obj.in_queue.put((submitted_qty, next(self.input_iter)))
                    assert self._length is None or submitted_qty < self._length
                    submitted_qty += 1
                    curr_submit_qty += 1
                    if self.bounded and curr_submit_qty >= curr_batch_size:
                        break
            except StopIteration:
                finished_input = True

            curr_batch_size = self.chunk_size
            left_qty = submitted_qty - received_qty

            for k in range(min(self.chunk_size, left_qty)):
                obj_id, result = self.parent_obj.out_queue.get()
                if is_exception(result):
                    if self.parent_obj.exception_behavior == ExceptionBehaviour.IMMEDIATE:
                        # Cleaning the input queue (else in unbounded mode we have to wait for all other tasks to finish)
                        self.clean_input_queue()
                        self.parent_obj._close()

                        raise result
                    elif self.parent_obj.exception_behavior == ExceptionBehaviour.DEFERRED:
                        exceptions_arr.append(result)
                    else:
                        # If exception is ignored it will be returned to the end user
                        assert self.parent_obj.exception_behavior == ExceptionBehaviour.IGNORE

                if self.is_unordered:
                    yield result
                else:
                    sorted_out_helper.add_obj(obj_id, result)
                    for result in sorted_out_helper.yield_results():
                        yield result

                assert received_qty < submitted_qty
                assert self._length is None or received_qty < self._length
                # We update this counter after receiving an element from the queue rather than after
                # returning/yielding it. If the priority queue is not empty after all elements are processed
                # and received, we will still empty it afer exiting the outer loop.
                received_qty += 1

            for result in sorted_out_helper.yield_results():
                yield result

        for result in sorted_out_helper.yield_results():
            yield result

        assert sorted_out_helper.empty(), \
            f'Logic error, the output queue should be empty at this point, but it has {len(out_queue)} elements'

        self.parent_obj._close()
        if exceptions_arr:
            raise Exception(*exceptions_arr)

    def clean_input_queue(self):
        try:
            while not self.parent_obj.in_queue.empty():
                # Some small non-zero timeout is fine
                self.parent_obj.in_queue.get(1e-6)
        except:
            pass


class Pool:
    """
     A class representing a pool of workers for parallel processing.

     This class manages a pool of worker processes or threads that can execute tasks in parallel.
     It supports both bounded and unbounded execution modes, stateless and stateful workers. Moreover,
     it can handle different argument passing strategies and exception behaviors.
    """
    def __enter__(self):
        return self

    def __call__(self, input_iterable):
        """
        Call the Pool object as a function to process the input iterable.

        :param input_iterable: An iterable containing inputs to be processed
        :return: A generator yielding results from the worker pool. This generator is also a context manager.
        :rtype: :class:`WorkerPoolResultGenerator`
        """
        assert self.chunk_size >= 1
        assert self.chunk_prefill_ratio >= 1

        return WorkerPoolResultGenerator(parent_obj=self, input_iterable=input_iterable,
                                         is_unordered=self.is_unordered, bounded=self.bounded,
                                         chunk_size=self.chunk_size,
                                         chunk_prefill_ratio=self.chunk_prefill_ratio)

    def __init__(self, worker_or_worker_arr,
                 n_jobs: int = None,
                 argument_type: ArgumentPassing = ArgumentPassing.AS_SINGLE_ARG,
                 exception_behavior: ExceptionBehaviour = ExceptionBehaviour.IMMEDIATE,
                 bounded: bool = True,
                 chunk_size: int = None, chunk_prefill_ratio: int = None,
                 is_unordered: bool = False,
                 use_threads: bool = False,
                 task_timeout: float = None,
                 join_timeout: float = None):
        """
        Initialize the Pool object with the given parameters.

        :param worker_or_worker_arr: A single worker function/object or a list of worker functions/objects
        :param n_jobs: Number of worker processes/threads to create (ignored if worker_or_worker_arr is a list)
        :param argument_type: Specifies how arguments are passed to workers
        :param exception_behavior: Defines how exceptions are handled
        :param bounded: Whether to use bounded execution mode: The bounded execution mode is memory efficient.
                        In the unbounded execution mode, all input items are loaded into memory.
        :param chunk_size: Size of chunk
        :param chunk_prefill_ratio: Prefill ratio for chunks
        :param is_unordered: Whether results can be returned in any order
        :param use_threads: Use threads instead of processes
        :param task_timeout: Timeout for individual tasks (currently discouraged)
        :param join_timeout: Timeout for joining workers
        """

        if task_timeout is not None:
            logging.warning("The task timeout features is deprecated."
                            " We currently cannot support task timeouts in the safe and cross-platform fashion")

        if type(worker_or_worker_arr) == list:
            assert n_jobs is None or n_jobs == len(worker_or_worker_arr), \
                'The number of workers does not match the worker array length (you can just set it None)!'
            self.num_workers = len(worker_or_worker_arr)
            for worker in worker_or_worker_arr:
                assert is_valid_worker(worker), \
                    f'A worker must be a function or an instance of a class with a delayed initialization, ' + \
                    ' not {type(worker)}!'
        else:
            assert n_jobs is not None, 'Specify the number of jobs or an array of worker objects!'
            assert is_valid_worker(worker_or_worker_arr), \
                f'A worker must be a function or an instance of a class with a delayed initialization,' + \
                ' not {type(function_or_worker_arr)}!'
            self.num_workers = max(int(n_jobs), 1)

        self.bounded = bounded
        self.chunk_prefill_ratio = max(int(chunk_prefill_ratio), 1) if chunk_prefill_ratio is not None else 2
        self.chunk_size = max(int(chunk_size), 1) if chunk_size is not None else self.num_workers

        self.exception_behavior = exception_behavior
        self.argument_type = argument_type
        self.is_unordered = is_unordered

        self.in_queue = mp.Queue()
        self.out_queue = mp.Queue()

        self.term_signal_sent = False
        self.exited = False

        self.use_threads = use_threads

        if self.use_threads:
            import threading
            process_class = threading.Thread
            daemon = None
        else:
            process_class = mp.Process
            daemon = True

        self.join_timeout = join_timeout
        self.task_timeout = task_timeout

        self.workers = []

        # Start worker processes
        for proc_id in range(self.num_workers):
            one_worker = worker_or_worker_arr[proc_id] \
                if type(worker_or_worker_arr) == list else worker_or_worker_arr
            one_proc = process_class(target=WorkerWrapper(one_worker, self.task_timeout),
                                     args=(self.in_queue, self.out_queue, self.argument_type),
                                     daemon=daemon)
            self.workers.append(one_proc)
            one_proc.start()

    def __exit__(self, type, value, tb):
        # Close will not do anything if the close function was called already
        self._close()
        # If a process "refuses" to stop it can be terminated.
        # Unfortunately, threads cannot be stopped / terminated in Python,
        # but they will die when the main process terminates.
        if not self.use_threads:
            for p in self.workers:
                p.terminate()
        self.exited = True

    def _join_workers(self):
        for p in self.workers:
            p.join(self.join_timeout)

    def _close(self):
        if not self.term_signal_sent:
            for _ in range(self.num_workers):
                self.in_queue.put(None)  # end-of-work signal: one per worker
            self._join_workers()
        self.term_signal_sent = True
