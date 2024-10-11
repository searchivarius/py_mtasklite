from typing import NamedTuple


class ArgumentPassing(NamedTuple):
    """
        A slightly modified version of pqdm constants
        https://github.com/niedakh/pqdm/blob/master//pqdm/constants.py
    """
    AS_SINGLE_ARG = 'single_arg'
    AS_ARGS = 'args'
    AS_KWARGS = 'kwargs'


class ExceptionBehaviour(NamedTuple):
    IGNORE = 'ignore'
    IMMEDIATE = 'immediate'
    DEFERRED = 'deferred'
