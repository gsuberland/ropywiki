# ROPyWiki
ROPyWiki (read-only python wiki) is a simple, lightweight, locally run, read-only wiki for markdown files. The primary use-case is as a web frontend for a git-backed wiki. It is heavily inspired by [sqshr's mikiwiki](https://github.com/sqshr/mikiwiki).

## Features

ROPyWiki is currently under development, but it is in a usable state.

Current features include:

* Standard markdown support, including images
* Minimal dependencies. At current the only dependency is the [Markdown](https://pypi.org/project/Markdown/) package.
* Search against file/directory names and file contents, with search term highlighting on results.

## Known issues

XSS is trivially possible via the search functionality and file contents. **ROPyWiki is not intended for use with untrusted content, nor is it intended to be accessed remotely!**

## Setup and use

ROPyWiki is designed to run under Python 3.6 or later.

1. Clone the repo.
2. Run `pip install markdown` to ensure that you have the markdown library.
3. Place your wiki documents into the `./wiki/` folder (or modify the `sitedir` variable at the top of `ropywiki.py` to point to your wiki directory)
4. Run `python ropywiki.py`
5. Connect to the wiki on http://127.0.0.1:8080/

## License

Code released under MIT license. Full license text can be read [here](LICENSE).

## Contributions

Pull requests welcome. Only hard rule is not to introduce new dependencies! :)
