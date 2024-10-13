#!/usr/bin/env python
import argparse
from mtasklite import set_process_start_method
from .test_stateless import test_stateless_1


def main(args):
    n_fail = 0
    n_fail += not test_stateless_1(max_elem=10)

    print(f'Number of tests failed: {n_fail}')


if __name__ == '__main__':
    set_process_start_method()

    parser = argparse.ArgumentParser()
    parser.add_argument('--n_elem', type=int, default=2000)

    main(parser.parse_args())