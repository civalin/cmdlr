> Deprecated: please see the [releases page](https://github.com/civalin/cmdlr/releases).

# Changelog

## 3.X

### 3.0.0

Fully rewrited version. The new shiny features is:

- Efficient:
    - Async download / analyze everythings. include html (for analysis) and images.
- Metadata improvements:
    - Metadata is yaml files. human readable / writeable.
    - Distributed metadata:
        - Maintain subscriptions with file browser.
        - Keep extra volume meta in volume files:
        - Fault tolerance.
- Analyzer framework update:
    - Simpler and more flexible analyzer format.
    - Robust error reporting and mistake-proofing.
    - Hide the complexity about async analyzing.
    - Allow fetch "finished" status from website now.
    - Allow user to load customized analyzer module locally. Easier develop and share analyzers to others.
- A lot of source code improved for maintainability.

Also drop some ability, including:

- No more bare files (e.g., `.png`, `.jpg`):
    - Only support `.cbz` format now.
- No more automatic hanzi convert.



## 2.X

### 2.1.4

- Analyzer: fix `8c` analyzer malfunction by web site changed.



### 2.1.3

- Analyzer: set `u17` analyzer reject pay chapter.



### 2.1.2

- Analyzer: set `u17` analyzer reject vip chapter.



### 2.1.1

- Analyzer: `u17` tweak for site changed.



### 2.1.0

- Tweaked: use `--list-all` to list all comic which user subscribed. and `-l` only show comic with no downloaded volumes.
- Analyzer: `8c` tweak for site changed.



### 2.0.6

- Analyzer: `cartoonmad` tweak for site changed.



### 2.0.5

- fixed: remove debug code.



### 2.0.4

- Analyzer: `8comic` tweak for site changed.



### 2.0.3

- Fixed: cbz convert error when volume name contain `.` character.
- Fixed: better sorting when using `-l`
- Added: `-l` option can search keyword in title.
- Enhanced: volume disappeard info when using `-l`.



### 2.0.2

- Enhanced: Better exception processing.



### 2.0.1

- Enhanced: Truly avoid the title conflict.
- Enhanced: Windows platform path assign.



### 2.0.0

This is a fully rewrite version

- Backend DB: `tinydb` -> `sqlite`
- Collect more data.
- Remove search function.
- make it extensible.



## 1.X

### 1.1.0

- Init release.
