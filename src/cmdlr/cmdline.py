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
        cdb = cmdlr.cdb
        cpath = comicpath.get_cpath(cdb)

        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            description='Subscribe and download your comic books!')

        parser.add_argument(
            "-v", action="count", dest='verbose', default=0,
            help="Change output verbosity. E.g., -v, -vvv")

        parser.add_argument(
            '--version', action='version', version=info.VERSION)

        azg = parser.add_argument_group('Analyzers Management')

        azg.add_argument(
            '--azr', metavar='CODENAME', dest='analyzer_info',
            type=str, default=None,
            choices=[codename
                     for codename in sorted(cmdlr.am.all_analyzers.keys())],
            help='Show the analyzer\'s info message.')

        azg.add_argument(
            '--azr-custom', metavar='DATA', dest='analyzer_custom',
            type=str, default=None,
            help='Set analyzer\'s custom data.\n'
                 'Format: "codename/key1=value1,key2=value2"\n'
                 'Check analyzer\'s info message for more detail.')

        azg.add_argument(
            '--azr-list', dest='list_analyzers', action='store_true',
            help='List all analyzers and it is on/off.')

        azg.add_argument(
            '--azr-on', metavar='CODENAME', dest='analyzer_on',
            type=str, default=None,
            choices=[codename for codename
                     in sorted(cmdlr.am.disabled_analyzers.keys())],
            help='Turn on a analyzer.\n'
                 'By default all analyzers are enabled.')

        azg.add_argument(
            '--azr-off', metavar='CODENAME', dest='analyzer_off',
            type=str, default=None,
            choices=[codename for codename
                     in sorted(cmdlr.am.analyzers.keys())],
            help='Turn off a analyzer.\n')

        smg = parser.add_argument_group('Subscription Management')

        smg.add_argument(
            '-s', '--subscribe', metavar='COMIC',
            dest='subscribe_comic_entrys', type=str, nargs='+',
            help='Subscribe some comic books.\n'
                 'COMIC can be a url or comic_id.')

        smg.add_argument(
            '-u', '--unsubscribe', metavar='COMIC',
            dest='unsubscribe_comic_entrys', type=str, nargs='+',
            help='Unsubscribe some comic books.')

        smg.add_argument(
            '--no-backup', dest='no_backup', action='store_true',
            help='No backup downloaded files when unsubscribed.\n'
                 'Must using with "-u" option')

        smg.add_argument(
            '-l', '--list-info', dest='list_info', action='store_true',
            help='List all subscribed books info.')

        smg.add_argument(
            '-r', '--refresh', dest='refresh', action='store_true',
            help='Update all subscribed comic info.')

        smg.add_argument(
            '--as-new', metavar='COMIC',
            dest='as_new_comics', type=str, nargs='+',
            help='Set all volumes to "no downloaded" status.\n')

        downloading_group = parser.add_argument_group('Downloading')

        downloading_group.add_argument(
            '-d', '--download', dest='download', action='store_true',
            help='Download all no downloaded volumes.')

        downloading_group.add_argument(
            '--skip-exists', dest='skip_exists', action='store_true',
            help='Do not re-download when localfile exists.\n'
                 'Must using with "-d" option.')

        options_setting_group = parser.add_argument_group(
            'Setting Management')

        options_setting_group.add_argument(
            '--output-dir', metavar='DIR', dest='output_dir', type=str,
            help='Set comics directory.\n'
                 '(= "{}")'.format(cpath.output_dir))

        options_setting_group.add_argument(
            '--backup-dir', metavar='DIR', dest='backup_dir', type=str,
            help='Set comics backup directory. Unsubscribed comics will\n'
                 'be moved in here.\n'
                 '(= "{}")'.format(cpath.backup_dir))

        options_setting_group.add_argument(
            '--hanzi-mode', metavar="MODE", dest='hanzi_mode', type=str,
            choices=['trad', 'simp'],
            help='Select characters set converting rule for chinese.\n'
                 'Choice one of [%(choices)s]. (= "{}")'.format(
                     cdb.get_option('hanzi_mode')))

        options_setting_group.add_argument(
            '--move', dest='move', action='store_true',
            help='Move *ALL* real files in directories to new location.\n'
                 'Recommend use this with "--output-dir",\n'
                 '"--backup-dir" and "--hanzi-mode".')

        options_setting_group.add_argument(
            '--threads', metavar='NUM', dest='threads', type=int,
            choices=range(1, 11),
            help='Set download threads count. (= {})'.format(
                 cdb.get_option('threads')))

        options_setting_group.add_argument(
            '--cbz', dest='cbz', action='store_true',
            help='Toggle new incoming volumes to cbz format.'
                 ' (= {})'.format(cdb.get_option('cbz')))

        args = parser.parse_args()
        return args

    args = parse_args()
    return args


def main():
    def options_setting(cmdlr, args):
        def move_cpath(cmdlr):
            output_dir = cmdlr.cdb.get_option('output_dir')
            backup_dir = cmdlr.cdb.get_option('backup_dir')
            hanzi_mode = cmdlr.cdb.get_option('hanzi_mode')
            dst_cpath = comicpath.ComicPath(
                output_dir, backup_dir, hanzi_mode)
            cmdlr.move_cpath(dst_cpath)

        if args.analyzer_custom:
            cmdlr.am.set_custom_data(args.analyzer_custom)
        if args.analyzer_on or args.analyzer_off:
            if args.analyzer_on:
                cmdlr.am.on(args.analyzer_on)
            if args.analyzer_off:
                cmdlr.am.off(args.analyzer_off)
            cmdlr.am.print_analyzers_list()
        if args.threads is not None:
            cmdlr.cdb.set_option('threads', args.threads)
            print('Thread count: {}'.format(cmdlr.cdb.get_option('threads')))
        if args.cbz:
            cmdlr.cdb.set_option('cbz', not cmdlr.cdb.get_option('cbz'))
            print('Cbz mode: {}'.format(cmdlr.cdb.get_option('cbz')))

        if args.output_dir or args.backup_dir or args.hanzi_mode:
            if args.output_dir:
                cmdlr.cdb.set_option('output_dir', args.output_dir)
                print('Output directory: {}'.format(
                    cmdlr.cdb.get_option('output_dir')))
            if args.backup_dir:
                cmdlr.cdb.set_option('backup_dir', args.backup_dir)
                print('Backup directory: {}'.format(
                    cmdlr.cdb.get_option('backup_dir')))
            if args.hanzi_mode:
                cmdlr.cdb.set_option('hanzi_mode', args.hanzi_mode)
                print('Chinese charactors mode: {}'.format(
                    cmdlr.cdb.get_option('hanzi_mode')))
            if args.move:
                move_cpath(cmdlr)
            sys.exit(0)
        elif args.move:
            print('Warning: The "--move" are useless without\n'
                  ' "--output-dir", "--backup-dir" or "--hanzi-mode".')

    def subscription_management(cmdlr, args):
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

    def print_information(cmdlr, args):
        if args.list_analyzers:
            cmdlr.am.print_analyzers_list()
        if args.analyzer_info:
            cmdlr.am.print_analyzer_info(args.analyzer_info)
        if args.list_info:
            cmdlr.list_info(args.verbose + 1)

    cdb = comicdb.ComicDB(dbpath=os.path.expanduser(DBPATH))
    cmdlr = comicdownloader.ComicDownloader(cdb)
    args = get_args(cmdlr)

    options_setting(cmdlr, args)
    cmdlr = comicdownloader.ComicDownloader(cdb)  # refresh
    subscription_management(cmdlr, args)
    print_information(cmdlr, args)
