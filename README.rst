cmdlr
################

``cmdlr`` is a extensible command line tool for download comic books
from online comic sites.

Install
=============

Make sure your python >= 3.4, then...

.. code:: bash

    pip3 install cmdlr

How to use
==========

Set Your Local Comics Directory
-------------------------------

.. code:: bash

    cmdlr --output-dir <DIR>


Default comics directory is ``~/comics``.

Subscribe a comic
-----------------

.. code:: bash

    cmdlr -s <COMIC>

The ``<COMIC>`` can be a comic_id or comic's url (the url usually is comic index page, but defined by analyzer independent).

Check current subscribed status
-------------------------------

.. code:: bash

    cmdlr -l

It will listing all information in database. If you want more detail, please combine `-v` option multiple time like...

.. code:: bash

    cmdlr -lv

or

.. code:: bash

    cmdlr -lvv

Download all your comics
-------------------------

.. code:: bash

    cmdlr -d

All "no downloaded volumes" will be downloaded into your's comics directory.

Check comic sites update
---------------------------

.. code:: bash

    cmdlr -r

    # or
    cmdlr -rd  # check updated then download

Subscription Database
==========================

You can backup database manually if you want.

.. code:: bash

    ~/.cmdlr.db

How to create a new analyzer plugin?
======================================

Very easy!

1. Clone ``cmdlr`` project from http://bitbucket.org/civalin/cmdlr.
2. Check ``src/cmdlr/comicanalyzer.py`` to learn what function you need to implement. And reference other analyzer plugin to create yours.
3. Put your ``.py`` file into ``src/cmdlr/analyzers`` directory.
4. Run ``./cmdlr.py`` to testing the plugin.
5. When you done, don't forget make a pull request to me. Thanks!

I recommend use the ``cmdlr.Downloader.save()`` & ``cmdlr.downloader.get()`` function to download data, but it is not necessary. you can choice any tools freely. Also, using any prefer tools to parsing data. like ``lxml``.

Happy hacking! :D

LICENSE
=========

MIT License

Copyright (c) 2014~2015 CIVA LIN

Changelog
=========

2.0.0
---------

Fully rewrite version

- Backend DB: ``tinydb`` -> ``sqlite``
- Collect more data.
- Remove search function.
- make it extensible.

1.1.0
---------

- Init release.
