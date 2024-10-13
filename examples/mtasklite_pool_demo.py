#!/usr/bin/env python
import argparse
import multiprocessing as mp

from tqdm.auto import tqdm

from mtasklite import Pool, delayed_init, is_exception, set_process_start_method, ExceptionBehaviour, ArgumentPassing


def sample_expensive_calc_func(input_arg):
    """
        This is a useless yet expensive function that computes useless values,
        but takes relatively long time. We use an expensive function to
        simulate some real-world computation.

    :param input_arg:
    :return:
    """
    ret_val = input_arg
    for t in range(100_000):
        ret_val = (ret_val * ret_val) % 337
    return ret_val


@delayed_init
class SampleExpensiveCalcClassWorker:
    def __init__(self, proc_id, fire_exception_proc_id=None):
        print(f'Initialized process {mp.current_process()} passed ID = {proc_id} with fire_exception_proc_id: {fire_exception_proc_id}\n')
        self.proc_id = proc_id
        self.fire_exception_proc_id = fire_exception_proc_id

    def __call__(self, input_arg):
        if self.proc_id == self.fire_exception_proc_id:
            raise Exception("Rogue exception!")
        return sample_expensive_calc_func(input_arg)


def main(args):
    set_process_start_method()

    if args.iterable_arg_passing == ArgumentPassing.AS_SINGLE_ARG:
        input_arr = [k * 10 for k in range(args.num_lines)]
    elif args.iterable_arg_passing == ArgumentPassing.AS_ARGS:
        input_arr = [[k * 10] for k in range(args.num_lines)]
    else:
        assert args.iterable_arg_passing == ArgumentPassing.AS_KWARGS
        input_arr = [dict(input_arg=k * 10) for k in range(args.num_lines)]

    def input_arr_generator():
        for e in input_arr:
            yield e

    if args.use_unsized_iterable:
        input_iterable = input_arr_generator()
    else:
        input_iterable = input_arr

    tot_res = 0

    n_jobs = args.n_jobs
    print('Number of jobs:', n_jobs)
    print('Use stateless (function) worker?:', args.use_stateless_function_worker)
    print('Use threads?:', args.use_threads)
    print('Number of input items:', len(input_arr))
    print('Input iterable without __len__?', args.use_unsized_iterable)
    print('UN-ordered?:', args.is_unordered)

    if args.use_stateless_function_worker:
        function_or_worker_arr = sample_expensive_calc_func
    else:
        function_or_worker_arr = \
            [SampleExpensiveCalcClassWorker(proc_id, fire_exception_proc_id=args.fire_exception_proc_id)
             for proc_id in range(n_jobs)]

    with Pool(function_or_worker_arr, n_jobs,
              chunk_size=args.chunk_size, chunk_prefill_ratio=args.chunk_prefill_ratio,
              use_threads=args.use_threads,
              argument_type=args.iterable_arg_passing,
              is_unordered=args.is_unordered,
              bounded=not args.is_unbounded,
              exception_behavior=args.exception_behavior,
              join_timeout=1) as proc_pool:
        # just marking the type
        for result in tqdm(proc_pool(input_iterable)):
            if is_exception(result):
                print('Error:', result)
            else:
                tot_res += result

    print('Total:', tot_res)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--num_lines', type=int, default=2000)
    parser.add_argument('--chunk_size', type=int, default=100)
    parser.add_argument('--chunk_prefill_ratio', type=int, default=2)
    parser.add_argument('--n_jobs', type=int, default=mp.cpu_count())
    parser.add_argument('--is_unordered', action='store_true')
    parser.add_argument('--use_threads',  action='store_true')
    parser.add_argument('--is_unbounded', action='store_true')

    parser.add_argument('--fire_exception_proc_id', type=int, default=None,
                        help='Fire a "rogue" exception from the process with this ID')
    parser.add_argument('--use_stateless_function_worker',
                        action='store_true', help='Use a regular (stateless) function-based worker instead of a class')
    parser.add_argument('--use_unsized_iterable', action='store_true')

    parser.add_argument('--iterable_arg_passing', default=ArgumentPassing.AS_SINGLE_ARG,
                        choices=[ArgumentPassing.AS_SINGLE_ARG, ArgumentPassing.AS_ARGS, ArgumentPassing.AS_KWARGS])
    parser.add_argument('--exception_behavior', default=ExceptionBehaviour.IGNORE,
                        choices=[ExceptionBehaviour.DEFERRED, ExceptionBehaviour.IGNORE, ExceptionBehaviour.IMMEDIATE])

    args = parser.parse_args()
    main(args)
