import warnings
import unittest
import tempfile
import mock
from datetime import datetime
from ml_utils.io import Pack
from ml_utils.io.context_dependencies.module_version import ModuleVersionContextDependency
from ml_utils.io.exc import SlotKeyError, MLIOPackSlotWrongChecksum, MLIODependenciesNotSatisfied
from ml_utils.io.pack import PackManifest

from tests.io.generic import ObjectFixturesMixIn


class PackTestCase(ObjectFixturesMixIn, unittest.TestCase):

    def test_ctor_on_new_file(self):

        with tempfile.TemporaryFile("w+b") as tf:

            with Pack(tf) as pck:
                self.assertDictEqual(pck.slots_info, {})
                self.assertIsInstance(pck.manifest_info, PackManifest)

    def test_ctor_on_text_stream(self):

        with tempfile.TemporaryFile("w+") as tf:

            with Pack(tf) as pck:
                self.assertDictEqual(pck.slots_info, {})
                self.assertIsInstance(pck.manifest_info, PackManifest)

    @mock.patch('ml_utils.io.pack.datetime')
    def test_func_info(self, mocked_datetime):
        creation_time = datetime(2017, 1, 1, 2, 2, 2)
        updated_time = datetime(2018, 1, 1, 2, 2, 2)

        with tempfile.TemporaryFile("w+") as tf:
            mocked_datetime.utcnow.return_value = creation_time
            with Pack(tf) as pck:
                mocked_datetime.utcnow.return_value = updated_time
                pck.dump('slot1', self.obj1k)
                pck.dump('slot2', self.obj2k)
                self.assertListEqual(
                    sorted(pck.slots_info.keys()),
                    ['slot1', 'slot2']
                )
                self.assertEqual(pck.manifest_info.created_at, creation_time)
                self.assertEqual(pck.manifest_info.updated_at, updated_time)

    def test_existing_pack_objects(self):

        with tempfile.TemporaryFile("w+") as tf:
            with Pack(tf) as pck:

                # On empty list
                self.assertListEqual(sorted(pck._existing_pack_objects()), [])

                # With two same items
                pck.dump('slot1', self.obj1k)
                pck.dump('slot1-2', self.obj1k)

                self.assertListEqual(sorted(pck._existing_pack_objects()),
                                     ['25189f37eb6bc70786defce3ef1d200806687e083206dfad3edd641e8cd407d7.slot'])

                # With three items of 2 different objects
                pck.dump('slot2', self.obj2k)

                self.assertListEqual(sorted(pck._existing_pack_objects()),
                                     ['097e551bf9015606337c642a65e284006fc84f672654d24bf5d9cb31594ae2b2.slot',
                                      '25189f37eb6bc70786defce3ef1d200806687e083206dfad3edd641e8cd407d7.slot'])

    def test_remove_dangling_slot_objects(self):

        with tempfile.TemporaryFile("w+") as tf:
            with Pack(tf) as pck:

                # On empty list
                removed = list(pck._cleanup_dangling_pack_objects())
                self.assertListEqual(removed, [])
                self.assertListEqual(list(pck._existing_pack_objects()), [])

                # On populated pack
                pck.dump('slot1', self.obj1k)
                pck.dump('slot2', self.obj2k)

                removed = list(pck._cleanup_dangling_pack_objects())
                self.assertListEqual(removed, [])
                self.assertListEqual(sorted(pck._existing_pack_objects()),
                                     ['097e551bf9015606337c642a65e284006fc84f672654d24bf5d9cb31594ae2b2.slot',
                                      '25189f37eb6bc70786defce3ef1d200806687e083206dfad3edd641e8cd407d7.slot'])

                pck.remove('slot2')

                # Check that we cannot read object data
                dat = pck._zip_fh.read('097e551bf9015606337c642a65e284006fc84f672654d24bf5d9cb31594ae2b2.slot')
                self.assertEqual(len(dat), 0)
                self.assertListEqual(list(pck._existing_pack_objects()),
                                     ['25189f37eb6bc70786defce3ef1d200806687e083206dfad3edd641e8cd407d7.slot'])

    def test_dump_on_existing(self):

        with tempfile.TemporaryFile("w+") as tf:
            with Pack(tf) as pck:

                pck.dump('slot1', self.obj1k)
                with self.assertRaises(SlotKeyError):
                    pck.dump('slot1', self.obj2k)

    def test_dump(self):

        with tempfile.TemporaryFile("w+") as tf:
            with Pack(tf) as pck:

                pck.dump('slot1', self.obj1k)
                self.assertIn('slot1', pck.slots_info.keys())

    def test_dump_same_object_and_remove_one_slot(self):

        with tempfile.TemporaryFile("w+") as tf:
            with Pack(tf) as pck:
                pck.dump('slot1', self.obj1k)
                pck.dump('slot2', self.obj1k)

                pck.remove('slot2')

                recovered_1k = pck.load('slot1')
                self.assertEqualObj1k(recovered_1k)

    def test_redump_same_object(self):

        with tempfile.TemporaryFile("w+") as tf:
            with Pack(tf) as pck:
                pck.dump('slot1', self.obj1k)

                pck.remove('slot1')

                pck.dump('slot2', self.obj1k)
                recovered_1k = pck.load('slot2')
                self.assertEqualObj1k(recovered_1k)

    def test_load_invalid_key(self):

        with tempfile.TemporaryFile("w+") as tf:
            with Pack(tf) as pck:
                with self.assertRaises(SlotKeyError):
                    pck.load('unknown-slot1')

    def test_load_invalid_hash(self):

        with tempfile.TemporaryFile("w+") as tf:
            with Pack(tf) as pck:
                pck.dump('slot1', self.obj1k)

                # Break object checksum
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    pck._zip_fh.writestr(pck.slots_info['slot1'].pack_object, b'broken data')

                # Try to load slot should fail on checksum
                with self.assertRaises(MLIOPackSlotWrongChecksum):
                    pck.load('slot1')

    def test_load_unsatisfied_dependencies(self):

        with tempfile.TemporaryFile("w+") as tf:
            with Pack(tf) as pck:
                pck.dump('slot1', self.obj1k)

                # Hack to inject a dependency
                dep = ModuleVersionContextDependency('moduleone', '==1.1.0')
                pck.slots_info['slot1'].dependencies[dep.dependency_id()] = dep

                with mock.patch('ml_utils.io.context_dependencies.module_version.get_installed_module_version') \
                        as mocked_get_installed_module:
                    # Mock that dep is not satisfied
                    mocked_get_installed_module.side_effect = lambda m: {'moduleone': '2.1.0'}[m]

                    with self.assertRaises(MLIODependenciesNotSatisfied):
                        pck.load('slot1')

    def test_load_valid(self):

        with tempfile.TemporaryFile("w+") as tf:
            with Pack(tf) as pck:
                pck.dump('slot1', self.obj1k)
                pck.dump('slot2', self.obj2k)

                self.assertEqualObj1k(pck.load('slot1'))
                self.assertEqualObj2k(pck.load('slot2'))


if __name__ == '__main__':
    unittest.main()
