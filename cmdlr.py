#!/usr/bin/env python3

import pathlib

import src.cmdlr.cmdlr as cmdlr

cmdlr.DBPATH = str(pathlib.Path(__file__).parent / 'testing.db')
cmdlr.main()
