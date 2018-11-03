If you want to write an analyzer, this is for you.

# Develop An Analyzer

To support more sites, please write an analyzer as plugin.



## 1. Set up

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



Now everything was set up, but this analyzer not do anything right now.



## 2. Required Components

An Analyzer has many functions, but only those three are necessary.

- *property* `entry_patterns`
    - determine a "entry url" should or should not be processed by this analyzer.
- *async method* `async def get_comic_info(url, request, loop)`
    - parsing a "entry url" and return the metadata of this book.
- *async method* `async def save_volume_images(url, request, save_image, loop)`
    - parsing a "volume url" in metadata, find out the all of the image's urls.



### *property* `entry_patterns`

This is a list of regex strings or `re.compile()` results. For example:

```python
entry_patterns = [r'^https?://(?:www\.)?example\.com/html/']
```



### *async method* `async def get_comic_info(url, request, loop)`

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



### *async method* `async def save_volume_images(url, request, save_image, loop)`

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



## 3. Optional Components

An ananlyzer has some optional components.



### *method* `def entry_normalizer(self, pref)`

(**Recommended to override**)

Developer can use this method to make sure multiple **semantic equivalence** url can mapping to a single one form. Let's see an example:

Forms:

1. `http://example.com/book/123`
2. `https://example.com/book/123`
3. `https://www.example.com/book/123`
4. `https://example.com/book/123.html`



Assume those urls point to the same book. User may input `form 1`, sometime `form 2`, and the url in metadata file is `form 4`. In this situation, user may troubled because they can't select exists book "correctly".

If analyzer has an `entry_normalizer`, all internal url operations will be based on the **normalized form**. Problem solved.

Here is a example to show how to write a `entry_normalizer`:

```python
Analyzer(BaseAnalyzer):
    entry_patterns = [
        re.compile(r'^http://(?:www.)?example.com/book/(\d+)(?:\.html)?$'),  # (\d+) is the book's id
    ]

    def entry_normalizer(self, url):
        """Normalize all possible entry url to single one form."""
        match = entry_patterns[0].search(url)
        id = match.group(1)

        return 'http://example.com/book/{}.html'.format(id)
```

**default**: return `url` directly (without normalized)



### *property* `default_request_kwargs`

The `request(...)` function has a lot of parameters powered by [aiohttp.ClientSession.request].

Developer can set up the default parameters here for all request.

Hints:

1. It affect the all `request()` call about this analyzer, include implicate call.
2. This value will be readed each time request call, so developer can use `@property` to dynamic the value.

**default**:

```python
{
    'method': 'GET',
}
```



### *property* `default_pref`

The default preference settings for this analyzer.

User can override those settings in their configuration file.

For example:

```python
# in analyzer's file

Analyzer(BaseAnalyzer):
    default_pref = {
        'https': True
        'picture_size': 'big',
    }
```

```yaml
# in user's configuration file

analyzer_pref:
  <your_analyzer_name>:
    picture_size: small  # override from big to small
```

Check `def to_config(pref)` for more detail.

**default**: `{}`



### *staticmethod* `def to_config(pref)`

For ease to use, raw settings usually want some pre-processing.

This function is used to convert the merged result of user's `analyzer_pref` and the `default_pref` (we call `pref`) to a new `config`.

Analyzer framework will save this method's returns to `self.config`.

**default**: return the `pref` itself.



### *method* `def get_image_extension(self, resp)`

This method can use the `resp` (a [aiohttp.ClientResponse] object) of image to determine the image file extension. (e.g., `.jpg`, `.png`)

**default**: using HTTP `Content-Type` to calculate the file extension.



## 4. Helper Functions

We offer some helper functions in `cmdlr.autil` module.



### *async function* `async def fetch(url, request, encoding='utf8', **req_kwargs)`

A simple helper to get remote html resource and relevent `BeautifulSoup`.

Arguments:

- `request` is the `request` function in `get_comic_info(...)` and `save_volume_images(...)`.
- `encoding` is the page encoding of the `url`.
- `req_kwargs` other keyword arguments of `request()` function.

Returns:

It will return a `FetchResult` (`nametuple`), which the defination is:

```python
namedtuple('FetchResult', ['soup', 'absurl'])
```

The `soup` is a [BeautifulSoup] object about the `url`.

The `absurl` is a function `absurl(url)` which can make the urls in this page absoluted.



### *function* `def run_in_nodejs(js)`

Eval the javascript code in node.js and get the return. The user's system should prepare `node` and `npm` before it can work.

The `js` code string will be ran in a jail provided by [vm2].



### *function* `def get_random_useragent()`

Get random useragent string from build-in database.



[asyncio.AbstractEventLoop]: https://docs.python.org/3/library/asyncio-eventloop.html?highlight=run_in_executor#asyncio.AbstractEventLoop
[aiohttp.ClientSession.request]: https://aiohttp.readthedocs.io/en/stable/client_reference.html#aiohttp.ClientSession.request
[aiohttp.ClientResponse]: https://aiohttp.readthedocs.io/en/stable/client_reference.html#aiohttp.ClientResponse
[BeautifulSoup]: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
[vm2]: https://github.com/patriksimek/vm2
