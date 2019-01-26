import sys
import unittest

import os
import shutil

import base_diff
import to_opus

test_dir = os.path.dirname(os.path.realpath(__file__))
source_dir = test_dir + '/source'
target_dir = test_dir + '/target'


class MicroMock(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestToOpus(unittest.TestCase):

    def test_main(self):
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

        to_opus.main(MicroMock(
            source=source_dir,
            target=target_dir,
            verbose=True,
            opusenc_args=[]
        ))

        self.assertEqual(0, base_diff.main(source_dir, target_dir))

    def test_parse_args_min(self):
        sys.argv = [
            'cmd',
            '-s', '/path/to/src',
            '-t', '/path/to/out',
        ]

        cfg = to_opus.parse_args()

        self.assertEqual('/path/to/src', cfg.source)
        self.assertEqual('/path/to/out', cfg.target)
        self.assertEqual(False, cfg.verbose)
        self.assertEqual([], cfg.opusenc_args)

    def test_parse_args_full(self):
        sys.argv = [
            'cmd',
            '-s', '/path/to/src',
            '-t', '/path/to/out',
            '-v',
            '--opusenc-args', "'--cvbr'",
            '--opusenc-args', "'--quiet'",
        ]

        cfg = to_opus.parse_args()

        self.assertEqual('/path/to/src', cfg.source)
        self.assertEqual('/path/to/out', cfg.target)
        self.assertEqual(True, cfg.verbose)
        self.assertEqual(['--cvbr', '--quiet'], cfg.opusenc_args)

    def test_parse_cfg_min(self):
        sys.argv = [
            'cmd',
            '-c', test_dir + '/cfg_min.txt',
        ]

        cfg = to_opus.parse_args()

        self.assertEqual('/path/to/src', cfg.source)
        self.assertEqual('/path/to/out', cfg.target)
        self.assertEqual(False, cfg.verbose)
        self.assertEqual([], cfg.opusenc_args)

    def test_parse_cfg_full(self):
        sys.argv = [
            'cmd',
            '-c', test_dir + '/cfg_full.txt',
        ]

        cfg = to_opus.parse_args()

        self.assertEqual('/path/to/src', cfg.source)
        self.assertEqual('/path/to/out', cfg.target)
        self.assertEqual(True, cfg.verbose)
        self.assertEqual(['--cvbr', '--quiet'], cfg.opusenc_args)


if __name__ == '__main__':
    unittest.main()
