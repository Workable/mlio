import unittest
import os
from unittest import mock
from tempfile import TemporaryDirectory
from pathlib import Path
from contextlib import ExitStack


from ml_utils.resources.repositories import RepositoryBase, LocalDirectoryRepository, RepositoriesContainer
from ml_utils.resources.exceptions import RepositoryReadOnlyError, RepositoryPathTraversalError


class RepositoryBaseTestCase(unittest.TestCase):

    def test_constructor_and_attributes(self):

        # Different attributes
        rb = RepositoryBase(
            repository_id='theid',
            writable=0
        )
        self.assertEqual(rb.id, 'theid')
        self.assertFalse(rb.is_writable)

        self.assertEqual(str(rb), "<RepositoryBase[theid] Read-Only>")
        self.assertEqual(repr(rb), "<RepositoryBase[theid] Read-Only>")

        rb = RepositoryBase(
            repository_id='theid',
            writable=True
        )
        self.assertEqual(rb.id, 'theid')
        self.assertTrue(rb.is_writable)

        # Abstract methods
        with self.assertRaises(NotImplementedError):
            rb.has('test')

        with self.assertRaises(NotImplementedError):
            rb._open_impl('file')

        self.assertEqual(str(rb), "<RepositoryBase[theid]>")
        self.assertEqual(repr(rb), "<RepositoryBase[theid]>")

    def test_open_check_readonly(self):

        rb = RepositoryBase(
            repository_id='theid',
            writable=False
        )
        rb._open_impl = lambda *args, **kwargs: None

        with self.assertRaises(RepositoryReadOnlyError):
            rb.open('test', mode='r+')

        with self.assertRaises(RepositoryReadOnlyError):
            rb.open('test', mode='w')

        with self.assertRaises(RepositoryReadOnlyError):
            rb.open('test', mode='a')

        with self.assertRaises(RepositoryReadOnlyError):
            rb.open('test', mode='a+')

        # Should not raise
        rb.open('test', mode='r')


