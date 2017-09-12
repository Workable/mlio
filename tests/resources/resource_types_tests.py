import unittest
import mock
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory

from ml_utils import io as mlio

from ml_utils.resources.exceptions import UnboundResourceError, AlreadyBoundResourceError, \
    ResourceNotFoundError, ResourceNotLoadedError
from ml_utils.resources.resource_types import (
    DictionaryResource, VocabularyResource, MLIOResource, ResourceBase)


def load_fixture(fname):
    full_path = Path(__file__).resolve().parent / 'fixtures' / 'data' / fname

    with open(full_path, 'rt', encoding='utf-8') as f:
        return f.read()


class DictionaryResourceTestCase(unittest.TestCase):

    def test_construction_and_attributes(self):

        r = DictionaryResource('an id', 'a/file.txt')
        self.assertEqual(r.id, 'an id')
        self.assertEqual(r.filename, 'a/file.txt')
        self.assertFalse(r.is_loaded())

        self.assertEqual(str(r), "<DictionaryResource[an id] filename='a/file.txt' UNBOUND>")
        self.assertEqual(repr(r), "<DictionaryResource[an id] filename='a/file.txt' UNBOUND>")

    def test_load_object(self):

        with TemporaryDirectory() as tmp_dir:
            opener = partial(open, Path(tmp_dir) / 'test.json')

            with opener(mode='wt+', encoding='utf-8') as f:
                f.write(load_fixture('something.map'))

            r = DictionaryResource('theid', 'something')

            self.assertDictEqual({
                'a': 1,
                'foo': 'bar',
                "unicode": "Νιαις œ•³≥≠÷’…ß÷≠ γιουνικοτ"
            }, r._load_object_impl(opener))

    def test_dump_object(self):

        with TemporaryDirectory() as tmp_dir:
            opener = partial(open, Path(tmp_dir) / 'test.json')

            r = DictionaryResource('theid', 'something')
            r._dump_object_impl({
                'a': 1,
                'foo': 'bar',
                "unicode": "Νιαις œ•³≥≠÷’…ß÷≠ γιουνικοτ"
            }, opener)

            with opener(mode='rt+', encoding='utf-8') as f:
                file_data = f.read()

            self.assertEqual(file_data, """{"a": 1, "foo": "bar", "unicode": "Νιαις œ•³≥≠÷’…ß÷≠ γιουνικοτ"}""")

    def test_update_object(self):

        r = DictionaryResource('theid', 'something')

        with self.assertRaises(TypeError):
            r.update_object("something not dict")

        with self.assertRaises(TypeError):
            r.update_object({'a', 'set'})

        a_dict = {'a': 'foo'}
        r.update_object(a_dict)
        self.assertIs(r.object, a_dict)


class VocabularyResourceTestCase(unittest.TestCase):

    def setUp(self):
        self.voc_entries = {
            'one',
            'two',
            'νιαις œ•³≥≠÷’…ß÷≠ γιουνικοτ',
            'again',
            'leading space',
            'trailing space',
        }

    def test_construction_and_attributes(self):

        r = VocabularyResource('an id', 'a/file.txt')
        self.assertEqual(r.id, 'an id')
        self.assertEqual(r.filename, 'a/file.txt')
        self.assertFalse(r.is_loaded())

        self.assertEqual(str(r), "<VocabularyResource[an id] filename='a/file.txt' UNBOUND>")
        self.assertEqual(repr(r), "<VocabularyResource[an id] filename='a/file.txt' UNBOUND>")

    def test_load_object(self):
        with TemporaryDirectory() as tmp_dir:
            opener = partial(open, Path(tmp_dir) / 'test.json')

            with opener(mode='wt+', encoding='utf-8') as f:
                f.write(load_fixture('something.voc'))

            r = VocabularyResource('theid', 'something')

            self.assertSetEqual(
                self.voc_entries,
                r._load_object_impl(opener))

    def test_dump_object(self):
        with TemporaryDirectory() as tmp_dir:
            opener = partial(open, Path(tmp_dir) / 'test.json')

            r = VocabularyResource('theid', 'something')
            r._dump_object_impl({
                'oNe',
                'Two',
                "Νιαις œ•³≥≠÷’…ß÷≠ γιουνικοτ"
            }, opener)

            with opener(mode='rt+', encoding='utf-8') as f:
                file_data = f.read()

            self.assertEqual(sorted(file_data.split('\n')), ['', "one", "two", "νιαις œ•³≥≠÷’…ß÷≠ γιουνικοτ"])

    def test_update_object(self):
        r = VocabularyResource('theid', 'something')

        with self.assertRaises(TypeError):
            r.update_object("something not dict")

        with self.assertRaises(TypeError):
            r.update_object({'a': 'dict'})

        a_set = {'one', 'foo'}
        r.update_object(a_set)
        self.assertIs(r.object, a_set)


