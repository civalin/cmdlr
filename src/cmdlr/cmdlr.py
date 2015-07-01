#!/usr/bin/env python3

import urllib.request as UR
import urllib.error as UE
import re
import os
import concurrent.futures as CF
import argparse

import tinydb


VERSION = '1.0.0'


def get_html(url):
    response = UR.urlopen(url)
    html = response.read().decode('big5', errors='ignore')
    return html


def get_comic_index():
    list_url = "http://www.comicvip.com/comic/all.html"
    html = get_html(list_url)
    matches = re.finditer('<a href="/html/(\d*)\.html".*?>(.*?)</a>', html)
    data_list = [{'comic_id': int(match.group(1)),
                  'title': match.group(2)}
                 for match in matches]
    return data_list


def get_comic_metadata(comic_id):
    def get_comic_index_url(comic_id):
        return 'http://www.comicvip.com/html/{}.html'.format(comic_id)

    def get_one_page_url(comic_index_url):
        def get_random_cview_params(html):
            match = re.search(r"cview\('(.+?)',(\d+?)\)", html)
            return match.groups(1)

        def generate_one_page_url(one_page_url_fragment, catid):
            catid = int(catid)
            if catid in (4, 6, 12, 22):
                baseurl = "http://new.comicvip.com/show/cool-"
            elif catid in (1, 17, 19, 21):
                baseurl = "http://new.comicvip.com/show/cool-"
            elif catid in (2, 5, 7, 9):
                baseurl = "http://new.comicvip.com/show/cool-"
            elif catid in (10, 11, 13, 14):
                baseurl = "http://new.comicvip.com/show/best-manga-"
            elif catid in (3, 8, 15, 16, 18, 20):
                baseurl = "http://new.comicvip.com/show/best-manga-"

            fragment = one_page_url_fragment.replace(
                ".html", "").replace("-", ".html?ch=")
            return baseurl + fragment

        html = get_html(comic_index_url)
        one_page_url_fragment, catid = get_random_cview_params(html)
        return generate_one_page_url(one_page_url_fragment, catid)

    def get_comic_info(one_page_url):
        def get_title(html):
            match_title = re.search(r":\[(.*?)<font id=", html)
            title = match_title.group(1).strip()
            return title

        def get_comic_code(html):
            match_comic_code = re.search(r"var cs='(\w*)'", html)
            comic_code = match_comic_code.group(1)
            return comic_code

        def get_comic_id(html):
            match_comic_id = re.search(r"var ti=(\d*);", html)
            comic_id = int(match_comic_id.group(1))
            return comic_id

        def get_vol_code_list(comic_code):
            '''split code for each volume'''
            chunk_size = 50
            return [comic_code[i:i+chunk_size]
                    for i in range(0, len(comic_code), chunk_size)]

        html = get_html(one_page_url)
        title = get_title(html)
        comic_code = get_comic_code(html)
        comic_id = get_comic_id(html)
        vol_code_list = get_vol_code_list(comic_code)

        comic_info = {
            "title": title,
            "comic_id": comic_id,
            "volume_codes": vol_code_list,
            }
        return comic_info

    comic_url = get_comic_index_url(comic_id)
    one_page_url = get_one_page_url(comic_url)
    return get_comic_info(one_page_url)


def get_volume_metadata(comic_id, volume_code):
    def get_only_digit(string):
        return re.sub("\D", "", string)

    def get_image_url(page_number, comic_id,
                      did, sid, volume_number, volume_code, **kwargs):
        def get_hash(page_number):
            magic_number = (((page_number - 1) / 10) % 10) +\
                           (((page_number - 1) % 10) * 3)\
                           + 10
            magic_number = int(magic_number)
            return volume_code[magic_number:magic_number+3]

        hash = get_hash(page_number)
        image_url = "http://img{sid}.8comic.com/{did}/{comic_id}/"\
                    "{volume_number}/{page_number:03}_{hash}.jpg".format(
                        page_number=page_number,
                        comic_id=comic_id,
                        did=did,
                        sid=sid,
                        volume_number=volume_number,
                        hash=hash,
                        )
        return image_url

    def get_page_info(page_number, inner_volume_info):
        return {
                'page_number': page_number,
                'url': get_image_url(page_number, **inner_volume_info),
                }

    def get_pages(inner_volume_info):
        pages_info = []
        for page_number in range(1, inner_volume_info.get("page_count") + 1):
            page_info = get_page_info(page_number, inner_volume_info)
            pages_info.append(page_info)
        return pages_info

    inner_volume_info = {
        "comic_id": comic_id,
        "volume_code": volume_code,
        "volume_number": int(get_only_digit(volume_code[0:4])),
        "sid": get_only_digit(volume_code[4:6]),
        "did": get_only_digit(volume_code[6:7]),
        "page_count": int(get_only_digit(volume_code[7:10])),
        }
    volume_metadata = {
        'volume_number': inner_volume_info['volume_number'],
        'pages': get_pages(inner_volume_info),
        }
    return volume_metadata


