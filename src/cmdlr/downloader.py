import urllib.request as UR
import urllib.error as UE
import os


class Downloader():
    """
        General Download Toolkit
    """
    @classmethod
    def get(cls, url, **kwargs):
        '''
            urllib.request.urlopen wrapper
            return:
                binary data which it
        '''
        while True:
            try:
                response = UR.urlopen(url, timeout=60, **kwargs)
                break
            # except UE.HTTPError as err:  # Like 404 no find
            #     print('Skip {url} ->\n  {err}'.format(
            #         url=url,
            #         err=err))
            #     raise DownloadError
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
        os.makedirs(dirname, exists_ok=True)
        with open(filepath, 'wb') as f:
            f.write(binary_data)
