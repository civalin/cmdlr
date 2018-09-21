"""Cmdlr command line interface."""

import argparse
import textwrap
import sys

from . import info
from . import config
from . import log
from . import cuiprint


def _parser_setting():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.fill(info.DESCRIPTION, 70))

    parser.add_argument(
        '--version', action='version',
        version='.'.join(map(lambda x: str(x), info.VERSION)))

    parser.add_argument(
        'urls', metavar='URL', type=str, nargs='*',
        help=('select some books which want to process.\n'
              'if no urls are given, select all subscribed books.\n'
              'if some urls haven\'t been subscribed,'
              ' subscrube these now.\n'
              'more process depend on which flags be given.'))

    parser.add_argument(
        '-m', '--update-meta', dest='update_meta', action='store_true',
        help='request update meta, not only when subscribe.')

    parser.add_argument(
        '-d', '--download', dest='download', action='store_true',
        help='download the volumes files.')

    parser.add_argument(
        '-s', '--skip-download-errors',
        dest='skip_download_errors', action='store_true',
        help=('generate volume files even if some images fetch failed.\n'
              'may cause incomplete volume files, so use carefully.\n'
              'must using with --download flag.'))

    parser.add_argument(
        '-f', '--force-download',
        dest='force_download', action='store_true',
        help=('refetch volume files even if it\'s already exists.\n'
              'must using with --download flag.'))

    parser.add_argument(
        '-o', '--output',
        dest='output_dirpath', metavar='DIR', type=str,
        help='temporary reassign the "dirs" in config file.')

    parser.add_argument(
        '-l', '--list', dest='list', action='store_true',
        help=('list exists comics info.\n'
              'also display extra data if URLs are given.\n'
              'this flag will prevent any current status change.'))

    parser.add_argument(
        '-a', dest='analyzer', nargs='?', type=str,
        default=argparse.SUPPRESS,
        help=('list all enabled analyzers.\n'
              'or print the detail if give a name.\n'))

    return parser


def _get_args():
    parser = _parser_setting()
    args = parser.parse_args()

    if args.force_download and not args.download:
        log.logger.critical('Please use -f options with -d options.')
        sys.exit(1)

    if args.skip_download_errors and not args.download:
        log.logger.critical('Please use -s options with -d options.')
        sys.exit(1)

    if not args.urls and not sys.stdin.isatty():  # Get URLs from stdin
        args.urls = [url for url in sys.stdin.read().split() if url]
    elif len(sys.argv) == 1 or (len(sys.argv) == 3 and args.output_dirpath):
        log.logger.critical('Please give at least one arguments or flags.'
                            ' Use "-h" for more info.')
        sys.exit(1)

    return args


def _get_coll_dirpaths(output_dirpath):
    if output_dirpath:
        return [output_dirpath]
    return config.get_all_dirs()


def main():
    """Command ui entry point."""
    args = _get_args()
    coll_dirpaths = _get_coll_dirpaths(args.output_dirpath)

    if args.list:
        cuiprint.print_comic_info(coll_dirpaths, args.urls)
    elif 'analyzer' in args:
        cuiprint.print_analyzer_info(args.analyzer)
    else:
        from . import core

        core.start(coll_dirpaths=coll_dirpaths,
                   urls=args.urls,
                   update_meta=args.update_meta,
                   download=args.download,
                   force_download=args.force_download,
                   skip_download_errors=args.skip_download_errors)
