from mtasklite.constants import ArgumentPassing
from mtasklite.processes import pqdm
from mtasklite.utils import current_function_name
from mtasklite import Pool


def ret_args(a, b, c):
    return a, b, c


def ret_single_arg(a):
    return a


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
    input = [1, 2, 3, 4]

    for use_threads in [False, True]:
        with Pool(ret_single_arg, 4, use_threads=use_threads) as pbar:
            result = pbar(input)
            assert not result.parent_obj.exited, \
                f'Unexpected exit status before leaving with: {result.parent_obj.exited}'
        assert result.parent_obj.exited, \
            f'Unexpected exit status after leaving with: {result.parent_obj.exited}'

        pbar = Pool([ret_single_arg] * 4, use_threads=use_threads)
        result = pbar(input)
        assert not result.parent_obj.exited, \
            f'Unexpected exit status when context manager is not used: {result.parent_obj.exited}'


def test_misc_1():
    try:
        test_exited_1()
    except Exception as e:
        print('Unexpected exception in test_exited_1:', e)
        return False

    try:
        test_single_arg()
    except Exception as e:
        print('Unexpected exception in test_single_arg:', e)
        return False

    try:
        test_args(ArgumentPassing.AS_ARGS)
        test_args(ArgumentPassing.AS_KWARGS)
    except Exception as e:
        print('Unexpected exception in test_args:', e)
        return False


    return True


