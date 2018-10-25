"""Cmdlr command line interface."""

import argparse
import textwrap
import sys

from . import info
from .conf import Config
from . import log
from . import cuiprint
from .amgr import AnalyzerManager
from .cmgr import ComicManager


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

    if args.skip_download_errors and not args.download:
        print('Please use -s options with -d options.', file=sys.stderr)
        sys.exit(1)

    if not args.urls and not sys.stdin.isatty():  # Get URLs from stdin
        args.urls = [url for url in sys.stdin.read().split() if url]

    elif len(sys.argv) == 1:
        print(('Please give at least one arguments or flags.'
               ' Use "-h" for more info.'),
              file=sys.stderr)
        sys.exit(1)

    return args


def main():
    """Command ui entry point."""
    args = _get_args()

    config = Config()
    config_filepaths = [Config.default_config_filepath]
    config.load_or_build(*config_filepaths)

    amgr = AnalyzerManager(config)

    if 'analyzer' in args:
        cuiprint.print_analyzer_info(amgr.get_analyzer_infos(), args.analyzer)
        return

    cuiprint.print_useless_urls(amgr, args.urls)

    cmgr = ComicManager(config, amgr)

    if args.list:
        url_to_comics = cmgr.get_url_to_comics(args.urls)
        cuiprint.print_comic_info(url_to_comics, detail_mode=args.urls)

    else:
        from .loopmgr import LoopManager

        lmgr = LoopManager(config.max_concurrent)

        ctrl = {
            'update_meta': args.update_meta,
            'download': args.download,
            'skip_download_errors': args.skip_download_errors
        }

        lmgr.start(config=config,
                   amgr=amgr,
                   cmgr=cmgr,
                   urls=args.urls,
                   ctrl=ctrl)
