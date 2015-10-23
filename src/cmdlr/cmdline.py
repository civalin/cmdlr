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


import os
import sys
import argparse

from . import comicdownloader
from . import comicdb
from . import comicpath
from . import info


DBPATH = '~/.cmdlr.db'


def get_args(cmdlr):
    def parse_args():
        def parser_setting():
            parser = argparse.ArgumentParser(
                formatter_class=argparse.RawTextHelpFormatter,
                description='Subscribe and download your comic books!')

            parser.add_argument(
                "-v", action="count", dest='verbose', default=0,
                help="Change output verbosity. E.g., -v, -vvv")

            parser.add_argument(
                '--version', action='version', version=info.VERSION)

            return parser

        def azr_parser_setting(subparsers):
            azrparser = subparsers.add_parser(
                'azr',
                formatter_class=argparse.RawTextHelpFormatter,
                help='Listing and custom any analyzers',
                description='Usually you don\'t need to access the following '
                            'function.\n'
                            'But if some analyzers bother you, you '
                            'can view some detail and turn it off\n'
                            'in here.')

            all_analyzers_list = [codename for codename in sorted(
                cmdlr.am.all_analyzers.keys())]

            azrparser.add_argument(
                '-l', '--list', dest='list_analyzers', action='store_true',
                help='List all analyzers and checking they are on or off.')

            azrparser.add_argument(
                '-i', '--info', metavar='CODENAME', dest='analyzer_info',
                type=str, default=None,
                choices=all_analyzers_list,
                help='Show the analyzer\'s info message.')

            azrparser.add_argument(
                '--on', metavar='CODENAME', dest='analyzer_on',
                type=str, default=None,
                choices=all_analyzers_list,
                help='Turn on a analyzer.\n'
                     'By default all analyzers are enabled.')

            azrparser.add_argument(
                '--off', metavar='CODENAME', dest='analyzer_off',
                type=str, default=None,
                choices=all_analyzers_list,
                help='Turn off a analyzer.\n')

            azrparser.add_argument(
                '--custom', metavar='DATA', dest='analyzer_custom',
                type=str, default=None,
                help='Set analyzer\'s custom data.\n'
                     'Format: "codename/key1=value1,key2=value2"\n'
                     'Check analyzer\'s info message (-i) for more detail.')

        def opt_parser_setting(subparsers):
            cpath = comicpath.get_cpath(cmdlr.cdb)

            optparser = subparsers.add_parser(
                'opt',
                formatter_class=argparse.RawTextHelpFormatter,
                help='Tweaks option like output directory and other things',
                description=None)

            optparser.add_argument(
                '-l', '--list', dest='list_options', action='store_true',
                help='List all options values.')

            optparser.add_argument(
                '-o', '--output-dir', metavar='DIR', dest='output_dir',
                type=str,
                help='Set comics directory.\n'
                     '(= "{}")'.format(cpath.output_dir))

            optparser.add_argument(
                '-b', '--backup-dir', metavar='DIR', dest='backup_dir',
                type=str,
                help='Set comics backup directory. Unsubscribed comics\n'
                     'will be moved in here.\n'
                     '(= "{}")'.format(cpath.backup_dir))

            optparser.add_argument(
                '--hanzi-mode', metavar="MODE", dest='hanzi_mode', type=str,
                choices=['trad', 'simp'],
                help='Select characters set converting rule for chinese.\n'
                     'Choice one of [%(choices)s]. (= "{}")'.format(
                         cmdlr.cdb.get_option('hanzi_mode')))

            optparser.add_argument(
                '--move', dest='move', action='store_true',
                help='Move *ALL* files in directories to new location.\n'
                     'Recommend use this with "--output-dir",\n'
                     '"--backup-dir" and "--hanzi-mode".')

            optparser.add_argument(
                '-t', '--threads', metavar='NUM', dest='threads', type=int,
                choices=range(1, 11),
                help='Set download threads count. (= {})'.format(
                     cmdlr.cdb.get_option('threads')))

            optparser.add_argument(
                '--cbz', dest='cbz', action='store_true',
                help='Toggle new incoming volumes to cbz format.'
                     ' (= {})'.format(cmdlr.cdb.get_option('cbz')))

        def subscription_group_setting(parser):
            subscription_group = parser.add_argument_group('## Subscription')

            subscription_group.add_argument(
                '-s', '--subscribe', metavar='COMIC',
                dest='subscribe_comic_entrys', type=str, nargs='+',
                help='Subscribe some comic books.\n'
                     'COMIC can be a url or comic_id.')

            subscription_group.add_argument(
                '-u', '--unsubscribe', metavar='COMIC',
                dest='unsubscribe_comic_entrys', type=str, nargs='+',
                help='Unsubscribe some comic books.')

            subscription_group.add_argument(
                '--no-backup', dest='no_backup', action='store_true',
                help='No backup downloaded files when unsubscribed.\n'
                     'Must using with "-u" option')

            subscription_group.add_argument(
                '-l', '--list-info', dest='list_info', action='store_true',
                help='List all subscribed books info.')

            subscription_group.add_argument(
                '-r', '--refresh', dest='refresh', action='store_true',
                help='Update all subscribed comic info.')

            subscription_group.add_argument(
                '--as-new', metavar='COMIC',
                dest='as_new_comics', type=str, nargs='+',
                help='Set all volumes to "no downloaded" status.\n')

        def downloading_group_setting(parser):
            downloading_group = parser.add_argument_group('## Downloading')

            downloading_group.add_argument(
                '-d', '--download', dest='download', action='store_true',
                help='Download all no downloaded volumes.')

            downloading_group.add_argument(
                '--skip-exists', dest='skip_exists', action='store_true',
                help='Do not re-download when localfile exists.\n'
                     'Must using with "-d" option.')

        parser = parser_setting()
        subparsers = parser.add_subparsers(
            title='## Sub Commands ##',
            help='Try "-h" to get help message and exit.\n'
                 '(E.g., "%(prog)s azr -h")')
        azr_parser_setting(subparsers)
        opt_parser_setting(subparsers)
        subscription_group_setting(parser)
        downloading_group_setting(parser)

        args = parser.parse_args()
        return args

    args = parse_args()
    return args