def get_volume_download_list(volume_metadata, comic_dir):
    volume_number_string = '{:04}'.format(volume_metadata['volume_number'])
    volume_dir = os.path.join(comic_dir, volume_number_string)
    for page in volume_metadata['pages']:
        filename = '{:03}.jpg'.format(page['page_number'])
        save_path = os.path.join(volume_dir, filename)
        yield {'url': page['url'],
               'save_path': save_path}


def get_comic_download_list(comic_metadata, output_dir):
    comic_dir = os.path.join(output_dir, comic_metadata['title'])
    comic_id = comic_metadata['comic_id']
    comic_download_list = []
    for volume_code in comic_metadata['volume_codes']:
        volume_metadata = get_volume_metadata(comic_id, volume_code)
        comic_download_list.extend(
            get_volume_download_list(volume_metadata, comic_dir))
    return comic_download_list


def download_image(url, save_path):
    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        # print('Already Exist: {}'.format(save_path))
        pass
    else:
        dirname = os.path.dirname(save_path)
        os.makedirs(dirname, exist_ok=True)
        while True:
            try:
                response = UR.urlopen(url, timeout=60)
                break
            except UE.HTTPError as err:
                print('Skip {url} ->\n  {save_path}\n  {err}'.format(
                    url=url,
                    save_path=save_path,
                    err=err))
                break
            except UE.URLError as err:
                print('Retry {url} ->\n  {save_path}\n  {err}'.format(
                    url=url,
                    save_path=save_path,
                    err=err))
                continue
        with open(save_path, 'wb') as f:
            f.write(response.read())
        print('OK: {}'.format(save_path))


def get_comic_index_table(db):
    return db.table('comic_index')


def get_subscribed_table(db):
    return db.table('subscribed')


def get_args():
    def parse_args():
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            description='Download comic books from 8comic!')

        parser.add_argument(
            'query', metavar='QUERY', type=str, nargs='?',
            help='Search index to find the comic_id')

        parser.add_argument(
            '-s', '--subscribe', metavar='Comic_ID',
            dest='subscribe_comic_ids', type=int, nargs='+',
            help='Subscribe some comic book.')

        parser.add_argument(
            '-u', '--unsubscribe', metavar='Comic_ID',
            dest='unsubscribe_comic_ids', type=int, nargs='+',
            help='Unsubscribe some comic book.')

        parser.add_argument(
            '-l', '--list-subscribed', dest='list_subscribed',
            action='store_const', const=True, default=False,
            help='List all subscribed books.')

        parser.add_argument(
            '-r', '--refresh', dest='refresh',
            action='store_const', const=True, default=False,
            help='Refresh index of content and subscribed comic\'s'
                 '\nmetadata.')

        parser.add_argument(
            '-d', '--download', dest='download',
            action='store_const', const=True, default=False,
            help='Download subscribed comic books.')

        parser.add_argument(
            '-o', '--output-dir', metavar='DIR', dest='output_dir', type=str,
            default=os.getcwd(),
            help='Change download folder. default is cwd.'
                 '\n(default: %(default)s)')

        parser.add_argument(
            '--init', dest='init',
            action='store_const', const=True, default=False,
            help='Clear whole comic book database!')

        parser.add_argument(
            '-v', '--version', action='version', version=VERSION)

        args = parser.parse_args()
        return args

    args = parse_args()
    return args


