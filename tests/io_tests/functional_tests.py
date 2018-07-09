import unittest
import tempfile

from mlio.io import load, dump, Pack
from mlio.io.exc import SlotKeyError

from tests.io.generic import ObjectFixturesMixIn


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


class ClassicApiTestCase(ObjectFixturesMixIn, unittest.TestCase):

    def test_simple_dump_load(self):
        with tempfile.TemporaryFile("w+b") as tf:
            with Pack(tf) as pck:
                self.assertFalse(pck.has_slot('slot1'))
                pck.dump('slot1', self.obj2k)
                self.assertTrue(pck.has_slot('slot1'))

                # Try to recover on opened pack
                recovered_obj2k = pck.load('slot1')
                self.assertEqualObj2k(recovered_obj2k)

            with Pack(tf) as pck:

                # Try to recover on re-opened pack
                recovered_obj2k = pck.load('slot1')
                self.assertEqualObj2k(recovered_obj2k)

    def test_multislot_dump_load(self):
        with tempfile.TemporaryFile("w+b") as tf:

            with Pack(tf) as pck:

                self.assertFalse(pck.has_slot('1k'))
                self.assertFalse(pck.has_slot('2k'))

                pck.dump('1k', self.obj1k)
                pck.dump('2k', self.obj2k)

                self.assertTrue(pck.has_slot('1k'))
                self.assertTrue(pck.has_slot('2k'))

                # Try to recover on opened pack
                recovered_obj1k = pck.load('1k')
                recovered_obj2k = pck.load('2k')
                self.assertEqualObj1k(recovered_obj1k)
                self.assertEqualObj2k(recovered_obj2k)

            with Pack(tf) as pck:

                # Try to recover on re-opened pack
                recovered_obj1k = pck.load('1k')
                recovered_obj2k = pck.load('2k')
                self.assertEqualObj1k(recovered_obj1k)
                self.assertEqualObj2k(recovered_obj2k)

    def test_sameslot_dump_load(self):

        with tempfile.TemporaryFile("w+b") as tf:

            with Pack(tf) as pck:
                pck.dump('same-slot', self.obj1k)

                with self.assertRaises(SlotKeyError):
                    # Try to re-write on the same slot
                    pck.dump('same-slot', self.obj1k)

                pck.remove('same-slot')
                # Try to re-write on the same slot
                pck.dump('same-slot', self.obj2k)

                recovered_obj2k = pck.load('same-slot')
                self.assertEqualObj2k(recovered_obj2k)


if __name__ == '__main__':
    unittest.main()