def main():
    def azr_cmds_process(cmdlr, args):
        if 'list_analyzers' not in args:
            return
        if args.analyzer_custom:
            cmdlr.am.set_custom_data(args.analyzer_custom)
        if args.analyzer_on or args.analyzer_off:
            if args.analyzer_on:
                cmdlr.am.on(args.analyzer_on)
            if args.analyzer_off:
                cmdlr.am.off(args.analyzer_off)
            cmdlr.am.print_analyzers_list()
        if args.list_analyzers:
            cmdlr.am.print_analyzers_list()
        if args.analyzer_info:
            cmdlr.am.print_analyzer_info(args.analyzer_info)

    def opt_cmds_process(cmdlr, args):
        def move_cpath(cmdlr):
            output_dir = cmdlr.cdb.get_option('output_dir')
            backup_dir = cmdlr.cdb.get_option('backup_dir')
            hanzi_mode = cmdlr.cdb.get_option('hanzi_mode')
            dst_cpath = comicpath.ComicPath(
                output_dir, backup_dir, hanzi_mode)
            cmdlr.move_cpath(dst_cpath)

        def print_threads():
            print('Thread count:      {}'.format(
                cmdlr.cdb.get_option('threads')))

        def print_cbz_mode():
            print('Cbz mode:          {}'.format(cmdlr.cdb.get_option('cbz')))

        def print_output_dir():
            print('Output directory:  {}'.format(
                cmdlr.cdb.get_option('output_dir')))

        def print_backup_dir():
            print('Backup directory:  {}'.format(
                cmdlr.cdb.get_option('backup_dir')))

        def print_hanzi_mode():
            print('Hanzi mode:        {}'.format(
                cmdlr.cdb.get_option('hanzi_mode')))

        def print_all_options():
            print_output_dir()
            print_backup_dir()
            print_hanzi_mode()
            print_threads()
            print_cbz_mode()

        if 'output_dir' not in args:
            return

        if args.threads is not None:
            cmdlr.cdb.set_option('threads', args.threads)
            print_threads()
        if args.cbz:
            cmdlr.cdb.set_option('cbz', not cmdlr.cdb.get_option('cbz'))
            print_cbz_mode()
        if args.output_dir or args.backup_dir or args.hanzi_mode:
            if args.output_dir:
                cmdlr.cdb.set_option('output_dir', args.output_dir)
                print_output_dir()
            if args.backup_dir:
                cmdlr.cdb.set_option('backup_dir', args.backup_dir)
                print_backup_dir()
            if args.hanzi_mode:
                cmdlr.cdb.set_option('hanzi_mode', args.hanzi_mode)
                print_hanzi_mode()
            if args.move:
                move_cpath(cmdlr)
            sys.exit(0)
        elif args.move:
            print('Warning: The "--move" are useless without\n'
                  ' "--output-dir", "--backup-dir" or "--hanzi-mode".')
        if args.list_options:
            print_all_options()

    def subscription_process(cmdlr, args):
        if args.as_new_comics:
            for comic_entry in args.as_new_comics:
                cmdlr.as_new(comic_entry, args.verbose)
        if args.unsubscribe_comic_entrys:
            for comic_entry in args.unsubscribe_comic_entrys:
                cmdlr.unsubscribe(
                    comic_entry, not args.no_backup, args.verbose)
        elif args.no_backup:
            print('Warning: The "--no-backup" are useless without'
                  ' "--unsubscribe"')
        if args.subscribe_comic_entrys:
            for entry in args.subscribe_comic_entrys:
                cmdlr.subscribe(entry, args.verbose)
        if args.refresh:
            cmdlr.refresh_all(args.verbose + 1)
        if args.download:
            cmdlr.download_subscribed(args.skip_exists)
        elif args.skip_exists:
            print('Warning: The "--skip-exists" are useless without'
                  ' "--download".')
        if args.list_info:
            cmdlr.list_info(args.verbose + 1)

    cdb = comicdb.ComicDB(dbpath=os.path.expanduser(DBPATH))
    cmdlr = comicdownloader.ComicDownloader(cdb)
    args = get_args(cmdlr)

    azr_cmds_process(cmdlr, args)
    opt_cmds_process(cmdlr, args)
    subscription_process(cmdlr, args)
