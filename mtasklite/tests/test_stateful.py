from mtasklite import Pool, delayed_init

from mtasklite.constants import ArgumentPassing
from mtasklite.utils import current_function_name

from tqdm import tqdm

@delayed_init
class Square:
    def __init__(self, worker_id):
        self.worker_id = worker_id

    def __call__(self, a):
        return self.worker_id, a*a


def run_generic_stateful_test(n_elem, n_jobs,
             use_threads: bool,
             is_unordered: bool,
             use_unsized_iterable: bool,
             iterable_arg_passing: ArgumentPassing,
             chunk_size: int = 1, chunk_prefill_ratio: int = 2,
             is_bounded: bool = True):

    input_range = range(0, n_elem)
    if iterable_arg_passing == ArgumentPassing.AS_SINGLE_ARG:
        input_arr = list(input_range)
    elif iterable_arg_passing == ArgumentPassing.AS_ARGS:
        input_arr = [[e] for e in input_range]
    else:
        assert iterable_arg_passing == ArgumentPassing.AS_KWARGS, \
                                                            f'Unexpected argument passing type: {iterable_arg_passing}'
        input_arr = [{'a': e} for e in input_range]

    expected_sorted_result = [e * e for e in input_range]

    def input_arr_generator():
        for e in input_arr:
            yield e

    if use_unsized_iterable:
        input_iterable = input_arr_generator()
    else:
        input_iterable = input_arr

    function_or_worker_arr = [Square(i) for i in range(n_jobs) ]

    with Pool(
        function_or_worker_arr, n_jobs,
        chunk_size=chunk_size, chunk_prefill_ratio=chunk_prefill_ratio,
        use_threads=use_threads,
        argument_type=iterable_arg_passing,
        is_unordered=is_unordered,
        bounded=is_bounded
    ) as pool:
        # Each input element is repeated n_jobs times in the input, but the
        # worker will ignore items assigned to a different worker_id and will return None
        result = []
        for worker_id, e in pool(input_iterable):
            assert worker_id >= 0 and worker_id < n_jobs, \
                f'Wrong worker ID received {worker_id} should be in he range [0, {n_jobs-1}]'
            result.append(e)

    assert len(result) == len(expected_sorted_result), f'Length different, returned: {len(result)}, expected {len(expected_sorted_result)}'

    if is_unordered:
        assert set(result) == set(expected_sorted_result), 'result set differ, is_unordered'
    else:
        assert result == expected_sorted_result, 'result set differ, is_ordered'


def test_stateful_1(max_elem):
    kwarg_arr = []

    for use_threads in [False, True]:
        for is_unordered in [False, True]:
            for use_unsized_iterable in [False, True]:
                for iterable_arg_passing in [ArgumentPassing.AS_SINGLE_ARG,
                                             ArgumentPassing.AS_ARGS,
                                             ArgumentPassing.AS_KWARGS]:
                    # Importantly we also need to test empty inputs
                    for n_elem in range(0, max_elem):
                        for n_jobs in [1, 3, 4]:
                            if not use_unsized_iterable:
                                kwarg_arr.append(dict(n_elem=n_elem, n_jobs=n_jobs,
                                                      use_threads=use_threads,
                                                      iterable_arg_passing=iterable_arg_passing,
                                                      is_unordered=is_unordered,
                                                      use_unsized_iterable=use_unsized_iterable,
                                                      is_bounded=False))

                            for chunk_size in [1, 2, 4]:
                                for chunk_prefill_ratio in [1, 2, 4]:
                                    kwarg_arr.append(dict(n_elem=n_elem, n_jobs=n_jobs,
                                                          use_threads=use_threads,
                                                          iterable_arg_passing=iterable_arg_passing,
                                                          is_unordered=is_unordered,
                                                          use_unsized_iterable=use_unsized_iterable,
                                                          chunk_size=chunk_size, chunk_prefill_ratio=chunk_prefill_ratio))

        for kwargs in tqdm(kwarg_arr, f'Testing {current_function_name()}'):
            try:
                run_generic_stateful_test(**kwargs)
            except Exception as e:
                print('Unexpected exception:', type(e), e)
                print('Test function arguments:')
                print(kwargs)
                return False

        return True