class MLIOResourceTestCase(unittest.TestCase):

    def setUp(self):
        self.the_list = ["a", "list", "of", "elements"]
        self.the_text = "Νιαις œ•³≥≠÷’…ß÷≠ γιουνικοτ"

    def test_construction_and_attributes(self):

        r = MLIOResource('an id', 'a/file.txt')
        self.assertEqual(r.id, 'an id')
        self.assertEqual(r.filename, 'a/file.txt')
        self.assertFalse(r.is_loaded())

        self.assertEqual(str(r), "<MLIOResource[an id] filename='a/file.txt' slot_key='None' UNBOUND>")
        self.assertEqual(repr(r), "<MLIOResource[an id] filename='a/file.txt' slot_key='None' UNBOUND>")

    def test_default_slot_load_object(self):

        opener = partial(open, Path(__file__).resolve().parent / 'fixtures' / 'data' / 'default.mlpack')

        r = MLIOResource('theid', 'something')
        self.assertIsNone(r.slot_key)

        self.assertListEqual(
            self.the_list,
            r._load_object_impl(opener))

    def test_multi_slot_load_object(self):

        opener = partial(open, Path(__file__).resolve().parent / 'fixtures' / 'data' / 'multi.mlpack')

        r = MLIOResource('theid', 'something', slot_key='the-text')
        self.assertEqual(r.slot_key, 'the-text')

        self.assertEqual(
            self.the_text,
            r._load_object_impl(opener))

    def test_default_dump_object(self):
        with TemporaryDirectory() as tmp_dir:
            opener = partial(open, Path(tmp_dir) / 'test.mlpack')

            r = MLIOResource('theid', 'something')
            obj = {
                'oNe',
                'Two',
                "Νιαις œ•³≥≠÷’…ß÷≠ γιουνικοτ"
            }
            r._dump_object_impl(obj, opener)

            with opener(mode='rb') as f:
                recovered_obj = mlio.load(f)
            self.assertSetEqual(obj, recovered_obj)

    def test_multi_dump_object(self):
        with TemporaryDirectory() as tmp_dir:
            opener = partial(open, Path(tmp_dir) / 'test.mlpack')

            # Perform two writes in different slots.
            r = MLIOResource('theid', 'something', slot_key='the-list')
            r._dump_object_impl(self.the_list, opener)
            r = MLIOResource('theid', 'something', slot_key='the-text')
            r._dump_object_impl(self.the_text, opener)

            # The MLPack shouldn't be truncated
            with opener(mode='rb') as f:
                recovered_text = mlio.load(f, slot_key='the-text')
                recovered_list = mlio.load(f, slot_key='the-list')

            self.assertListEqual(self.the_list, recovered_list)
            self.assertEqual(self.the_text, recovered_text)


