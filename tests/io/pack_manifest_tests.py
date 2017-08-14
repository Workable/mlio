import unittest
import mock
import os
import json
from datetime import datetime


from ml_utils.io.exc import MLIOPackWrongFormat, SlotKeyError
from ml_utils.io.pack import PackManifestSlot, PackManifest
from ml_utils.io.serializers.generic import GenericMLModelsSerializer
from ml_utils.io.serializers.gensim import GensimWord2VecModelsSerializer
from ml_utils.io.context_dependencies.module_version import ModuleVersionContextDependency


class PackManifestSlotTestCase(unittest.TestCase):

    def setUp(self):
        self.manifest_deps_by_id = {
            dep.dependency_id(): dep
            for dep in [ModuleVersionContextDependency('themodule', '==1.1.0')]
        }

    def test_ctor_empty(self):
        ser = GenericMLModelsSerializer()

        slot = PackManifestSlot(
            slot_key='key',
            serializer=ser,
            serialized_sha256_hash='ahash',

        )
        self.assertEqual(slot.slot_key, 'key')
        self.assertIs(slot.serializer, ser)
        self.assertDictEqual(slot.dependencies, {})
        self.assertEqual(slot.pack_filename, 'ahash.slot')

    def test_ctor_with_dependencies(self):
        ser = GenericMLModelsSerializer()
        slot = PackManifestSlot(
            slot_key='key',
            serializer=ser,
            serialized_sha256_hash='ahash',
            dependencies=self.manifest_deps_by_id.values()
        )
        self.assertEqual(slot.slot_key, 'key')
        self.assertIs(slot.serializer, ser)
        self.assertEqual(slot.serialized_sha256_hash, 'ahash')
        self.assertDictEqual(slot.dependencies, self.manifest_deps_by_id)
        self.assertEqual(slot.pack_filename, 'ahash.slot')

    def test_ctor_with_wrong_dep_types(self):
        ser = GenericMLModelsSerializer()

        with self.assertRaises(TypeError):
            PackManifestSlot(
                slot_key='key',
                serializer=ser,
                serialized_sha256_hash='ahash',
                dependencies=['themodule-=1.1.0']
            )

    def test_to_dict(self):
        ser = GenericMLModelsSerializer()

        slot = PackManifestSlot(
            slot_key='nice slot',
            serialized_sha256_hash='ahash',
            serializer=ser,
            dependencies=self.manifest_deps_by_id.values()
        )

        self.assertEqual(slot.to_dict(), {
            'serializer': 'generic-ml-models',
            'serialized_sha256_hash': 'ahash',
            'dependencies': ['module-version:themodule-==1.1.0']
        })

    def test_from_dict(self):

        slot = PackManifestSlot.from_dict(
            'nice slot',
            {
                'serializer': 'generic-ml-models',
                'serialized_sha256_hash': 'ahash',
                'dependencies': ['module-version:themodule-==1.1.0']
            },
            manifest_dependencies=self.manifest_deps_by_id
        )

        self.assertEqual(slot.slot_key, 'nice slot')
        self.assertIsInstance(slot.serializer, GenericMLModelsSerializer)
        self.assertDictEqual(slot.dependencies, self.manifest_deps_by_id)
        self.assertEqual(slot.pack_filename, 'ahash.slot')
        self.assertEqual(slot.serialized_sha256_hash, 'ahash')

    def test_from_dict_missing_hash_field(self):

        manifest_deps = {}

        with self.assertRaises(MLIOPackWrongFormat):
            PackManifestSlot.from_dict(
                'nice slot',
                {
                    'serializer': 'generic-ml-models',
                    'dependencies': ['module-version:themodule-==1.1.0']
                },
                manifest_dependencies=manifest_deps
            )

    def test_from_dict_missing_serializer_field(self):
        manifest_deps = {}

        with self.assertRaises(MLIOPackWrongFormat):
            PackManifestSlot.from_dict(
                'nice slot',
                {
                    'serialized_sha256_hash': 'ahash',
                    'dependencies': ['module-version:themodule-==1.1.0']
                },
                manifest_dependencies=manifest_deps
            )

    def test_from_dict_missing_dependency(self):
        manifest_deps = {}

        with self.assertRaises(MLIOPackWrongFormat):
            PackManifestSlot.from_dict(
                'nice slot',
                {
                    'serializer': 'generic-ml-models',
                    'serialized_sha256_hash': 'ahash',
                    'dependencies': ['module-version:themodule-==1.1.0']
                },
                manifest_dependencies=manifest_deps
            )


