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

import urllib.request as UR
import urllib.error as UE
import os


class DownloadError(Exception):
    pass


class Downloader():
    """
        General Download Toolkit
    """
    def __init__(self, config):
        """
            args:
                config: <dict>
                    a Downloader config dict.
                    {
                        'proxies': <dict>,  # default: None (use env setting)
                            # e.g., {'http': 'http://proxy.hinet.net:80/'}
                    }
        """
        proxyhandler = UR.ProxyHandler(proxies=config.get('proxies', None))
        self.__opener = UR.build_opener(proxyhandler)

    def get(self, url, **options):
        '''
            urllib.request.urlopen wrapper.

            args:
                options:
                {
                    timeout: <positive int>,  # default: 60
                    method: <string>,  # default: None (auto select GET/POST)
                    headers: <dict>,   # default: {},
                        # e.g., {'User-Agent': Mozilla/5.0 Firefox/41.0}
                    data: <bytes>,     # Post data, default: None
                }

            return:
                binary data pack which be downloaded.
        '''
        req = UR.Request(
                url,
                data=options.get('data', None),
                headers=options.get('headers', {}),
                method=options.get('method', None),
                )
        while True:
            try:
                resp = self.__opener.open(req,
                                          timeout=options.get('timeout', 60))
                break
            except UE.HTTPError as err:  # Like 404 no find
                if err.code in (408, 503, 504, 507, 509):
                    print('Retry {url} ->\n  {err}'.format(
                        url=url,
                        err=err))
                    continue
                else:
                    print('Skip {url} ->\n  {err}'.format(
                        url=url,
                        err=err))
                    raise DownloadError()
            except UE.URLError as err:  # Like timeout
                print('Retry {url} ->\n  {err}'.format(
                    url=url,
                    err=err))
                continue
        binary_data = resp.read()
        return binary_data

    def save(self, url, filepath, **options):
        '''
            args:
                url:
                    the file want to download
                filepath:
                    the file location want to save
        '''
        binary_data = self.get(url, **options)
        dirname = os.path.dirname(filepath)
        os.makedirs(dirname, exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(binary_data)


_downloader = Downloader({})
get = _downloader.get
save = _downloader.save