class LocalRepositoryBaseTestCase(unittest.TestCase):

    def test_constructor_on_non_existing_directory(self):

        with TemporaryDirectory() as tmpdirname:

            with self.assertRaises(ValueError):
                LocalDirectoryRepository(
                    repository_id='id',
                    directory_path=str(Path(tmpdirname) / 'nonexisting')
                )

    def test_constructor_and_attributes(self):

        with TemporaryDirectory() as tmpdirname:

            # default Read-only
            rd = LocalDirectoryRepository(
                repository_id='the id',
                directory_path=tmpdirname,
            )
            self.assertEqual(rd.directory_path, tmpdirname)
            self.assertEqual(rd.id, 'the id')
            self.assertFalse(rd.is_writable)

            self.assertEqual(str(rd), "<LocalDirectoryRepository[the id] directory='{}' Read-Only>".format(
                tmpdirname
            ))
            self.assertEqual(repr(rd), "<LocalDirectoryRepository[the id] directory='{}' Read-Only>".format(
                tmpdirname
            ))

            # Writable
            rd = LocalDirectoryRepository(
                repository_id='anot!@#5452',
                directory_path=tmpdirname,
                writable=True
            )
            self.assertEqual(rd.directory_path, tmpdirname)
            self.assertEqual(rd.id, 'anot!@#5452')
            self.assertTrue(rd.is_writable)

            self.assertEqual(str(rd), "<LocalDirectoryRepository[anot!@#5452] directory='{}'>".format(
                tmpdirname
            ))
            self.assertEqual(repr(rd), "<LocalDirectoryRepository[anot!@#5452] directory='{}'>".format(
                tmpdirname
            ))

    def test_absolute_path_valid(self):

        with TemporaryDirectory() as tmpdirname:

            rd = LocalDirectoryRepository(
                repository_id='the id',
                directory_path=tmpdirname,
            )

            self.assertEqual(
                rd._file_absolute_path('afile.txt.txt'),
                "{}/{}".format(tmpdirname, 'afile.txt.txt')
            )

            self.assertEqual(
                rd._file_absolute_path('γιουνικοντ/afile.txt.txt'),
                "{}/{}".format(tmpdirname, 'γιουνικοντ/afile.txt.txt')
            )

            self.assertEqual(
                rd._file_absolute_path('/root/path/afile.txt.txt'),
                "{}/{}".format(tmpdirname, 'root/path/afile.txt.txt')
            )

            self.assertEqual(
                rd._file_absolute_path('///root/path/afile.txt.txt'),
                "{}/{}".format(tmpdirname, 'root/path/afile.txt.txt')
            )

            self.assertEqual(
                rd._file_absolute_path('/something/../else/../afile.txt.txt'),
                "{}/{}".format(tmpdirname, 'afile.txt.txt')
            )

    def test_absolute_path_traversal_security(self):

        with TemporaryDirectory() as tmpdirname:

            rd = LocalDirectoryRepository(
                repository_id='the id',
                directory_path=tmpdirname,
            )

            with self.assertRaises(RepositoryPathTraversalError):
                rd._file_absolute_path('../../afile.txt.txt')

            with self.assertRaises(RepositoryPathTraversalError):
                rd._file_absolute_path('/something/../else/../../afile.txt.txt')

            with self.assertRaises(RepositoryPathTraversalError):
                rd._file_absolute_path('.')

    def test_method_has(self):

        with TemporaryDirectory() as tmpdirname:

            rd = LocalDirectoryRepository(
                repository_id='the id',
                directory_path=tmpdirname,
            )

            self.assertFalse(rd.has('unknown'))

            # Touch some file inside directory
            os.makedirs(Path(tmpdirname) / 'one' / 'two')
            open(Path(tmpdirname) / 'test.txt', 'w+').close()
            open(Path(tmpdirname) / 'one' / 'two' / 'inside.txt', 'w+').close()

            self.assertTrue(rd.has('test.txt'))
            self.assertTrue(rd.has('/one/two/inside.txt'))

            # Should not return has for directories
            self.assertFalse(rd.has('one'))
            self.assertFalse(rd.has('/one/two'))

    @mock.patch('ml_utils.resources.repositories.open')
    def test_method_open_readonly(self, mocked_open):

        with TemporaryDirectory() as tmpdirname:

            rd = LocalDirectoryRepository(
                repository_id='the id',
                directory_path=tmpdirname,
            )

            # No arguments
            rd.open('a.file.txt')
            mocked_open.assert_called_once_with(
                "{!s}/{}".format(tmpdirname, 'a.file.txt'),
                mode='r',
                encoding=None
            )

            with self.assertRaises(RepositoryReadOnlyError):
                rd.open('a.file.txt', mode='w+')

    @mock.patch('ml_utils.resources.repositories.open')
    def test_method_open_writable(self, mocked_open):
        with TemporaryDirectory() as tmpdirname:
            rd = LocalDirectoryRepository(
                repository_id='the id',
                directory_path=tmpdirname,
                writable=True
            )

            # With specific mode and encoding
            rd.open('a.file.txt', mode='w+', encoding='utf-8')
            mocked_open.assert_called_once_with(
                "{!s}/{}".format(tmpdirname, 'a.file.txt'),
                mode='w+',
                encoding='utf-8'
            )

    def test_method_open_directory(self):
        with TemporaryDirectory() as tmpdirname:
            rd = LocalDirectoryRepository(
                repository_id='the id',
                directory_path=tmpdirname,
                writable=True
            )

            # Touch some file inside directory
            os.makedirs(Path(tmpdirname) / 'one' / 'two')

            with self.assertRaises(IsADirectoryError):
                rd.open('one', mode='w+', encoding='utf-8')

    def test_method_open_reading_non_existing(self):
        with TemporaryDirectory() as tmpdirname:
            rd = LocalDirectoryRepository(
                repository_id='the id',
                directory_path=tmpdirname,
                writable=True
            )

            with self.assertRaises(FileNotFoundError):
                rd.open('a.file.txt')

    def test_method_open_autocreate_directory(self):
        with TemporaryDirectory() as tmpdirname:

            rd = LocalDirectoryRepository(
                repository_id='the id',
                directory_path=tmpdirname,
                writable=True
            )

            # Should autocreate with mode 'w' or '+' or 'a'
            rd.open('one/two/a.file.txt', mode='w').close()

            rd.open('two/three/another.file.txt', mode='w+').close()

            rd.open('two/three/four/yet another.file.txt', mode='a').close()


