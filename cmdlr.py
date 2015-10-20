#!/usr/bin/env python3

import pathlib

import src.cmdlr.cmdline as cmdline

cmdline.DBPATH = str(pathlib.Path(__file__).parent / 'testing.db')
cmdline.main()
