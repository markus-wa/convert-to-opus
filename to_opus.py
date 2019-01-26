import sys
from multiprocessing import Pool

import logging
import os
from pathlib import Path
from shutil import copyfile
from shutil import which
from subprocess import Popen

if which('opusenc') is None:
    print("ERROR: opusenc not found in PATH - please make sure it's installed", file=sys.stderr)
    exit(1)

logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


# We can't use a lambda since they aren't picklable
def opusenc(src, dest):
    if Popen(['opusenc', src, dest]).wait() is 0:
        logging.info('converted "{0}" -> "{1}"'.format(src, dest))
    else:
        # Fallback to copy
        # Can happen if a .ogg file is encoded as Vorbis, not FLAC
        logging.warning('Falling back to copy for {0}'.format(src))
        _, src_ext = os.path.splitext(src)
        target_base, _ = os.path.splitext(dest)
        copyfile(src, target_base + src_ext)


def to_opus(src_base, src_ext):
    base_action(src_base, src_ext, '.opus', opusenc)


def copy(src_base, src_ext):
    base_action(src_base, src_ext, src_ext, copyfile)


def base_action(src_base, src_ext, dest_ext, f):
    dest_base = target_dir + os.sep + os.path.relpath(src_base, source_dir)
    dest_path = dest_base + dest_ext
    Path(dest_base).parent.mkdir(parents=True, exist_ok=True)
    if not os.path.isfile(dest_path):
        src_path = src_base + src_ext
        logging.info('copy/convert: "{0}" -> "{1}"'.format(src_path, dest_path))
        pool.apply_async(f, (src_path, dest_path,))


extensions_to_action = {
    # Convert files with these extensions to .opus
    **{ext: to_opus for ext in ['.wav', '.flac', '.ogg', '.aif']},

    # Ignore files with these extensions
    # My source folder is synced with google drive and I don't want to copy google drive metadata
    # TODO: make configurable
    **{ext: lambda *args: None for ext in ['.driveupload', '.drivedownload']}
}


def main(source: str, target: str):
    global source_dir, target_dir, pool
    source_dir = source
    target_dir = target
    pool = Pool(processes=8)

    logging.info('checking for unconverted files')
    for root, _, files in os.walk(source_dir):
        for file in files:
            file_base, src_ext = os.path.splitext(file)
            src_base = root + os.sep + file_base
            extensions_to_action.get(src_ext, copy)(src_base, src_ext)

    logging.info('finishing conversions')
    pool.close()
    pool.join()
    logging.info('conversions finished')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
