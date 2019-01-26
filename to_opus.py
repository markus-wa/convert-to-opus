import sys
from multiprocessing import Pool

import configargparse
import logging
import os
from pathlib import Path
from shutil import copyfile
from shutil import which
from subprocess import Popen
from typing import Callable, Dict

if which('opusenc') is None:
    print("ERROR: opusenc not found in PATH - please make sure it's installed", file=sys.stderr)
    exit(1)


# We can't use a lambda since they aren't picklable
def opusenc(src: str, dest: str) -> None:
    if Popen(['opusenc', src, dest] + opusenc_args).wait() is 0:
        logging.info('converted "{0}" -> "{1}"'.format(src, dest))
    else:
        # Fallback to copy
        # Can happen if a .ogg file is encoded as Vorbis, not FLAC
        logging.warning('Falling back to copy for {0}'.format(src))
        _, src_ext = os.path.splitext(src)
        target_base, _ = os.path.splitext(dest)
        copyfile(src, target_base + src_ext)


def to_opus(src_base: str, src_ext: str) -> None:
    base_action(src_base, src_ext, '.opus', opusenc)


def copy(src_base: str, src_ext: str) -> None:
    base_action(src_base, src_ext, src_ext, copyfile)


def base_action(src_base: str, src_ext: str, dest_ext: str, migrate: Callable[[str, str], None]):
    dest_base = target_dir + os.sep + os.path.relpath(src_base, source_dir)
    dest_path = dest_base + dest_ext
    Path(dest_base).parent.mkdir(parents=True, exist_ok=True)
    src_path = src_base + src_ext
    if needs_migration(src_path, dest_path):
        logging.info('migrating: "{0}" -> "{1}"'.format(src_path, dest_path))
        pool.apply_async(migrate, (src_path, dest_path,), error_callback=logging.error)


def needs_migration(src_path: str, dest_path: str) -> bool:
    if not os.path.isfile(dest_path):
        return True
    # TODO: if original file size changed, return True
    # TODO: if original file hash changed,  return True
    return False


extensions_to_action: Dict[str, Callable[[str, str], None]] = {
    # Convert files with these extensions to .opus
    **{ext: to_opus for ext in ['.wav', '.flac', '.ogg', '.aif']},

    # Ignore files with these extensions
    # My source folder is synced with google drive and I don't want to copy google drive metadata
    # TODO: make configurable
    **{ext: lambda *args: None for ext in ['.driveupload', '.drivedownload']}
}


def init_worker(opus_args):
    global opusenc_args
    opusenc_args = opus_args


def main(cfg):
    log_level = {
        True: logging.DEBUG,
        False: logging.INFO,
    }[cfg.verbose]

    logging.basicConfig(
        stream=sys.stdout,
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=log_level,
        datefmt='%Y-%m-%d %H:%M:%S')

    logging.debug('config: ' + str(cfg))

    global source_dir, target_dir, pool
    source_dir = cfg.source
    target_dir = cfg.target
    pool = Pool(processes=8, initializer=init_worker, initargs=[cfg.opusenc_args])

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


def parse_args():
    p = configargparse.ArgParser()
    p.add_argument('-c', '--config', is_config_file=True, help='config file path')
    p.add_argument('-s', '--source', required=True, help='path to source directory')
    p.add_argument('-t', '--target', required=True, help='path to target directory')
    p.add_argument('--opusenc-args', action='append', default=[],
                   help='arguments to pass to opusenc (see '
                        'https://mf4.xiph.org/jenkins/view/opus/job/opus-tools/ws/man/opusenc.html)')
    p.add_argument('-v', '--verbose', action='store_true', help='print debug information')

    options = p.parse_args()

    # to avoid configargparse misinterpreting the opusenc-args values we need to use single quotes around them
    options.opusenc_args = list(map(lambda arg: arg.replace("'", ''), options.opusenc_args))

    return options


if __name__ == '__main__':
    main(parse_args())
