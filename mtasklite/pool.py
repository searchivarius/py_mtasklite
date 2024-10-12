import concurrent.futures
import multiprocessing as mp
import inspect

from typing import List, Type, Union

from .constants import ExceptionBehaviour, ArgumentPassing
from .delayed_init import ShellObject

from .utils import is_sized_iterator, is_exception


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


class WorkerPoolResultGenerator:
    def __init__(self, parent_obj, input_iterable,
                 is_unordered,
                 chunk_size, chunk_prefill_ratio):
        self.parent_obj = parent_obj
        self.input_iter = iter(input_iterable)
        self.is_unordered = is_unordered
        self.chunk_size = chunk_size
        self.chunk_prefill_ratio = chunk_prefill_ratio

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

        while not finished_input or received_qty < submitted_qty:
            try:
                for k in range(curr_batch_size):
                    self.parent_obj.in_queue.put((submitted_qty, next(self.input_iter)))
                    assert self._length is None or submitted_qty < self._length
                    submitted_qty += 1
            except StopIteration:
                finished_input = True

            curr_batch_size = self.chunk_size
            left_qty = submitted_qty - received_qty

            output_arr = []
            for k in range(min(self.chunk_size, left_qty)):
                obj_id, result = self.parent_obj.out_queue.get()
                if is_exception(result):
                    if self.parent_obj.exception_behavior == ExceptionBehaviour.IMMEDIATE:
                        self.parent_obj.close()
                        self.parent_obj.join_workers()
                        raise result
                    elif self.parent_obj.exception_behavior == ExceptionBehaviour.DEFERRED:
                        exceptions_arr.append(result)
                    else:
                        # If exception is ignored it will be returned to the end user
                        assert self.parent_obj.exception_behavior == ExceptionBehaviour.IGNORE

                if self.is_unordered:
                    yield result
                else:
                    output_arr.append((obj_id, result))

                assert received_qty < submitted_qty
                assert self._length is None or received_qty < self._length
                received_qty += 1

            output_arr.sort()
            for (obj_id, result) in output_arr:
                yield result

        self.parent_obj.close()
        self.parent_obj.join_workers()
        if exceptions_arr:
            raise Exception(*exceptions_arr)


class Pool:
    def __enter__(self):
        return self

    def __call__(self, input_iterable):
        if self.bounded:
            chunk_size = self.bounded_exec_chunk_size
            chunk_prefill_ratio = self.bounded_exec_chunk_prefill_ratio
        else:
            if is_sized_iterator(input_iterable):
                chunk_size = len(input_iterable)
                chunk_prefill_ratio = 1
            else:
                raise Exception('Unbounded execution requires length-providing iterables!')
        return WorkerPoolResultGenerator(parent_obj=self, input_iterable=input_iterable,
                                         is_unordered=self.is_unordered,
                                         chunk_size=chunk_size,
                                         chunk_prefill_ratio=chunk_prefill_ratio)

    def __init__(self, worker_or_worker_arr: Union[Type, List[ShellObject]],
                 n_jobs: int = None,
                 argument_type: ArgumentPassing = ArgumentPassing.AS_SINGLE_ARG,
                 exception_behavior: ExceptionBehaviour = ExceptionBehaviour.IMMEDIATE,
                 bounded: bool = True,
                 chunk_size: int = 100, chunk_prefill_ratio: int = 2,
                 is_unordered: bool = False,
                 use_threads: bool = False,
                 task_timeout: float = None,
                 join_timeout: float = None):

        if type(worker_or_worker_arr) == list:
            assert n_jobs is None or n_jobs == len(worker_or_worker_arr), \
                'The number of workers does not match the worker array length (you can just set it None)!'
            self.num_workers = len(worker_or_worker_arr)
            for worker in worker_or_worker_arr:
                assert inspect.isfunction(worker) or type(worker) == ShellObject, \
                    f'A worker must be a function or an instance of a class with a delayed initialization, ' + \
                    ' not {type(worker)}!'
        else:
            assert n_jobs is not None, 'Specify the number of jobs or an array of worker objects!'
            assert inspect.isfunction(worker_or_worker_arr) or type(worker_or_worker_arr) == ShellObject, \
                    f'A worker must be a function or an instance of a class with a delayed initialization,' + \
                    ' not {type(function_or_worker_arr)}!'
            self.num_workers = max(int(n_jobs), 1)

        self.bounded = bounded
        # chunk sizes will only be used for the bounded execution
        self.bounded_exec_chunk_prefill_ratio = max(int(chunk_prefill_ratio), 1)
        self.bounded_exec_chunk_size = int(chunk_size)

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
        self.close()
        # If a process "refuses" to stop it can be terminated.
        # Unfortunately, threads cannot be stopped / terminated in Python,
        # but they will die when the main process terminates.
        if not self.use_threads:
            for p in self.workers:
                p.terminate()
        self.exited = True

    def join_workers(self):
        for p in self.workers:
            p.join(self.join_timeout)

    def close(self):
        if not self.term_signal_sent:
            for _ in range(self.num_workers):
                self.in_queue.put(None)  # end-of-work signal: one per worker
        self.term_signal_sent = True
