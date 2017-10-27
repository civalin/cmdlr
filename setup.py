#!/usr/bin/env python3

"""Install script."""

import sys

from setuptools import setup, find_packages
import src.cmdlr.info

if not sys.version_info >= (3, 5, 0):
    print("ERROR: You cannot install because python version < 3.5")
    sys.exit(1)

setup(
    name=src.cmdlr.info.PROJECT_NAME,
    version='.'.join(map(lambda x: str(x), src.cmdlr.info.VERSION)),
    author=src.cmdlr.info.AUTHOR,
    author_email=src.cmdlr.info.AUTHOR_EMAIL,
    license=src.cmdlr.info.LICENSE,
    url=src.cmdlr.info.PROJECT_URL,
    description=src.cmdlr.info.DESCRIPTION,
    long_description='''''',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Environment :: Console",
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Archiving"],
    install_requires=[
        'pyyaml >=3, <4',
        'aiohttp >=2, <3',
        'voluptuous',
        'wcwidth',
        'lxml >=3.8, <4',
        'beautifulsoup4',
        'pyexecjs >=1.4.0, <2',
        ],
    setup_requires=[],
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    entry_points={
        'console_scripts': ['cmdlr = cmdlr.cui:main'],
        'setuptools.installation': ['eggsecutable = cmdlr.cui:main']
        },
    keywords='comic download archive',
    )
