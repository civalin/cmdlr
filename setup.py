#!/usr/bin/env python3
# coding=utf-8

import sys

from setuptools import setup
import src.cmdlr.cmdlr

if not sys.version_info >= (3, 3, 0):
    print("ERROR: You cannot install because python version should >= 3.3")
    sys.exit(1)

setup(
    name='cmdlr',
    version=src.cmdlr.cmdlr.VERSION,
    author='Civa Lin',
    author_email='larinawf@gmail.com',
    license='MIT',
    url='https://bitbucket.org/civalin/cmdlr',
    description="A script to download comic book from 8comic website",
    long_description='''''',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: System :: Archiving"],
    install_requires=[],
    setup_requires=[],
    package_dir={'': 'src'},
    packages=['cmdlr'],
    entry_points={
        'console_scripts': ['cmdlr = cmdlr.cmdlr:main'],
        'setuptools.installation': ['eggsecutable = cmdlr.cmdlr:main']
        },
    keywords='comic archive',
    )
