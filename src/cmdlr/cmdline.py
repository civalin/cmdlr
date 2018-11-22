"""Cmdlr command line interface."""

import argparse
import textwrap
import sys

from .info import DESCRIPTION
from .info import VERSION

from .conf import Config
from .log import init_logging
from .amgr import AnalyzerManager
from .cmgr import ComicManager
from .loopctrl import LoopManager

from .infoprint import print_analyzer_info
from .infoprint import print_not_matched_urls
from .infoprint import print_comic_info
from .infoprint import print_comic_json


def _parser_setting():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.fill(DESCRIPTION, 70))

    parser.add_argument(
        '--version', action='version',
        version='.'.join(map(lambda x: str(x), VERSION)))

    parser.add_argument(
        'urls', metavar='URL', type=str, nargs='*',
        help=('select which ones should processing.\n'
              'no one be given mean select all existing.\n'
              'perform subscription if a url hasn\'t been subscribed.'))

    parser.add_argument(
        '-m', dest='update_meta', action='store_true',
        help='update metadata')

    parser.add_argument(
        '-d', dest='download', action='store_true',
        help='download the volume files')

    parser.add_argument(
        '-s', dest='skip_errors', action='store_true',
        help='allow to skip partial downloading failed in a volume')

    parser.add_argument(
        '-l', '--list', dest='list', action='store_true',
        help='print subscriptions for human reading')

    parser.add_argument(
        '-j', '--json', dest='json', action='store_true',
        help='print subscriptions as json lines')

    parser.add_argument(
        '-a', metavar='NAME', dest='analyzer_name', nargs='?', type=str,
        default=argparse.SUPPRESS,
        help='print the analyzer\'s information')

    parser.add_argument(
        '-c', metavar='FILE', dest='extra_config_path', type=str,
        help=('assign a extra config file and merge in'),
    )

    parser.add_argument(
        '-C', action='store_true', dest='stop_default_config',
        help=('suppress the default config file:\n  {}'
              .format(Config.default_config_filepath)),
    )

    return parser


def _get_args():
    parser = _parser_setting()
    args = parser.parse_args()

    if args.skip_errors and not args.download:
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


def _get_config(args):
    config = Config()
    config_filepaths = []

    if args.stop_default_config is not True:
        config_filepaths.append(Config.default_config_filepath)

    if args.extra_config_path:
        config_filepaths.append(args.extra_config_path)

    config.load_or_build(*config_filepaths)

    return config


def main():
    """Command ui entry point."""
    args = _get_args()
    config = _get_config(args)

    init_logging(config.logging_dir, config.logging_level)

    amgr = AnalyzerManager(config)

    if 'analyzer_name' in args:
        print_analyzer_info(amgr, args.analyzer_name)

        return

    print_not_matched_urls(amgr, args.urls)

    cmgr = ComicManager(config, amgr)

    if args.list:
        print_comic_info(cmgr, urls=args.urls, detail_mode=args.urls)

    elif args.json:
        print_comic_json(cmgr, urls=args.urls)

    else:
        lmgr = LoopManager(config, amgr, cmgr)

        ctrl = {
            'update_meta': args.update_meta,
            'download': args.download,
            'skip_errors': args.skip_errors
        }

        lmgr.start(args.urls, ctrl)
