import unittest
import tempfile

from ml_utils.io import load, dump, SlotKeyError, Pack

from .generic import GenericObject


class ObjectFixturesMixIn(object):
    def setUp(self):
        self.obj2k = GenericObject(2000)
        self.obj1k = GenericObject(1000)

        with self.assertRaises(AssertionError):
            # Meta-unit-test that objects are actually different
            self.assertDictEqual(self.obj1k.data, self.obj2k.data)

    def assertEqualObj1k(self, recovered_obj):
        self.assertDictEqual(self.obj1k.data, recovered_obj.data)
        self.assertIsNot(self.obj1k, recovered_obj)

    def assertEqualObj2k(self, recovered_obj):
        self.assertDictEqual(self.obj2k.data, recovered_obj.data)
        self.assertIsNot(self.obj2k, recovered_obj)


class CompatibilityApiTestCase(ObjectFixturesMixIn, unittest.TestCase):

    def test_simple_dump_load(self):

        with tempfile.TemporaryFile("w+b") as tf:

            dump(self.obj2k, tf)

            recovered_obj2k = load(tf)

        self.assertEqualObj2k(recovered_obj2k)

    def test_multislot_dump_load(self):

        with tempfile.TemporaryFile("w+b") as tf:
            dump(self.obj1k, tf, slot_key='1k')
            dump(self.obj2k, tf, slot_key='2k')

            recovered_obj1k = load(tf, slot_key='1k')
            recovered_obj2k = load(tf, slot_key='2k')

        self.assertEqualObj1k(recovered_obj1k)
        self.assertEqualObj2k(recovered_obj2k)

    def test_sameslot_dump_load(self):

        with tempfile.TemporaryFile("w+b") as tf:
            dump(self.obj1k, tf, slot_key='same-slot')
            recovered_obj1k = load(tf, slot_key='same-slot')

            # Try to override
            dump(self.obj2k, tf, slot_key='same-slot')
            recovered_obj2k = load(tf, slot_key='same-slot')

        self.assertEqualObj1k(recovered_obj1k)
        self.assertEqualObj2k(recovered_obj2k)


class PackApiTestCase(ObjectFixturesMixIn, unittest.TestCase):

    def test_simple_dump_load(self):
        with tempfile.TemporaryFile("w+b") as tf:
            with Pack(tf) as pck:
                self.assertFalse(pck.has_slot('slot1'))
                pck.dump_slot('slot1', self.obj2k)
                self.assertTrue(pck.has_slot('slot1'))

                # Try to recover on opened pack
                recovered_obj2k = pck.load_slot('slot1')
                self.assertEqualObj2k(recovered_obj2k)

            with Pack(tf) as pck:

                # Try to recover on re-opened pack
                recovered_obj2k = pck.load_slot('slot1')
                self.assertEqualObj2k(recovered_obj2k)

    def test_multislot_dump_load(self):
        with tempfile.TemporaryFile("w+b") as tf:

            with Pack(tf) as pck:

                self.assertFalse(pck.has_slot('1k'))
                self.assertFalse(pck.has_slot('2k'))

                pck.dump_slot('1k', self.obj1k)
                pck.dump_slot('2k', self.obj2k)

                self.assertTrue(pck.has_slot('1k'))
                self.assertTrue(pck.has_slot('2k'))

                # Try to recover on opened pack
                recovered_obj1k = pck.load_slot('1k')
                recovered_obj2k = pck.load_slot('2k')
                self.assertEqualObj1k(recovered_obj1k)
                self.assertEqualObj2k(recovered_obj2k)

            with Pack(tf) as pck:

                # Try to recover on re-opened pack
                recovered_obj1k = pck.load_slot('1k')
                recovered_obj2k = pck.load_slot('2k')
                self.assertEqualObj1k(recovered_obj1k)
                self.assertEqualObj2k(recovered_obj2k)

    def test_sameslot_dump_load(self):

        with tempfile.TemporaryFile("w+b") as tf:

            with Pack(tf) as pck:
                pck.dump_slot('same-slot', self.obj1k)

                with self.assertRaises(SlotKeyError):
                    # Try to re-write on the same slot
                    pck.dump_slot('same-slot', self.obj1k)

                pck.remove_slot('same-slot')
                # Try to re-write on the same slot
                pck.dump_slot('same-slot', self.obj2k)

                recovered_obj2k = pck.load_slot('same-slot')
                self.assertEqualObj2k(recovered_obj2k)


if __name__ == '__main__':
    unittest.main()
