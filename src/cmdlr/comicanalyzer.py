import abc


class ComicAnalyzerException(Exception):
    pass


class ComicAnalyzer(metaclass=abc.ABCMeta):
    '''Base class of all comic analyzer'''

    @property
    @abc.abstractmethod
    def codename(self):
        '''
        Return analyzer code name.
        Keep it SHORT and CLEAR. and not conflict with other analyzer.
        Recommend use 2 chars.

        e.g., co, sm, rd
        '''

    @property
    @abc.abstractmethod
    def desc(self):
        '''
        Return analyzer short description.
        Recommend include sitename or siteurl for user friendly.

        e.g., "8comic: vipcomic.com"
        '''

    def convert_to_local_comic_id(self, comic_id):
        if comic_id.startswith(self.codename + '/'):
            return comic_id[len(self.codename) + 1:]
        else:
            return None

    def convert_to_comic_id(self, local_comic_id):
        return self.codename + '/' + local_comic_id

    @abc.abstractmethod
    def url_to_comic_id(self, comic_entry_url):
        '''
            Convert comic_entry_url to comic_id.
            If convert success return a str format url, else return None.
        '''

    @abc.abstractmethod
    def comic_id_to_url(self, comic_id):
        '''
            Convert comic_id to comic_entry_url
            If convert success return a str format comic_id, else return None.
        '''

    @abc.abstractmethod
    def get_comic_info(self, comic_id):
        '''
            Get comic info from the internet
            The return data will be saved into user's comic_db

            return:
                {
                    comic_id: <comic_id>,
                    title: <comic_title>,
                    desc: <comic_desc>,
                    extra_data: {...},
                    volumes: [
                        {
                            'volume_id': <volume_id>,  # e.g., '16', '045'
                            'name': <volume_name>,
                        },
                        {...},
                        ...
                    ]
                }
        '''

    @abc.abstractmethod
    def get_volume_pages(self, comic_id, volume_id, extra_data):
        '''
            Get images url for future download.

            args:
                comic_id:
                    which comic you want to analysis
                volume_id:
                    which volume you want to analysis
                extra_data:
                    the comic extradata create by self.get_comic_info()

            yield:
                {
                    'url': <image_url>,
                    'local_filename': <local_filename>,  # e.g., 12.jpg
                }
        '''
