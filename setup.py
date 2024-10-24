import sys
from os import path
from setuptools import setup, find_packages

PACKAGE_NAME='mtasklite'

sys.path.append(PACKAGE_NAME)
from version import __version__

print('Building version:', __version__)

curr_dir = path.abspath(path.dirname(__file__))
with open(path.join(curr_dir, 'README_SHORT.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=PACKAGE_NAME,
    version=__version__,
    description='An pqdm-compatible (almost) extension that supports stateful worker pools with both sized and unsized iterables.',
    project_urls={
        "Homepage": "https://github.com/searchivarius/py_mtasklite",
    },
    author='Leonid Boytsov',
    author_email='leo@boytsov.info',
    long_description=long_description,
    long_description_content_type='text/markdown',
    py_modules=[PACKAGE_NAME],
    install_requires=[l for l in open('requirements.txt') if not l.startswith('#') and not l.startswith('git+') and l.strip() != ''],
    license='Apache 2.0',
    python_requires='>=3.6',
    packages=find_packages()
)
