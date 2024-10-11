import platform
import multiprocessing


def is_sized_iterator(input_iterable):
    return hasattr(input_iterable, '__len__')


def is_exception(result):
    return isinstance(result, Exception)


def set_process_start_method():
    os_name = platform.system().lower()
    if 'windows' in os_name:
        multiprocessing.set_start_method('spawn')
    else:
        multiprocessing.set_start_method('fork')
