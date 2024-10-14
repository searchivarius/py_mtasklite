#!/usr/bin/env python
import argparse
import sys

from mtasklite import set_process_start_method
from .test_stateless import test_stateless_1
from .test_stateful import test_stateful_1

def main(args):
    n_fail = 0
    n_fail += not test_stateful_1(args.n_elem)
    n_fail += not test_stateless_1(args.n_elem)

    print(f'Number of tests failed: {n_fail}')
    if n_fail > 0:
        print('Some failures!')
        sys.exit(1)
    else:
        print('Success!')


if __name__ == '__main__':
    set_process_start_method()

    parser = argparse.ArgumentParser()
    parser.add_argument('--n_elem', type=int, default=2000)

    main(parser.parse_args())