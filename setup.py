#!/usr/bin/env python3
# coding=utf-8

#########################################################################
#  The MIT License (MIT)
#
#  Copyright (c) 2014~2015 CIVA LIN (林雪凡)
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files
#  (the "Software"), to deal in the Software without restriction, including
#  without limitation the rights to use, copy, modify, merge, publish,
#  distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so,
#  subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##########################################################################

import sys

from setuptools import setup
import src.cmdlr.cmdlr

if not sys.version_info >= (3, 4, 0):
    print("ERROR: You cannot install because python version should >= 3.4")
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
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
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
