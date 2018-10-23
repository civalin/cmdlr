#!/usr/bin/env python3
"""Cmdlr command ui starting script."""

import sys
import os


sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


import cmdlr.cmdline as cmdline  # NOQA


cmdline.main()
