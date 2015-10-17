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

        TODO: Accept extra configure data like cookies or a retry period
              which generated from some analyzer to deal some site.
    """
    @classmethod
    def get(cls, url, **kwargs):
        '''
            urllib.request.urlopen wrapper.

            return:
                binary data pack which be downloaded.
        '''
        while True:
            try:
                response = UR.urlopen(url, timeout=60, **kwargs)
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
        binary_data = response.read()
        return binary_data

    @classmethod
    def save(cls, url, filepath, **kwargs):
        '''
            args:
                url:
                    the file want to download
                filepath:
                    the file location want to save
        '''
        binary_data = cls.get(url, **kwargs)
        dirname = os.path.dirname(filepath)
        os.makedirs(dirname, exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(binary_data)


get = Downloader.get
save = Downloader.save
