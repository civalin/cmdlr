Freezing to cbz
################

``cmdlr`` is a command line tool for download comic books from 8comic.

Example
==============

Search comics
-------------

::

    cmdlr COMICNAME

you will got some comicname and ``COMIC_ID``.

Subscribe comics
----------------

::

    cmdlr -s COMIC_ID COMIC_ID ...

List all your subscribed::

    cmdlr -l

Unsubscribed::

    cmdlr -u COMIC_ID COMIC_ID ...

Check Subscribed Comic Update
-------------------------------

::

    cmdlr -r

Download All Subscribed
------------------------

::

    cmdlr -d

Install
=============

Make sure your python >= 3.3, then...

.. code:: bash

    pip3 install cmdlr

Subscription Database
==========================

User can backup the database manually if (s)he want.

.. code:: bash

    ~/.cmdlrdb

Changelog
=========

1.1.0
---------

- Init release.