class ResourceBasicGenericTestCase(unittest.TestCase):

    def test_construction_and_attributes(self):

        r = ResourceBase('an id', 'a/file.txt')
        self.assertEqual(r.id, 'an id')
        self.assertEqual(r.filename, 'a/file.txt')
        self.assertFalse(r.is_loaded())

        self.assertEqual(str(r), "<ResourceBase[an id] filename='a/file.txt' UNBOUND>")
        self.assertEqual(repr(r), "<ResourceBase[an id] filename='a/file.txt' UNBOUND>")

    def test_unbound(self):
        r = ResourceBase('an id', 'a/file.txt')
        with self.assertRaises(UnboundResourceError):
            r.manager

    def test_bind_manager(self):
        mocked_manager = mock.Mock()

        r = ResourceBase('an id', 'a/file.txt')
        r.bind_manager(mocked_manager)
        self.assertIs(r.manager, mocked_manager)

        # Try to re-bind
        with self.assertRaises(AlreadyBoundResourceError):
            r.bind_manager(mocked_manager)

        self.assertEqual(str(r), "<ResourceBase[an id] filename='a/file.txt' BOUND>")
        self.assertEqual(repr(r), "<ResourceBase[an id] filename='a/file.txt' BOUND>")

    def test_update_object(self):
        r = ResourceBase('an id', 'a/file.txt')
        self.assertFalse(r.is_loaded())

        obj = {'a', 'b'}
        self.assertFalse(r.is_loaded())
        r.update_object(obj)
        self.assertTrue(r.is_loaded())
        self.assertIs(r.object, obj)

    def test_load_not_found(self):
        mocked_manager = mock.Mock()

        r = ResourceBase('an id', 'a/file.txt')
        r.bind_manager(mocked_manager)

        mocked_manager.repositories.which.return_value = []
        with self.assertRaises(ResourceNotFoundError):
            r.load()

    def test_manual_load(self):
        mocked_manager = mock.Mock()

        r = ResourceBase('an id', 'a/file.txt')
        r.bind_manager(mocked_manager)
        obj = {'a', 'b'}

        with mock.patch.object(r, '_load_object_impl') as mocked_load_impl:
            mocked_load_impl.return_value = obj
            r.load()
            self.assertEqual(obj, r.object)

    def test_auto_load(self):
        mocked_manager = mock.Mock()
        mocked_repo = mock.Mock()

        mocked_manager.repositories.which.return_value = mocked_repo

        r = ResourceBase('an id', 'a/file.txt')
        r.bind_manager(mocked_manager)
        obj = {'a', 'b'}

        with mock.patch.object(r, '_load_object_impl') as mocked_load_impl:
            mocked_load_impl.return_value = obj
            # Try to get object
            self.assertEqual(obj, r.object)

            # Try to get object again
            self.assertEqual(obj, r.object)

            # Assure only once was called
            self.assertEqual(1, mocked_load_impl.call_count)

    def test_dump_not_loaded(self):
        mocked_manager = mock.Mock()
        mocked_repo = mock.Mock()

        mocked_manager.repositories.which.return_value = mocked_repo

        r = ResourceBase('an id', 'a/file.txt')
        r.bind_manager(mocked_manager)

        with self.assertRaises(ResourceNotLoadedError):
            r.dump('unknown repo')

    def test_dump(self):
        mocked_manager = mock.Mock()
        mocked_repo = mock.Mock()

        mocked_manager.repositories = {'repoid': mocked_repo}

        r = ResourceBase('an id', 'a/file.txt')
        r.bind_manager(mocked_manager)
        obj = {'a', 'b'}
        r.update_object(obj)

        with mock.patch.object(r, '_dump_object_impl') as mocked_dump_impl:
            mocked_dump_impl.return_value = obj

            r.dump('repoid')

            # Check that object is intact
            self.assertEqual(obj, r.object)

            # Assure only once was called
            mocked_dump_impl.assert_called_once_with(
                opener=mock.ANY,
                obj=obj
            )


if __name__ == '__main__':
    unittest.main()
