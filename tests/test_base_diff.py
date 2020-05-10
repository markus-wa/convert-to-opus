import unittest
import sys
import os

import base_diff

tests_dir = os.path.dirname(os.path.realpath(__file__))
source_dir = tests_dir + '/source'
golden_dir = tests_dir + '/golden'

ignored_files = {'desktop.ini.txt', 'Folder.jpg.txt'}


class MicroMock(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestBaseDiff(unittest.TestCase):

    # noinspection DuplicatedCode
    def test_parse_args_min(self):
        sys.argv = [
            'cmd',
            '-s', '/path/to/src',
            '-t', '/path/to/out',
        ]

        cfg = base_diff.parse_args()

        self.assertEqual('/path/to/src', cfg.from_dir)
        self.assertEqual('/path/to/out', cfg.to_dir)

    def test_parse_args_full(self):
        sys.argv = [
            'cmd',
            '-s', '/path/to/src',
            '-t', '/path/to/out',
            '-i', 'desktop.ini.txt',
            '-i', 'Folder.jpg.txt'
        ]

        cfg = base_diff.parse_args()

        self.assertEqual('/path/to/src', cfg.from_dir)
        self.assertEqual('/path/to/out', cfg.to_dir)
        self.assertEqual(['desktop.ini.txt', 'Folder.jpg.txt'], cfg.ignore)

    def test_structure(self):
        actual = base_diff.structure(source_dir, {"desktop.ini.txt", "Folder.jpg.txt"})

        expected = [
            'aifc',
            'aiff',
            'flac-ogg',
            'flac',
            'opus',
            'vorbis',
            'wave',
            'nested' + os.sep + 'text',
            'nested' + os.sep + 'deep' + os.sep + 'aifc',
            'nested' + os.sep + 'deep' + os.sep + 'aiff',
            'nested' + os.sep + 'deep' + os.sep + 'flac-ogg',
            'nested' + os.sep + 'deep' + os.sep + 'flac',
            'nested' + os.sep + 'deep' + os.sep + 'opus',
            'nested' + os.sep + 'deep' + os.sep + 'vorbis',
            'nested' + os.sep + 'deep' + os.sep + 'wave',
        ]
        self.assertEqual(expected, actual)

    def test_main_same(self):
        exit_code = base_diff.main(MicroMock(
            from_dir=source_dir,
            to_dir=golden_dir,
            ignore=ignored_files
        ))

        self.assertEqual(0, exit_code)

    def test_main_diff(self):
        exit_code = base_diff.main(MicroMock(
            from_dir=source_dir,
            to_dir=source_dir + "/nested",
            ignore=ignored_files
        ))

        self.assertEqual(1, exit_code)


if __name__ == '__main__':
    unittest.main()
