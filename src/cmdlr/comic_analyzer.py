import abc


class ComicAnalyzer(metaclass=abc.ABCMeta):
    '''Base class of all comic analyzer'''

    @classmethod
    @abc.abstractmethod
    def url_to_comic_id(cls, comic_entry_url):
        '''
            Convert comic_entry_url to comic_id.
            If convert success return a str format url, else return None.
        '''

    @classmethod
    @abc.abstractmethod
    def comic_id_to_url(cls, comic_id):
        '''
            Convert comic_id to comic_entry_url
        '''

    @classmethod
    @abc.abstractmethod
    def get_comic_info(cls, comic_id):
        '''
            Get comic info from the comic_entry_url

            return:
                {
                    comic_id: <comic_id>,
                    title: <comic_title>,
                    desc: <comic_desc>,
                    volumes: [
                        {
                            'volume_id': <volume_number>,
                            'name': <volume_name>,
                            'volume_entry_url': <url>,
                        },
                        {...},
                        ...
                    ]
                }
        '''

    @classmethod
    @abc.abstractmethod
    def get_volume_pages(cls, volume_entry_url):
        '''
            yield:
                {
                    'url': <image_url>,
                    'local_filename': <local_filename>,
                }
        '''
