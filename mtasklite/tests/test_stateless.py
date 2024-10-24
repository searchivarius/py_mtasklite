from mtasklite import Pool

from mtasklite.constants import ArgumentPassing
from mtasklite.utils import current_function_name

from tqdm import tqdm


def square(a):
    return a*a


def run_generic_stateless_test(n_elem, n_jobs,
             use_pqdm_interface: bool,
             use_threads: bool,
             is_unordered: bool,
             use_unsized_iterable: bool,
             iterable_arg_passing: ArgumentPassing,
             chunk_size: int=1, chunk_prefill_ratio: int=2,
             is_bounded: bool=True):

    input_range = range(0, n_elem)
    if iterable_arg_passing == ArgumentPassing.AS_SINGLE_ARG:
        input_arr = list(input_range)
    elif iterable_arg_passing == ArgumentPassing.AS_ARGS:
        input_arr = [[e] for e in input_range]
    else:
        assert iterable_arg_passing == ArgumentPassing.AS_KWARGS, \
                                                            f'Unexpected argument passing type: {iterable_arg_passing}'
        input_arr = [{'a': e} for e in input_range]

    expected_sorted_result = [square(e) for e in input_range]

    def input_arr_generator():
        for e in input_arr:
            yield e

    if use_unsized_iterable:
        input_iterable = input_arr_generator()
    else:
        input_iterable = input_arr

    function_or_worker_arr = square
    if use_pqdm_interface:
        if use_threads:
            from mtasklite.threads import pqdm
        else:
            from mtasklite.processes import pqdm

        result = list(pqdm(input_iterable, function_or_worker_arr, n_jobs,
                        chunk_size=chunk_size, chunk_prefill_ratio=chunk_prefill_ratio,
                        argument_type=iterable_arg_passing,
                        is_unordered=is_unordered,
                        bounded=is_bounded,
                        disable=True)) # disable TQDM here
    else:
        with Pool(
            function_or_worker_arr, n_jobs,
            chunk_size=chunk_size, chunk_prefill_ratio=chunk_prefill_ratio,
            use_threads=use_threads,
            argument_type=iterable_arg_passing,
            is_unordered=is_unordered,
            bounded=is_bounded
        ) as pool:
            result = list(pool(input_iterable))

    assert len(result) == len(expected_sorted_result), f'Length different, returned: {len(result)}, expected {len(expected_sorted_result)}'

    if is_unordered:
        assert set(result) == set(expected_sorted_result), 'result set differ, is_unordered'
    else:
        if result != expected_sorted_result:
          import pdb ; pdb.set_trace()
        assert result == expected_sorted_result, 'result set differ, is_ordered'


def test_stateless_1(max_elem):
    kwarg_arr = []

    for use_threads in [False, True]:
        for is_unordered in [False, True]:
            for use_unsized_iterable in [False, True]:
                for iterable_arg_passing in [ArgumentPassing.AS_SINGLE_ARG,
                                             ArgumentPassing.AS_ARGS,
                                             ArgumentPassing.AS_KWARGS]:
                    for use_pqdm_interface in [False, True]:
                        # Importantly we also need to test empty inputs
                        for n_elem in range(0, max_elem):
                            for n_jobs in [1, 3, 4]:
                                if not use_unsized_iterable:
                                    kwarg_arr.append(dict(n_elem=n_elem, n_jobs=n_jobs,
                                                          use_pqdm_interface=use_pqdm_interface,
                                                          use_threads=use_threads,
                                                          is_unordered=is_unordered,
                                                          use_unsized_iterable=use_unsized_iterable,
                                                          iterable_arg_passing=iterable_arg_passing,
                                                          is_bounded=False))

                                for chunk_size in [1, 2, 4]:
                                    for chunk_prefill_ratio in [1, 2, 4]:
                                        kwarg_arr.append(dict(n_elem=n_elem, n_jobs=n_jobs,
                                                              use_pqdm_interface=use_pqdm_interface,
                                                              use_threads=use_threads,
                                                              is_unordered=is_unordered,
                                                              use_unsized_iterable=use_unsized_iterable,
                                                              iterable_arg_passing=iterable_arg_passing,
                                                              chunk_size=chunk_size, chunk_prefill_ratio=chunk_prefill_ratio))

        for kwargs in tqdm(kwarg_arr, f'Testing {current_function_name()}'):
            try:
                run_generic_stateless_test(**kwargs)
            except Exception as e:
                print('Unexpected exception:', type(e), e)
                print('Test function arguments:')
                print(kwargs)
                return False

        return True



