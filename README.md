# Cmdlr

An extensible command line tool for subscribe online comics.



# How to Use

## Subscribe

Copy your book's url, then:

```sh
cmdlr URL [URL ...]
```

That's it!

> Hint: `cmdlr` support multiple sites. To check out what sites and urls be supported, please use `cmdlr -a` & `cmdlr -a <analyzer_name>` command.

Btw, if you want to do some pipe magic, `stdin` also work!

```sh
echo -e 'URL1 URL2 \n URL3' | cmdlr
```



## Show Subscription Status

Cmdlr provide `-l` flag to query book's URL / metadata quickly.

```sh
cmdlr -l                # List all book's name and URL.
cmdlr URL [URL ...] -l  # More detail for those books.
```



## Update Metadata

After some time pass, ours metadata may outdated.

Use the `-m` option to update it.

```sh
cmdlr -m                # update metadata for all subscriptions
cmdlr URL [URL ...] -m  # update metadata for selected books
```

> Hint: the book's metadata include info of exist volumes, book's title, authors, url, etc.



## Fetch Files

Use `-d` flag to download all not downloaded volumes.

```sh
cmdlr -d                # download all subscriptions
cmdlr URL [URL ...] -d  # only download for selected books (and subscribe new URLs)
```



Can simple combine *metadata update* and *download* phases:

```sh
cmdlr -md
cmdlr URL [URL ...] -md
```



## More Usages

Use `cmdlr -h` to see more options.



# How to Configure

After run `cmdlr` at least one time. The default configuration file will be generated in `~/.config/cmdlr/config.yaml`. It look like this:

```yaml
dirs:
- ~/comics
disabled_analyzers: []
extra_analyzer_dir: null
max_concurrent: 10
max_retry: 4
proxy: null
```



## Option: `dirs` (List of Strings)

All subscribed books should be placed under the `dirs` directly. (default: `['~/comics']`)

example:

```yaml
dirs:
- /home/me/comic/new
- /home/me/comic/fantasy
- /home/me/comic/scifi
```

Notice:

1. The **first item** in `dirs` is the **INCOMING DIRECTORY** - all new subscribed books will be place in here automatically.
2. For performance reason, `cmdlr` would **NOT** recursive searching sub-folders. Only books in top level will be found.



## Option: `disabled_analyzers` (List of Strings)

Allow user to disable some analyzers. (default: `[]`)

This option is nice to use when some analyzers malfunction due to structure of site is changed. When a analyzer are disabled, all related books will not receive any further update. So user can waiting fix at ease without unsubscribe anything.

example:

```yaml
disabled_analyzers: ['example']
```



## Option: `extra_analyzer_dir` (String or Null)

All `*.py` files (or python package) in this folder will consider as analyzers. (default: `null`)

example:

```yaml
extra_analyzer_dir: '~/my_analyzers'  # `null` for disable
```

> Hint: if one analyzer in `extra_analyzer_dir` folder and has **THE SAME FILENAME** with built-in one, then, the built-in one will be **shadowed** by customized one.



## Option: `max_concurrent` (Integer)

Define the maximum global downloading concurrent number. And also be used to define how many books can processing parallel. (default: `10`)

This value should be setup based on user's network capacity. If too high may cause a lot of timeout error because multiple connections sharing a little traffic for each other, so no one can finish its task in a reasonable period.

example:

```yaml
max_concurrent: 10
```



## Option: `max_retry` (Integer)

Define the maximum network retry for any URLs. Value `0` mean no retry. (default: `4`)

example:

```yaml
max_retry: 2
```



## Option: `proxy` (String or Null)

Assign a http proxy for all connections. (default: `null`)

example:

```yaml
proxy: http://112.227.31.19:8080  # `null` for disable
```



## Option: `customization` (Dict)

Give some key value pairs to specific analyzer.

example:

```yaml
customization:
    AN_ANALYZER_NAME:
        username: xxx
        password: xxx
        language: en
```

> Hint: not need to tweak it unless an analyzer say it want something.



# How to Install

Make sure your `python >= 3.5` and already install the `pip`, then:

```sh
pip3 install cmdlr
```



# Supported Sites

