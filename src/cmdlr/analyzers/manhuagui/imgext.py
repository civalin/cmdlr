r"""Get volume image data for download.

[smh_js]

This is a sample of "smh js":

    SMH.imgData({
        "bid": 29747,
        "bname": "飞行文学",
        "bpic": "29747.jpg",
        "cid": 398038,
        "cname": "第11回",
        "files": ["001.jpg.webp",
                  "002.jpg.webp",
                  "003.jpg.webp",
                  "097.jpg.webp",
                  "098.jpg.webp"],
        "finished": false,
        "len": 5,
        "path": "/ps2/f/feixingwen_xue/第11回/",
        "status": 1,
        "block_cc": "",
        "nextId": 0,
        "prevId": 397656,
        "sl": {
            "md5": "GTdWjMobp0W0r6Y9tVW5tw"
        }
    }).preInit();

"smh_js" is decoded from "target_js"



[chapter_info]

The "chapter_info" is the object stored in "smh_js".

The important part include:

    path:
        image file path (not include filename) from root the root of hosts.

    files:
        multiple image filenames, order by reading order.

        If a filename ends with `.webp`, which can safely strip `.webp` and
        retriving the original format.

    cid:
        should exist in query string when fetch image files. maybe mean the "chapter id"?

    sl.md5:
        should exist in query string when fetch image files.



[image url format]

A sample image url look like this one:

    https://i.hamreus.com/ps2/f/feixingwen_xue/第11回/001.jpg?cid=398038&md5=GTdWjMobp0W0r6Y9tVW5tw

The structure is:

    https://{image_host_code}.hamreus.com{path}{files[*]}?cid={cid}&md5={sl.md5}



[image_host_code]

Run `servs` in browser's console can find the "image_host_code". Like
following:

    [{"name":"自動",
      "hosts":[{"h":"i","w":100},{"h":"us","w":1}],
      "w":101},
     {"name":"電信",
      "hosts":[{"h":"eu","w":100}, {"h":"i","w":1}, {"h":"us","w":1}],
      "w":102},
     {"name":"聯通",
      "hosts":[{"h":"us","w":100},{"h":"i","w":1},{"h":"eu","w":1}],
      "w":102}]



[target_js]

This is a "target_js", it look like:

    window["\x65\x76\x61\x6c"](function(p,a,c,k,e,d){e=function(c){return(c<a?"":e(parseInt(c/a)))+((c=c%a)>35?String.fromCharCode(c+29):c.toString(36))};if(!''.replace(/^/,String)){while(c--)d[e(c)]=k[c]||e(c);k=[function(e){return d[e]}];e=function(){return'\\w+'};c=1;};while(c--)if(k[c])p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c]);return p;}('c.h({"i":6,"e":"g","l":"6.2","m":j,"k":"4","d":["8.2.3","7.2.3","b.2.3","9.2.3","a.2.3"],"n":y,"z":5,"w":"/x/f/A/4/","B":1,"r":"","o":0,"p":u,"v":{"s":"t"}}).q();',38,38,'D7BWAcHNgdwUwEbmIGm8CMbB7aiATATgHYAWA4ABjJ3LLXMLoA5qBmYAZQFkAJYAMwEsANnADOwBADsAhgFs4IQHsZgGQjA4aaAzbWD8ZkACJSALlPH8AJsGZ4GZZkwDG0uePD9bwW6b78J/EQAs4ZhJwAB76AJJm4ABOcABuEcDRcGHe+uKCAPa2ANYA+rauMiYArMAA4gAqJgDqoBwZSGTVZFEAbACaePoAatXF+jDmhK3FrcAigokGvokiVLxSgiLywhJ8cPzBXpDwErnBAK7yIob6ByJAA=='['\x73\x70\x6c\x69\x63']('\x7c'),0,{}))    # NOQA

Strip `window[...]` and decrypt this one can find the "smh_js".

"""

import re
import json
from random import choice
from urllib.parse import urlencode

from cmdlr.autil import run_in_nodejs

from .sharedjs import get_shared_js


async def _get_chapter_info(soup, loop):
    """Get single chapter info in volume entry soup."""
    target_js = soup.find('script', string=re.compile(r'window\["')).string
    encrypted_js = re.sub(r'^window\[.+?\]', '', target_js)

    full_js = get_shared_js() + encrypted_js

    smh_js = await loop.run_in_executor(None, lambda: run_in_nodejs(full_js))

    json_string = re.search(r'{.*}', smh_js).group(0)

    return json.loads(json_string)


def _get_normalized_filenames(filenames):
    webp_regex = re.compile(r'\.webp$')

    return [webp_regex.sub('', filename) for filename in filenames]


def _get_image_url(filename, chapter_info, image_host_codes):
    cid = chapter_info['cid']
    md5 = chapter_info['sl']['md5']
    chapter_path = chapter_info['path']

    image_host_code = choice(image_host_codes)

    return (
        'https://{image_host_code}.hamreus.com{chapter_path}{filename}?{qs}'
        .format(image_host_code=image_host_code,
                chapter_path=chapter_path,
                filename=filename,
                qs=urlencode({'cid': cid, 'md5': md5}))
    )


async def get_image_urls(soup, image_host_codes, loop):
    """Get image's urls from soup and configuration."""
    chapter_info = await _get_chapter_info(soup, loop)

    filenames = chapter_info['files']

    norm_filenames = _get_normalized_filenames(filenames)
    image_urls = [
        _get_image_url(filename, chapter_info, image_host_codes)
        for filename in norm_filenames
    ]

    return image_urls
