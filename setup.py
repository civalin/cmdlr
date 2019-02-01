#!/usr/bin/env python3

"""Install script."""

import sys

from setuptools import setup, find_packages

from src.cmdlr.info import PROJECT_NAME
from src.cmdlr.info import VERSION
from src.cmdlr.info import AUTHOR
from src.cmdlr.info import AUTHOR_EMAIL
from src.cmdlr.info import LICENSE
from src.cmdlr.info import PROJECT_URL
from src.cmdlr.info import DESCRIPTION


if not sys.version_info >= (3, 5, 3):
    print("ERROR: You cannot install due to python version < 3.5.3")

    sys.exit(1)


setup(
    name=PROJECT_NAME,
    version='.'.join(map(lambda x: str(x), VERSION)),

    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    url=PROJECT_URL,
    description=DESCRIPTION,
    long_description='''''',

    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Environment :: Console",
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Archiving"],

    install_requires=[
        'pyyaml >=4.2b1, <5',
        'aiohttp >=3, <4',
        'aiohttp_socks ==0.2',
        'voluptuous >=0.11.5, <0.12',
        'wcwidth == 0.1.7',
        'beautifulsoup4',
        'fake_useragent == 0.1.11',
    ],
    setup_requires=[],

    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,

    entry_points={
        'console_scripts': ['cmdlr = cmdlr.cmdline:main'],
    },
)