- www.comicbus.com (external dependency: [nodejs](https://nodejs.org))
- www.cartoonmad.com
- ikanman.com (external dependency: [nodejs](https://nodejs.org))

> Feel free to send me PR to fix bug or support more sites :D



# How to Create a Custom Analyzer

Glad you asked. That's so easy!

1. Setup your `extra_analyzer_dirs` in configure file. (e.g., `~/test_analyzers`)
2. Create a `<analyzer_name>.py` file in `extra_analyzer_dirs` folder. (e.g., `~/test_analyzers/example.py`)
3. Define all **three necessary components** in this file.



Let's see what's a basic analyzer skeleton look like:

```python
"""The www.example.com analyzer."""

import re

from bs4 import BeautifulSoup


# # optional components
# session_init_kwargs = {}
# comic_req_kwargs = {}
# volume_req_kwargs = {}
#
#
# def entry_normalizer(url):
#     """Normalize all possible entry url to single one form."""
#     return url
#
#
# def get_image_extension(resp):
#     """Use response to calculate image extension."""
#     return '.jpg'


entry_patterns = []


async def get_comic_info(resp, **kwargs):
    """Find comic info from entry."""


async def save_volume_images(resp, save_image, **kwargs):
    """Get all images in one volume."""
```



Feel free copy the above code into your `<analyzer_name>.py` file (actually, the [real world template](#real-world-template) may more suitable). I will explain it later.



## Necessary Components in an Analyzer

Developer **must** define this 3 components in analyzer file:

- List of Regexes: `entry_patterns`
- Async Function: `get_comic_info(resp, *, request, loop, **kwargs)`
- Async Function: `save_volume_images(resp, save_image, *, request, loop, **kwargs)`



### List of Regexes: `entry_patterns`

A list of `re.compile()` result.

It will be used to determine a book's urls should or should not be processed by this analyzer.

example:

```python
entry_patterns = [re.compile(r'^https?://(?:www\.)?example\.com/html/')]
```



### Async Function: `get_comic_info(resp, *, request, loop, **kwargs)`

This function should return the comic's info from book's url.

- Arguments:
    - `resp` ([aiohttp.ClientResponse](http://aiohttp.readthedocs.io/en/stable/client_reference.html#response-object)): the response of comic book entry.
    - `request` (A warpper function of [aiohttp.ClientSession.request](http://aiohttp.readthedocs.io/en/stable/client_reference.html#aiohttp.ClientSession.request), with the same `**kwargs`): use this function to request more page if parsing need.
    - `loop` ([asyncio.AbstractEventLoop](https://docs.python.org/3/library/asyncio-eventloop.html?highlight=run_in_executor#asyncio.AbstractEventLoop)): event loop.
    - `**kwargs`: keep for future use.
- Returns: (dict)
    - This dict should match the pattern defined in `schema.meta_parsing`. (see below)



#### Returned Value

The returned value is look like this:

```python
return {'name': 'comic name',
        'description': 'bala bala...',
        'authors': ['David'],   # allow multiple authors
        'finished': False,      # True or False
        'volumes': {            # `valume_name` mapping to `volume_entry_url`
            'volume_name_001': 'http://comicsite.com/to/volume/entry/001'
            'volume_name_002': 'http://comicsite.com/to/volume/entry/002'
            'volume_name_003': 'http://comicsite.com/to/volume/entry/003'
        }}
```

Developer can choice any string as `volume_name`, but please follow some rules:

Requirement:

1. **unique**: single `volume_name` should mapping to a single `volume_entry_url`, one by one.

Try to do your best:

2. **stable**: the `volume_name` - `volume_entry_url` mapping not changed as usually.
3. **human readable**
4. **sortable**



#### Extract the HTML

```python
async def get_comic_info(resp, **kwargs):
    html = await resp.text()

    # # or manual decode
    # binary = await resp.read()
    # html = binary.decode('big5', errors='ignore')
```

That's it.

> See: [aiohttp.ClientResponse](http://aiohttp.readthedocs.io/en/stable/client_reference.html#response-object) for more detail.



#### Parse the HTML

I recommend using `BeautifulSoup` to parsing data. like this...

```python
    # `html` already exists

    soup = BeautifulSoup(html, 'lxml')
    name = soup.find('span', id='comic-name').string  # get comic-name
```

but `re` (regex) module are also useful.

> See: [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) and [re](https://docs.python.org/3/library/re.html) for more detail.



#### Request More Pages

Sometimes, not all of necessary information in single page. Developer need to travel through more than one page to collect all infomation.

We can use the `request` function to get everything we want.

```python
async def get_comic_info(resp, request, **kwargs):
    # ...

    # we need some data in `url2`.
    async with request(url=url2) as resp2:
        html2 = await resp2.text()

    # do anything you want with `html2`
```

> See: [aiohttp.ClientSession.request](http://aiohttp.readthedocs.io/en/stable/client_reference.html#aiohttp.ClientSession.request) for more detail.



### Async Function: `save_volume_images(resp, save_image, *, request, loop, **kwargs)`

This function should doing the following things in single volume.

1. find all image's *url* &  *page number*.
2. run `save_image()` multiple time for each images.

---

- Arguments:
    - `resp` ([aiohttp.ClientResponse](http://aiohttp.readthedocs.io/en/stable/client_reference.html#response-object)): the response of current volume's url.
    - `save_image` (callable): see below.
    - `request` (A warpper function of [aiohttp.ClientSession.request](http://aiohttp.readthedocs.io/en/stable/client_reference.html#aiohttp.ClientSession.request), with the same `**kwargs`): use this function to request more page if parsing need.
    - `loop` ([asyncio.AbstractEventLoop](https://docs.python.org/3/library/asyncio-eventloop.html?highlight=run_in_executor#asyncio.AbstractEventLoop)): event loop.
    - `**kwargs`: keep for future use.
- Returns: Not used.



#### Function: `save_image(page_num, *, url, **request_kwargs)`

Developer should run `save_image(...)` function for **EACH** images in this volume before `save_volume_images()` finished.

The `page_num` is page number like `1`, `2`, `50` (not string) to determine the order of images. and the `url` is the image's url.

example:

```python
async def save_volume_images(resp, save_image, **kwargs):
    # ... skip parsing

    # `img_urls`: is a list and already parsing from volume's html
    #             and sorted by page.
    for idx, img_url in enumerate(img_urls):
        save_image(page_num=idx + 1, url=img_url)
```

If developer need to do more settings (e.g., headers) to request image binary, just use the `**request_kwargs`. Those keyword arguments will transfer to [aiohttp.ClientSession.request](http://aiohttp.readthedocs.io/en/stable/client_reference.html#aiohttp.ClientSession.request) interface.



## Optional Components

Developer can define the following things if need:

- Dict: `session_init_kwargs`
    - kwargs for `aiohttp.ClientSession` initialize.
- Dict: `comic_req_kwargs`
    - the `kwargs` (without url) in `request(**kwargs)` to get `resp` in `get_comic_info(resp, ...)`.
- Dict: `volume_req_kwargs`
    - the `kwargs` (without url) in `request(**kwargs)` to get `resp` in `save_volume_images(resp, ...)`.
- Function: `get_image_extension(resp)`
    - see below.
- Function: `entry_normalizer(url)`
    - see below.



### Function: `get_image_extension(resp)`

This function can use the `resp` of image to determine the image file extension. (e.g., `.jpg`, `.png`)

By default, `cmdlr` will using `Content-Type` to calculate it. If you want to do some customize, here is an example:

```python
def get_image_extension(resp):
    """Always use .jpg format."""
    return '.jpg'
```



### Function: `entry_normalizer(url)`

Developer can use this function to make sure multiple **semantic equivalence** url can mapping to a single one form. Let's see an example:

```
1. http://example.com/book/123
2. https://example.com/book/123
3. https://www.example.com/book/123
4. https://example.com/book/123.html
```

Assume those urls point to the same book. User may input `form 1`, sometime `form 2`, and the url in metadata file is `form 4`. In this situation, user may troubled because they can't select exists book "correctly".

If analyzer has an `entry_normalizer()`, all internal url operations will base on the **normalized form**. Problem solved.

Here is a example to show how to write a normalizer:

```python
entry_patterns = [
        re.compile(r'^http://(?:www.)?example.com/book/(\d+)(?:\.html)?$'),  # (\d+) is the book id
        ]


def entry_normalizer(url):
    """Normalize all possible entry url to single one form."""
    match = entry_patterns[0].search(url)
    id = match.group(1)
    return 'http://example.com/book/{}.html'.format(id)
```



## Real World Template

Previous template is good for describe ours concept, but this one may easier to use in real world.

Please check out all `TODO` tag in following template and rewrite them. I think it can cover most of the cases.

Your first step is setup the `entry_patterns`, then use `cmdlr -md <entry_url>` to test it. Go now `(/^o^)/`

```python
"""The www.example.com analyzer.

Write anything here which you want user to know.
User can use `cmdlr -a <analyzer_name>` to read the message in here.
Here is some examples. But no specific format required.

# Entry example

- http://www.example.com/book/1234/
- http://www.example.com/book/1234.html
- http://example.com/book/1234.html



# Maintainer

Your Name <xxx@mail.bigcompany.com>
"""

import re
import urllib.parse as UP

from bs4 import BeautifulSoup


def _get_soup(binary):
    html = binary.decode('utf8', errors='ignore')  # TODO: change the codec?
    return BeautifulSoup(html, 'lxml')


def _get_name(soup):
    # TODO: here is a example
    return soup.title.string.split(' - ')[0]


def _get_description(soup):
    pass  # TODO


def _get_authors(soup):
    pass  # TODO


def _get_finished(soup):
    pass  # TODO


def _get_volumes(soup, baseurl):
    # use UP.urljoin(baseurl, vol_url) to calculate "absolute" volume url
    pass  # TODO


entry_patterns = [
        # TODO: here is a example
        # re.compile(r'^http://www.example.com/book/(\d+)(?:\.html)?$'),
        ]


async def get_comic_info(resp, **kwargs):
    """Find comic info from entry."""
    soup = _get_soup(await resp.read())
    return {'name': _get_name(soup),
            'description': _get_description(soup),
            'authors': _get_authors(soup),
            'finished': _get_finished(soup),
            'volumes': _get_volumes(soup, str(resp.url))}


async def save_volume_images(resp, save_image, **kwargs):
    """Get all images in one volume."""
    soup = _get_soup(await resp.read())

    # TODO: should extract all image_url and page_number from `soup`
    #       and save in `image_data`...

    for image_url, page_num in image_data:
        save_image(page_num, url=image_url)
```



## Advanced Skills

Those skills may rough or require external dependency. And you don't need it as usually.



### Get Configuration from User

Developer can get some user setted data for your analyzer. Like this one:

```python
import cmdlr.config as config  # import cmdlr related module

# from .. import config        # Hint: your analyzer fullname is:
                               #   "cmdlr.analyzers.<analyzername>"
                               # so relative import like here are also work.

import cmdlr.exceptions as exceptions


def _get_username_password():
    analyzer_name = 'example'
    settings = config.get_customization(analyzer_name)  # here is the magic

    username = settings.get('username')
    password = settings.get('password')

    if not username or not password:
        raise exceptions.AnalyzerRuntimeError(
            'please setup your username and password in config.yaml. e.g.,\n'
            '\n'
            'customization:\n'
            '  example:\n'          # "example" is the name of analyzer
            '    username: name\n'
            '    password: pass\n'
            )

    return username, password


async def get_comic_info(resp, **kwargs):
    username, password = _get_username_password()  # raise error only when
                                                   # user using this analyzer
    # ... do anything you want
```



### Move Some Functions to Other Threads / Processes

Use `loop` to dispatch blocking operations to other threads. Here is an example:

```python
# Notice: Not recommended because too heavy. Only for example.
# "selenium" and "PhantomJS" already installed in this system.

from selenium import webdriver

async def get_comic_info(resp, loop, **kwargs):
    browser = webdriver.PhantomJS()
    await loop.run_in_executor(None, lambda: browser.get(str(resp.url)))
    html = browser.page_source
    # continue parsing...
```

> See: [loop.run_in_executor](https://docs.python.org/3/library/asyncio-eventloop.html?highlight=run_in_executor#asyncio.AbstractEventLoop.run_in_executor) for more detail.

But be careful, direct access the `loop` may make concurrent number over the `max_concurrent` limit.



### Dispatch Javascript Fragment to External JS Runtime

```python
# "nodejs" already installed.

import execjs

val = execjs.eval('function(){ return 1 + 2 }()')  # val == 3
```

> See: [pyexecjs](https://github.com/doloopwhile/PyExecJS) project for more detail.