class PackManifestTestCase(unittest.TestCase):

    def setUp(self):
        self.dependencies = [
                ModuleVersionContextDependency('themodule', '==1.1.0'),
                ModuleVersionContextDependency('anothermodule', '>=1.1.0,<=2.2.0')
            ]

        self.deps_by_id = {
            dep.dependency_id(): dep
            for dep in self.dependencies
        }
        self.slots = [
            PackManifestSlot(
                'slot1',
                serializer=GenericMLModelsSerializer(),
                serialized_sha256_hash='hash1',
                dependencies=[self.deps_by_id['module-version:themodule-==1.1.0'],
                              self.deps_by_id['module-version:anothermodule-<=2.2.0,>=1.1.0']]
            ),
            PackManifestSlot(
                'slot2',
                serializer=GensimWord2VecModelsSerializer(),
                serialized_sha256_hash='hash2',
                dependencies=[self.deps_by_id['module-version:anothermodule-<=2.2.0,>=1.1.0']]
            )
        ]

        self.slots_by_id = {
            slot.slot_key: slot
            for slot in self.slots
        }

        manifest_filepath = os.path.join(os.path.dirname(__name__), '..', 'fixtures', 'manifest.json')
        with open(manifest_filepath, 'r') as f:
            self.manifest_dict = json.load(f)

    @mock.patch('ml_utils.io.pack.datetime')
    def test_ctor_empty(self, mocked_datetime):
        creation_time = datetime(2017, 1, 1, 2, 2, 2)
        mocked_datetime.utcnow.return_value = creation_time

        manifest = PackManifest()

        self.assertDictEqual(manifest.slots, {})
        self.assertDictEqual(manifest.dependencies, {})
        self.assertEqual(manifest.created_at, creation_time)
        self.assertEqual(manifest.updated_at, creation_time)

    @mock.patch('ml_utils.io.pack.datetime')
    def test_ctor(self, mocked_datetime):
        creation_time = datetime(2017, 1, 1, 2, 2, 2)
        mocked_datetime.utcnow.return_value = creation_time

        manifest = PackManifest(
            dependencies=self.dependencies,
            slots=self.slots
        )

        self.assertListEqual(sorted(manifest.slots.keys()), ['slot1', 'slot2'])
        self.assertEqual(manifest.slots['slot1'].slot_key, 'slot1')
        self.assertListEqual(sorted(manifest.slots['slot1'].dependencies.keys()),
                             ['module-version:anothermodule-<=2.2.0,>=1.1.0', 'module-version:themodule-==1.1.0'])

        self.assertEqual(manifest.slots['slot2'].slot_key, 'slot2')
        self.assertListEqual(sorted(manifest.slots['slot2'].dependencies.keys()),
                             ['module-version:anothermodule-<=2.2.0,>=1.1.0'])

        self.assertListEqual(sorted(manifest.dependencies.keys()),
                             ['module-version:anothermodule-<=2.2.0,>=1.1.0', 'module-version:themodule-==1.1.0'])
        self.assertEqual(manifest.dependencies['module-version:themodule-==1.1.0'].dependency_id(),
                         'module-version:themodule-==1.1.0')
        self.assertEqual(manifest.created_at, creation_time)
        self.assertEqual(manifest.updated_at, creation_time)

    @mock.patch('ml_utils.io.pack.datetime')
    def test_touch_update_at(self, mocked_datetime):
        creation_time = datetime(2017, 1, 1, 2, 2, 2)

        mocked_datetime.utcnow.return_value = creation_time
        manifest = PackManifest()

        self.assertEqual(manifest.created_at, creation_time)
        self.assertEqual(manifest.updated_at, creation_time)

        updated_time = datetime(2018, 1, 1, 2, 2, 2)
        mocked_datetime.utcnow.return_value = updated_time
        manifest.touch_updated_at()

        self.assertEqual(manifest.created_at, creation_time)
        self.assertEqual(manifest.updated_at, updated_time)

    def test_insert_slot(self):
        manifest = PackManifest()
        self.assertDictEqual(manifest.slots, {})
        self.assertDictEqual(manifest.dependencies, {})

        # Insert one slot
        manifest.insert_slot(self.slots_by_id['slot2'])

        self.assertListEqual(sorted(manifest.slots.keys()),
                             ['slot2'])
        self.assertListEqual(sorted(manifest.dependencies.keys()),
                             ['module-version:anothermodule-<=2.2.0,>=1.1.0'])

        # Insert a second slot with common dependency
        manifest.insert_slot(self.slots_by_id['slot1'])

        self.assertListEqual(sorted(manifest.slots.keys()),
                             ['slot1', 'slot2'])

        self.assertListEqual(sorted(manifest.dependencies.keys()),
                             ['module-version:anothermodule-<=2.2.0,>=1.1.0', 'module-version:themodule-==1.1.0'])

    def test_insert_slot_invalid(self):
        manifest = PackManifest()

        # Insert one slot
        manifest.insert_slot(self.slots_by_id['slot2'])

        # Insert the same slot twice
        with self.assertRaises(SlotKeyError):
            manifest.insert_slot(self.slots_by_id['slot2'])

        # Assure dependencies left intact
        self.assertListEqual(sorted(manifest.dependencies.keys()),
                             ['module-version:anothermodule-<=2.2.0,>=1.1.0'])

    def test_remove_slot_invalid(self):
        manifest = PackManifest()

        with self.assertRaises(SlotKeyError):
            manifest.remove_slot('unknown')

    @mock.patch('ml_utils.io.pack.datetime')
    def test_remove_slot(self, mocked_datetime):
        creation_time = datetime(2017, 1, 1, 2, 2, 2)
        mocked_datetime.utcnow.return_value = creation_time

        manifest = PackManifest(
            dependencies=self.dependencies,
            slots=self.slots
        )

        # Remove slot1
        manifest.remove_slot('slot1')

        # Check that one dangling dependency was removed
        self.assertListEqual(sorted(manifest.slots.keys()),
                             ['slot2'])
        self.assertListEqual(sorted(manifest.dependencies.keys()),
                             ['module-version:anothermodule-<=2.2.0,>=1.1.0'])

        # Remove slot2
        manifest.remove_slot('slot2')
        self.assertDictEqual(manifest.slots, {})
        self.assertDictEqual(manifest.dependencies, {})

    @mock.patch('ml_utils.io.pack.datetime')
    @mock.patch('ml_utils.io.pack.sys')
    def test_to_dict(self, mocked_sys, mocked_datetime):
        creation_time = datetime(2017, 1, 1, 2, 2, 2)
        mocked_datetime.utcnow.return_value = creation_time
        mocked_sys.version = '3.6.1 (default, Apr  4 2017, 09:40:21) \n' \
                             '[GCC 4.2.1 Compatible Apple LLVM 8.1.0 (clang-802.0.38)]'

        manifest = PackManifest(
            dependencies=self.dependencies,
            slots=self.slots
        )

        # Change updated_at timestamp
        updated_time = datetime(2018, 1, 1, 2, 2, 2)
        mocked_datetime.utcnow.return_value = updated_time
        manifest.touch_updated_at()

        self.maxDiff = None
        self.assertDictEqual(manifest.to_dict(),
                             self.manifest_dict)

    def test_from_dict_bare_minimum(self):

        manifest = PackManifest.from_dict({
            'version': 2
        })
        self.assertDictEqual(manifest.slots, {})
        self.assertDictEqual(manifest.dependencies, {})

    def test_from_dict_wrong_version(self):

        with self.assertRaises(MLIOPackWrongFormat):
            PackManifest.from_dict({
                'version': 1
            })

    def test_from_dict_wrong_dependencies_container(self):

        with self.assertRaises(MLIOPackWrongFormat):
            PackManifest.from_dict({
                'version': 2,
                'dependencies': []
            })

    def test_from_dict_wrong_slots_container(self):

        with self.assertRaises(MLIOPackWrongFormat):
            PackManifest.from_dict({
                'version': 2,
                'slots': []
            })

    def test_from_dict_wrong_dependencies_type(self):

        with self.assertRaises(MLIOPackWrongFormat):
            PackManifest.from_dict({
                'version': 2,
                'dependencies': {
                    'test': {
                        'type': 'unknown'
                    }
                }
            })

    def test_from_dict_wrong_dependencies_arguments(self):

        with self.assertRaises(MLIOPackWrongFormat):
            PackManifest.from_dict({
                'version': 2,
                'dependencies': {
                    'test': {
                        'type': 'module-version'
                    }
                }
            })

    def test_from_dict_wrong_dependencies_id(self):

        with self.assertRaises(MLIOPackWrongFormat):
            PackManifest.from_dict({
                'version': 2,
                'dependencies': {
                    'test': {
                        'type': 'module-version',
                        'module_name': 'tests',
                        'version_specs': '==1.1.0'
                    }
                }
            })

    def test_from_dict(self):
        creation_time = datetime(2017, 1, 1, 2, 2, 2)
        updated_time = datetime(2018, 1, 1, 2, 2, 2)

        manifest = PackManifest.from_dict(self.manifest_dict)

        self.assertListEqual(sorted(manifest.slots.keys()), ['slot1', 'slot2'])
        self.assertEqual(manifest.slots['slot1'].slot_key, 'slot1')
        self.assertListEqual(sorted(manifest.slots['slot1'].dependencies.keys()),
                             ['module-version:anothermodule-<=2.2.0,>=1.1.0', 'module-version:themodule-==1.1.0'])

        self.assertEqual(manifest.slots['slot2'].slot_key, 'slot2')
        self.assertListEqual(sorted(manifest.slots['slot2'].dependencies.keys()),
                             ['module-version:anothermodule-<=2.2.0,>=1.1.0'])

        self.assertListEqual(sorted(manifest.dependencies.keys()),
                             ['module-version:anothermodule-<=2.2.0,>=1.1.0', 'module-version:themodule-==1.1.0'])
        self.assertEqual(manifest.dependencies['module-version:themodule-==1.1.0'].dependency_id(),
                         'module-version:themodule-==1.1.0')
        self.assertEqual(manifest.created_at, creation_time)
        self.assertEqual(manifest.updated_at, updated_time)


if __name__ == '__main__':
    unittest.main()
