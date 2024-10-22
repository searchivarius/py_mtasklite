# Contributing

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

If you are submitting a pull request, make sure to run the tests. Feel free to expand the tests as well:
```
# Install the code in the "debug" mode. Run from the root directory:
pip install -e .

# Run the test, feel free to use larger and smaller values of --n_elem as well:
python -m mtasklite.tests.run_all_unittests --n_elem 10
```