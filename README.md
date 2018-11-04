# Cmdlr

Extensible command line tool to tracking online comics.



## Supported Sites

- `cartoonmad`: www.cartoonmad.com
- `manhuagui`: manhuagui.com (external dependency: [nodejs](https://nodejs.org))



## Usage

### Daily Use

```sh
# subscribe a book
$ cmdlr https://example.com/path/to/book

# update metadata of books then download new volumes
$ cmdlr -md

# unsubscribe: just remove the directory of the book
$ rm -r <data_dir>/<book_dir>/
```


### Configuration

The default configuration file are located in:

1. `$XDG_CONFIG_HOME/cmdlr/config.yaml` or
2. `~/.config/cmdlr/config.yaml`



## Install

```sh
$ pip3 install cmdlr  # require python >= 3.5.3
```
