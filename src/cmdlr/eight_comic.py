import urllib.request as UR
import urllib.error as UE
import re
import os

class EightComicException(Exception):
    pass

def get_html(url):
    while True:
        try:
            response = UR.urlopen(url, timeout=30)
            break
        except UE.URLError as err:
            print('Retry {url} ->\n  {err}'.format(
                url=url,
                err=err))
            continue
        except UE.HTTPError as err:
            print('Fatal Error {url} ->\n  {err}'.format(
                url=url,
                err=err))
            continue
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
            if match is None:
                raise EightComicException(
                    "CView decode Error: {}".format(comic_index_url))
            else:
                answer = match.groups(1)
                return answer


        def generate_one_page_url(one_page_url_fragment, catid):
            catid = int(catid)
            if catid in (4, 6, 12, 22):
                baseurl = "http://www.comicvip.com/show/cool-"
            elif catid in (1, 17, 19, 21):
                baseurl = "http://www.comicvip.com/show/cool-"
            elif catid in (2, 5, 7, 9):
                baseurl = "http://www.comicvip.com/show/cool-"
            elif catid in (10, 11, 13, 14):
                baseurl = "http://www.comicvip.com/show/best-manga-"
            elif catid in (3, 8, 15, 16, 18, 20):
                baseurl = "http://www.comicvip.com/show/best-manga-"

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
