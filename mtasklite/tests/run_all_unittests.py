#!/usr/bin/env python
import argparse
import sys

from mtasklite.tests.test_stateless import test_stateless_1
from mtasklite.tests.test_stateful import test_stateful_1
from mtasklite.tests.test_misc import test_misc_1


def main(args):
    n_fail = 0
    n_qty = 0

    n_fail += not test_misc_1() ; n_qty += 1
    n_fail += not test_stateful_1(args.n_elem) ; n_qty += 1
    n_fail += not test_stateless_1(args.n_elem) ; n_qty += 1

    print(f'Number of tests: {n_qty} failed: {n_fail}')
    if n_fail > 0:
        print('Some failures!')
        sys.exit(1)
    else:
        print('Success!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--n_elem', type=int, default=2000)

    main(parser.parse_args())
