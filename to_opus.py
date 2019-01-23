from subprocess import Popen
from multiprocessing import Pool
from shutil import copyfile
from pathlib import Path
import sys
import os

source = sys.argv[1]
target = sys.argv[2]


# We can't use a lambda since they aren't picklable
def opusenc(src, dest):
    Popen(['opusenc', src, dest]).wait()


def to_opus(src_base, src_ext):
    base_action(src_base, src_ext, '.opus', opusenc)


def copy(src_base, src_ext):
    base_action(src_base, src_ext, src_ext, copyfile)


def base_action(src_base, src_ext, dest_ext, f):
    dest_base = target + os.sep + os.path.relpath(src_base, source)
    dest_path = dest_base + dest_ext
    Path(dest_base).parent.mkdir(parents=True, exist_ok=True)
    if not os.path.isfile(dest_path):
        src_path = src_base + src_ext
        print('copy/convert from: "{0}" to: "{1}"'.format(src_path, dest_path))
        pool.apply_async(f, (src_path, dest_path,))


extensions_to_action = {
    # Convert files with these extensions to .opus
    **{ext: to_opus for ext in ['.wav', '.flac', '.ogg', '.aif']},

    # Ignore files with these extensions
    # My source folder is synced with google drive and I don't want to copy google drive metadata
    **{ext: lambda *args: None for ext in ['.driveupload', '.drivedownload']}
}


def main():
    for root, _, files in os.walk(source):
        for file in files:
            file_base, src_ext = os.path.splitext(file)
            src_base = root + os.sep + file_base
            extensions_to_action.get(src_ext, copy)(src_base, src_ext)


if __name__ == '__main__':
    pool = Pool(processes=8)
    main()
    pool.close()
    pool.join()