class RepositoriesContainerBaseTestCase(unittest.TestCase):

    def setUp(self):

        self.empty_cont = RepositoriesContainer()
        self.ordered_cont = RepositoriesContainer()
        self.ordered_cont.add_last(RepositoryBase('2'))
        self.ordered_cont.add_last(RepositoryBase('3'))
        self.ordered_cont.add_first(RepositoryBase('1'))

        with ExitStack() as stack:
            self.temp_dir = Path(stack.enter_context(TemporaryDirectory()))
            self._resource_stack = stack.pop_all()

        # prepare two repository directories

        os.makedirs(self.temp_dir / 'repo1' / 'common' / 'private-1')
        os.makedirs(self.temp_dir / 'repo1' / 'private-1')
        os.makedirs(self.temp_dir / 'repo2' / 'common' / 'private-2')
        os.makedirs(self.temp_dir / 'repo2' / 'private-2')

        open(self.temp_dir / 'repo1' / 'common' / 'common.txt', 'w').close()
        open(self.temp_dir / 'repo1' / 'common.txt', 'w').close()
        open(self.temp_dir / 'repo1' / 'private-1' / 'private-1.txt', 'w').close()
        open(self.temp_dir / 'repo2' / 'common' / 'common.txt', 'w').close()
        open(self.temp_dir / 'repo2' / 'common.txt', 'w').close()
        open(self.temp_dir / 'repo2' / 'private-2' / 'private-2.txt', 'w').close()

        self.repo1 = LocalDirectoryRepository('repo1', self.temp_dir / 'repo1')
        self.repo2 = LocalDirectoryRepository('repo2', self.temp_dir / 'repo2')

        self.cont = RepositoriesContainer()
        self.cont.add_first(self.repo1)
        self.cont.add_last(self.repo2)

        self.cont_inv = RepositoriesContainer()
        self.cont_inv.add_first(self.repo2)
        self.cont_inv.add_last(self.repo1)

    def tearDown(self):
        self._resource_stack.close()

    def test_iterator(self):

        # Empty
        self.assertListEqual(
            [],
            [repo for repo in self.empty_cont]
        )

        # Populated container, check that the order is respected
        self.assertListEqual(
            ['1', '2', '3'],
            [repo.id for repo in self.ordered_cont]
        )

    def test_contain_operator(self):

        # Unknown/Invalid
        for c in [self.empty_cont, self.ordered_cont]:
            self.assertFalse(None in c)
            self.assertFalse(False in c)
            self.assertFalse(True in c)
            self.assertFalse('unknown' in c)

        # Populated
        self.assertTrue('1' in self.ordered_cont)
        self.assertTrue('2' in self.ordered_cont)
        self.assertTrue('3' in self.ordered_cont)

    def test_has_method(self):

        # Unknown/Invalid
        for c in [self.empty_cont, self.ordered_cont]:
            self.assertFalse(c.has(None))
            self.assertFalse(c.has(False))
            self.assertFalse(c.has(True))
            self.assertFalse(c.has('unknown'))

        # Populated
        self.assertTrue('1' in self.ordered_cont)
        self.assertTrue('2' in self.ordered_cont)
        self.assertTrue('3' in self.ordered_cont)

    def test_add_get(self):

        # Some repos
        r1 = RepositoryBase('1')
        r2 = RepositoryBase('2')
        r3 = RepositoryBase('3')

        # Add only one at last
        c = RepositoriesContainer()
        c.add_last(r1)
        self.assertIs(c['1'], r1)

        # Add only one at the beginning
        c = RepositoriesContainer()
        c.add_first(r1)
        self.assertIs(c['1'], r1)

        # Add all and check
        c = RepositoriesContainer()
        c.add_last(r2)
        c.add_last(r3)
        c.add_first(r1)
        self.assertIs(c['1'], r1)
        self.assertIs(c['2'], r2)
        self.assertIs(c['3'], r3)

    def test_where_invalid(self):

        with self.assertRaises(RepositoryPathTraversalError):
            self.assertListEqual([], self.cont.where('.'))
        with self.assertRaises(RepositoryPathTraversalError):
            self.assertListEqual([], self.cont.where('..'))

    def test_where_on_empty(self):

        self.assertListEqual([], self.empty_cont.where('a/b/file.txt'))

    def test_where(self):

        # Find unknown
        self.assertListEqual([], self.empty_cont.where('a/b/file.txt'))

        # Find unique files
        self.assertListEqual(
            [self.repo1],
            self.cont.where('private-1/private-1.txt'))

        self.assertListEqual(
            [self.repo2],
            self.cont.where('private-2/private-2.txt'))

        # Find common files
        self.assertListEqual(
            [self.repo1, self.repo2],
            self.cont.where('common/common.txt'))

        # Find common inverted
        self.assertListEqual(
            [self.repo2, self.repo1],
            self.cont_inv.where('common/common.txt'))

    def test_which(self):

        # Find unknown
        self.assertIsNone(self.empty_cont.which('a/b/file.txt'))

        # Find unique files
        self.assertIs(
            self.repo1,
            self.cont.which('private-1/private-1.txt'))

        self.assertIs(
            self.repo2,
            self.cont.which('private-2/private-2.txt'))

        # Find common files
        self.assertIs(
            self.repo1,
            self.cont.which('common/common.txt'))

        # Find common inverted
        self.assertIs(
            self.repo2,
            self.cont_inv.which('common/common.txt'))

    def test_len(self):
        self.assertEqual(2, len(self.cont))
        self.assertEqual(2, len(self.cont_inv))
        self.assertEqual(3, len(self.ordered_cont))
        self.assertEqual(0, len(self.empty_cont))

    def test_repr_str(self):

        for c in (self.cont, self.cont_inv, self.ordered_cont, self.empty_cont):
            self.assertIsInstance(str(c), str)
            self.assertIsInstance(repr(c), str)


if __name__ == '__main__':
    unittest.main()
