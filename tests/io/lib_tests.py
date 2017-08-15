import unittest

from ml_utils.io._lib import file_as_blockiter, hash_file_object
from tests import fixtures


class LibTestCase(unittest.TestCase):

    def setUp(self):
        self.random1kdump_filepath = fixtures.file_path('random1k.dump')
        self.random1ksha256_filepath = fixtures.file_path('random1k.sha256')

        with open(self.random1kdump_filepath, 'r+b') as f:
            self.random1k_dump = f.read()

        with open(self.random1ksha256_filepath) as f:
            self.random1k_sha256 = f.read().strip()

    def test_file_as_blockiter(self):

        with open(self.random1kdump_filepath, 'r+b') as f:
            chunks = [
                chunk
                for chunk in file_as_blockiter(f, block_size=128)
            ]

        data = bytearray()
        for chunk in chunks:
            data += chunk
        self.assertEqual(len(chunks), 8)
        self.assertEqual(data, self.random1k_dump)

    def test_file_as_blockiter_uneven_chunks(self):

        with open(self.random1kdump_filepath, 'r+b') as f:
            chunks = [
                chunk
                for chunk in file_as_blockiter(f, block_size=15)
            ]

        data = bytearray()
        for chunk in chunks:
            data += chunk
        self.assertEqual(len(chunks), 69)
        self.assertEqual(data, self.random1k_dump)

    def test_hash_file_object(self):

        with open(self.random1kdump_filepath, 'r+b') as f:
            hexhash = hash_file_object(f)

        self.assertEqual(self.random1k_sha256, hexhash)


if __name__ == '__main__':
    unittest.main()
