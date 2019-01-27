# convert-to-opus

Small command-line tool to help convert your music library from lossless formats (Wave/WAV, FLAC, Ogg/FLAC & AIFF) to [Opus](https://en.wikipedia.org/wiki/Opus_(audio_format)).

[![Build Status](https://travis-ci.com/markus-wa/convert-to-opus.svg?branch=master)](https://travis-ci.com/markus-wa/convert-to-opus)
[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/download/releases/3.6.0/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat)](LICENSE.md)

## Purpose

I mainly wrote this for myself to synchronize the smaller, lossy Opus music files from my PC to mobile.
That way I have enough storage to keep everything on my phone.
The lossless versions are kept for use on the desktop and for backup into the cloud (Google Drive).

To do this I suggest to do the conversion to a output directory on your PC and synchronize it with something like [Resilio](https://www.resilio.com/).


## Requirements

- **[`opusenc`](http://opus-codec.org/downloads/) must be installed and in your `PATH` environment variable.**
- [Python](https://www.python.org/downloads/) 3.6 or higher


## Usage

### `to_opus.py`

Recursively copies **all** files in the source directory to the target directory.
Files ending with `.flac`, `.wav`, `.aiff` and `.ogg` are converted and renamed to `.opus`.

    python to_opus.py --source /path/to/source-dir --target /path/to/output-dir

Options:
```
$ python to_opus.py -h
usage: to_opus.py [-h] [-c CONFIG] -s SOURCE -t TARGET
                  [--opusenc-args OPUSENC_ARGS] [-db DATABASE] [-v]

Args that start with '--' (eg. -s) can also be set in a config file (specified
via -c). Config file syntax allows: key=value, flag=true, stuff=[a,b,c] (for
details, see syntax at https://goo.gl/R74nmi). If an arg is specified in more
than one place, then commandline values override config file values which
override defaults.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        config file path
  -s SOURCE, --source SOURCE
                        path to source directory
  -t TARGET, --target TARGET
                        path to target directory
  --opusenc-args OPUSENC_ARGS
                        arguments to pass to opusenc (see
                        https://mf4.xiph.org/jenkins/view/opus/job/opus-
                        tools/ws/man/opusenc.html)
  -db DATABASE, --database DATABASE
                        path to the database file
  -v, --verbose         print debug information
```


### `base_diff.py`

Outputs a diff between the source and target directory, ignoring file extensions (only 'base' names).
Can be useful to see if there are new, unconverted files.

    python base_diff.py /path/to/source-dir /path/to/output-dir
