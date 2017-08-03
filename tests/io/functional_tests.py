import unittest
import tempfile
import io as sys_io

from ml_utils.io import load, dump, remove_slot, SlotKeyError

from .generic import GenericObject


class CompatibilityApiTestCase(unittest.TestCase):

    def setUp(self):
        self.obj2k = GenericObject(2000)
        self.obj1k = GenericObject(1000)
        
        with self.assertRaises(AssertionError):
            # Meta-unit-test that objects are actually different
            self.assertDictEqual(self.obj1k.data, self.obj2k.data)
            
    def test_simple_dump_load(self):

        with tempfile.TemporaryFile("w+b") as tf:

            dump(self.obj2k, tf)

            tf.seek(0, sys_io.SEEK_SET)

            recovered_obj2k = load(tf)

        self.assertDictEqual(self.obj2k.data, recovered_obj2k.data)
        self.assertIsNot(self.obj2k, recovered_obj2k)

    def test_multislot_dump_load(self):

        with tempfile.TemporaryFile("w+b") as tf:
            dump(self.obj1k, tf, slot='1k')
            dump(self.obj2k, tf, slot='2k')

            tf.seek(0, sys_io.SEEK_SET)

            recovered_obj1k = load(tf, slot='1k')
            recovered_obj2k = load(tf, slot='2k')

        self.assertDictEqual(self.obj1k.data, recovered_obj1k.data)
        self.assertIsNot(self.obj1k, recovered_obj1k)

        self.assertDictEqual(self.obj2k.data, recovered_obj2k.data)
        self.assertIsNot(self.obj2k, recovered_obj2k)

    def test_sameslot_dump_load(self):

        with tempfile.TemporaryFile("w+b") as tf:
            dump(self.obj1k, tf, slot='same-slot')

            with self.assertRaises(SlotKeyError):
                # Try to override
                dump(self.obj2k, tf, slot='same-slot')

            remove_slot(tf, 'same-slot')
            dump(self.obj2k, tf, slot='same-slot')

            tf.seek(0, sys_io.SEEK_SET)

            recovered_obj2k = load(tf, slot='same-slot')

        self.assertDictEqual(self.obj2k.data, recovered_obj2k.data)
        self.assertIsNot(self.obj2k, recovered_obj2k)



if __name__ == '__main__':
    unittest.main()