def main():
    def print_subscribed_comic_info(row):
        if row['status'] == 'update':
            sign = '!'
        elif row['status'] == 'new':
            sign = '+'
        else:
            sign = ' '
        info = ('{sign} {comic_id:<10}{title}'
                '  (Volumes: {volume_count})').format(
                    comic_id=row['comic_id'],
                    title=row['title'],
                    volume_count=len(row['volume_codes']),
                    sign=sign,
                    )
        print(info)

    def get_all_subscribed_rows(db):
        s_table = get_subscribed_table(db)
        return sorted(s_table.all(),
                      key=lambda row: (row['status'], row['title']))

    def list_subscribed_comics(db):
        for row in get_all_subscribed_rows(db):
            print_subscribed_comic_info(row)

    def refresh(db):
        def refresh_index(db):
            comic_index_table = get_comic_index_table(db)
            comic_index_table.purge()
            comic_index = get_comic_index()
            comic_index_table.insert_multiple(comic_index)
            print("Index rebuild complete. Comics count: {}\n".format(
                len(comic_index)))

        def refresh_subscribed(db):
            print("Update subscribed comics metadata ...\n")
            s_table = get_subscribed_table(db)
            for row in s_table.all():
                subscribe(db=db, comic_id=row['comic_id'])
            print("\nMetadata update complete.")

        refresh_index(db)
        refresh_subscribed(db)

    def search(db, query):
        comic_index_table = get_comic_index_table(db)
        if not len(comic_index_table):
            refresh(db)
        matches = comic_index_table.search(
            tinydb.where('title').matches(r'.*?{}.*'.format(query)))
        if len(matches):
            # print('Comic ID  Title')
            # print('========= =====================')
            for match in matches:
                print('{comic_id:<10}{title}'.format(**match))

    def upsert_subscribed(db, new_comic_metadata):
        s_table = get_subscribed_table(db)
        comic_id = new_comic_metadata['comic_id']
        old_meta = s_table.get(
            tinydb.where('comic_id') == comic_id)
        if old_meta:
            s_table.update(new_comic_metadata, eids=[old_meta.eid])
            old_len = len(old_meta['volume_codes'])
            new_len = len(new_comic_metadata['volume_codes'])
            if old_len < new_len:
                s_table.update({'status': "update"}, eids=[old_meta.eid])
        else:
            s_table.insert(dict(status="new", **new_comic_metadata))
        return s_table.get(tinydb.where('comic_id') == comic_id)

    def subscribe(db, comic_id):
        comic_metadata = get_comic_metadata(comic_id)
        row = upsert_subscribed(db, comic_metadata)
        print_subscribed_comic_info(row)

    def unsubscribe(db, comic_id):
        s_table = get_subscribed_table(db)
        row = s_table.get(tinydb.where('comic_id') == comic_id)
        print_subscribed_comic_info(row)
        s_table.remove(tinydb.where('comic_id') == comic_id)

    def download_subscribed(db, output_dir):
        s_table = get_subscribed_table(db)
        for row in [r for r in get_all_subscribed_rows(db)
                    # if r.get('status')
                    ]:
            comic_download_list = get_comic_download_list(row, output_dir)
            with CF.ThreadPoolExecutor(max_workers=10) as e:
                for download_info in comic_download_list:
                    e.submit(download_image, **download_info)
            s_table.update(
                {"status": ""}, tinydb.where('comic_id') == row['comic_id'])

    args = get_args()
    db = tinydb.TinyDB(os.path.expanduser('~/.cmdlrdb'))

    if args.query:
        search(db, args.query)
    else:
        if args.refresh:
            refresh(db)
        # if args.output_dir:
        #     if db.table('settings').contain(
        #             tinydb.where('name') == 'output_dir'):
        #         elem = db.table('settings').get(
        #                 tinydb.where('name') == 'output_dir')
        #         elem['value']
        if args.unsubscribe_comic_ids:
            print('Unsubscribe:')
            for comic_id in args.unsubscribe_comic_ids:
                unsubscribe(db, comic_id)
        if args.subscribe_comic_ids:
            for comic_id in args.subscribe_comic_ids:
                subscribe(db, comic_id)
        if args.list_subscribed:
            list_subscribed_comics(db)
        if args.download:
            download_subscribed(db, args.output_dir)
        if args.init:
            db.purge_tables()


if __name__ == "__main__":
    main()
