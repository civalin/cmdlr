# Changelog

## 4.X

### 4.1.7

- fix: cannot print error msg when parsed data schema error.

### 4.1.6

- analyzer.cartoonmad: fix for site changed.

### 4.1.5

- migrate back to github.com.

### 4.1.4

- analyzer.cartoonmad: adapt both old and new image server.

### 4.1.3

- fix: redirect cause unexpected error.
- fix: not catch SocksError properly so not retry in those situation.
- improve: `-a` can print unicode in analyzer's pref.
- add: allow user define the logging level. (default is INFO level)
- tweak: move some kind of logs into DEBUG level .
- analyzer.manhuagui: allow ignore some volume name by regex patterns.



### 4.1.2

- fix: timeout error in body fetching phase can not be retried.
- fix: connections semaphores had released before the body was fetched.



### 4.1.1

- fix: connections number out of control after some exceptions.
- fix: request timeout error not catch properly.
- tweak: make dynamic delay more reasonable.



### 4.1.0

- add: support random user-agent for analyzer.
- security: resist malicious js attack in `run_in_nodejs`
- internal: change dynamic delay algorithm.



### 4.0.0

#### Major Break Changed

- Break: Analyzer API fully rewrite.
- Break: Configuration format fully rewrite.
    - A lot of settings was removed, renamed, re-organized, and also introduced some brand-new options.

#### Major Underlying Changed

- Changed: Decrease overall YAML usage.
    - Replace YAML to JSON for book's metadata. It make a HUGE performance improvement when starting up (about 100x fast if large numbers of subscription).
        - The old data will be migrated automatically.
    - Replace YAML to JSON for volume's metadata.
        - Cannot automatic migrate, but cmdlr never used it (just write it for logging), so it should not break anything.

#### Good Things for User

- Smarter book level tasks scheduling.
    - `cmdlr` will automatic try to do the best that make all analyzers can working in the same time. Avoid traffic bursting or stoping at a part of sites.
- Allow to configure network usage (like `timeout`, `delay`, `per_host_connections`) on analyzer level.
- Add Socks support.
- Can assign a config file in command line interface.
- Can logging to filesystem.
- Simplify commandline interface.
- New `--json` output. Recommended using with `jq` to make query.

#### Development Enhancement

- Code style improvement.
- Let `finished`, `description`, `authors` fields be optional. simplify analyzer development.
- New helper function `autil.fetch()` and `autil.run_in_nodejs()` to simplify analyzer development.
- Upgrade all dependencies to newer version.
- Remove metadata cache system.
- Remove dependencies: `lxml`, `pyexecjs`



## 3.X

### 3.1.0

#### Enhancement

- Flow control enhancement
    - add: configurable static fetching delay.
    - add: dynamic fetching delay. Which will auto adapting server's response. If server return some fail, slowdown the following downloading speed in the target server temporarily.
    - add: basic `per_host_concurrent` configuration.
- MIME detect: support `image/bmp` filetype.
- Allow user to *comment-out* some lines in configuration file directly.

#### Fix

- cartoonmad: some book cannot fetch all volumes.

#### Tweak

- Enlarge network timeout. (decrease website loading when it's busy)



### 3.0.6

- cartoonmad: allow both www or non-www prefix.
- comicbus: fix title parsing in some pages.



### 3.0.5

- change analyzer's name `ikanman` to `manhuagui`.
- manhuagui: allow new domain name.



### 3.0.4

- fix: site `comicbus` structure changed.



### 3.0.3

- fix: comicbus decode error (require external js env).



### 3.0.1

- Show original metadata automatically if validate failed.



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
