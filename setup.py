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
import src.cmdlr.info

if not sys.version_info >= (3, 4, 0):
    print("ERROR: You cannot install because python version < 3.4")
    sys.exit(1)

setup(
    name=src.cmdlr.info.PROJECT_NAME,
    version=src.cmdlr.info.VERSION,
    author=src.cmdlr.info.AUTHOR,
    author_email=src.cmdlr.info.AUTHOR_EMAIL,
    license=src.cmdlr.info.LICENSE,
    url=src.cmdlr.info.PROJECT_URL,
    description=src.cmdlr.info.DESCRIPTION,
    long_description='''''',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: SQL",
        "Environment :: Console",
        "Operating System :: POSIX :: Linux",
        "Topic :: Multimedia :: Graphics",
        "Topic :: System :: Archiving"],
    install_requires=['hanziconv'],
    setup_requires=[],
    package_dir={'': 'src'},
    packages=['cmdlr', 'cmdlr.analyzers'],
    entry_points={
        'console_scripts': ['cmdlr = cmdlr.cmdline:main'],
        'setuptools.installation': ['eggsecutable = cmdlr.cmdline:main']
        },
    keywords='comic download archive',
    )
