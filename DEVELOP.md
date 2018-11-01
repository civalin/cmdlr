If you want to write an analyzer, this is for you.

# Develop An Analyzer

To support more sites, please write an analyzer as plugin.



## Setup

1. Set the config option `analyzer_dir` to an empty local directory, e.g., `~/test-analyzers`.
2. Create an empty python file in `analyzer_dir`, e.g., `~/test-analyzers/example.py`.
3. Paste a do-nothing analyzer in this file. Here is it:

```python
"""The www.example.com analyzer.

[Entry examples]

- http://www.example.com/html/5640.html
- https://www.exmaple.com/html/5640.html
"""

from cmdlr.analyzer import BaseAnalyzer

class Analyzer(BaseAnalyzer):
    """The www.example.com analyzer."""

    entry_patterns = []

    async def get_comic_info(self, url, request, **unused):
        """Get comic info."""

    async def save_volume_images(self, url, request, save_image, **unused):
        """Get all images in one volume."""
```



4. Try `cmdlr -a`, you should find your new analyzer was loaded to system.

```sh
$ cmdlr -a
Enabled analyzers:
    - example           # here is the new analyzer (if filename == `example.py`)
```



Now everything is setup, but this analyzer not do anything right now.



## Required Components

Analyzer has many functions, but only those three are necessary.

- `entry_patterns`
    - determine a "entry url" should or should not be processed by this analyzer.
- `async def get_comic_info(url, request, loop)`
    - parsing a "entry url" and return the metadata of this book.
- `async def save_volume_images(url, request, save_image, loop)`
    - parsing a "volume url" in metadata, find out the all of the image's urls.



### Required: `entry_patterns`

This is a list of regex strings or `re.compile()` results. For example:

```python
entry_patterns = [r'^https?://(?:www\.)?example\.com/html/']
```



### Required: `async def get_comic_info(url, request, loop)`

Build the metadata by the input url.

- Arguments:
    - `url` (str): the book's entry.
    - `request(url, **kwargs)` (A warpper of [aiohttp.ClientSession.request]):
        - `url`: url want to retrieve.
        - `kwargs`: other kwargs that [aiohttp.ClientSession.request] accept.
    - `loop` ([asyncio.AbstractEventLoop]): event loop.
- Returns: (dict)
    - The metadata of this book.

The expected returning: (for example)

```python
{
    'name': 'comic name',           # required
    'volumes': {                    # required: "volume name" mapping to "volume url"
        'volume_name_001': 'http://comicsite.com/to/volume/entry/001'
        'volume_name_002': 'http://comicsite.com/to/volume/entry/002'
        'volume_name_003': 'http://comicsite.com/to/volume/entry/003'
    }
    'description': 'bala bala...',  # optional: string
    'authors': ['David'],           # optional: allow multiple authors
    'finished': False,              # optional: True or False
}
```


[asyncio.AbstractEventLoop]: https://docs.python.org/3/library/asyncio-eventloop.html?highlight=run_in_executor#asyncio.AbstractEventLoop
[aiohttp.ClientSession.request]: https://aiohttp.readthedocs.io/en/stable/client_reference.html#aiohttp.ClientSession.request



### Required: `async def save_volume_images(url, request, save_image, loop)`

Find out all of the images in a volume. Basically, include two steps:

1. find all image's **url** &  **page number**.
2. run `save_image()` to scheduling the download for each images.

- Arguments:
    - `url`: the url of a volume.
    - `request(url, **kwargs)` (A warpper of [aiohttp.ClientSession.request]): see above
    - `save_image(page_num, url, **kwargs)` (callable):
        - `page_num`: the page number, must `int`, not string.
        - `url`: image's url.
        - `kwargs`: other kwargs that [aiohttp.ClientSession.request] accept.
    - `loop` ([asyncio.AbstractEventLoop]): event loop.
- Returns:
    - Not used.

Call `save_image(...)` for example:

```python
for page_num, img_url in enumerate(img_urls, start=1):
    save_image(page_num, url=img_url)
```



## Optional Components

TODO



## Recipes

TODO
