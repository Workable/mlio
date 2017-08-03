import unittest
import tempfile
import io as sys_io


from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from gensim.models import Word2Vec
import numpy as np

from ml_utils.io.serializers.implementations import (
    DefaultSerializer, GenericMLModelsSerializer, GensimWord2VecModelsSerializer)
from tests.io.generic import GenericObject


RING_VERSE = [
    'one ring to rule them all'.split(),
    'one ring to find them'.split(),
    'one ring to bring them all'.split(),
    'and in the darkness bind them'.split()
]

DARK_TOWER = [
    'the man in black'.split(),
    'fled across the desert'.split(),
    'and the gunslinger followed'.split()
]


class DefaultSerializerTestCase(unittest.TestCase):

    def setUp(self):
        self.skreg = LinearRegression()
        self.skclf = RandomForestClassifier()
        self.xgboost = XGBClassifier()
        self.obj1k = GenericObject(1000)

    def test_class_method(self):

        self.assertTrue(DefaultSerializer.serializer_id(), 'default')

    def test_can_process(self):

        self.assertTrue(DefaultSerializer.can_process(int(1)))
        self.assertTrue(DefaultSerializer.can_process(int))
        self.assertTrue(DefaultSerializer.can_process("alala"))
        self.assertTrue(DefaultSerializer.can_process(self.skreg))
        self.assertTrue(DefaultSerializer.can_process(self.skclf))
        self.assertTrue(DefaultSerializer.can_process(self.xgboost))

    def test_dump_load_file(self):

        ser = DefaultSerializer()
        with tempfile.TemporaryFile('w+b') as tf:

            ser.dump(self.obj1k, tf)
            tf.seek(0, sys_io.SEEK_SET)
            recovered_obj1j = ser.load(tf)
        self.assertDictEqual(self.obj1k.data, recovered_obj1j.data)

        self.assertEqual(len(ser.get_context_dependencies()), 0)

    def test_dump_load_string(self):

        ser = DefaultSerializer()

        payload = ser.dumps(self.obj1k)
        recovered_obj1j = ser.loads(payload)
        self.assertDictEqual(self.obj1k.data, recovered_obj1j.data)

        self.assertEqual(len(ser.get_context_dependencies()), 0)

class GeneralMLTestCase(unittest.TestCase):

    def setUp(self):
        self.skreg = LinearRegression()
        self.skclf = RandomForestClassifier()
        self.xgboost = XGBClassifier()
        self.obj1k = GenericObject(1000)
        self.np_array = np.random.rand(1, 1000, 2000)

    def test_class_method(self):

        self.assertTrue(GenericMLModelsSerializer.serializer_id(), 'generic-ml-models')

    def test_can_process(self):

        # Expected to be processed
        self.assertTrue(GenericMLModelsSerializer.can_process(self.skreg))
        self.assertTrue(GenericMLModelsSerializer.can_process(self.skclf))
        self.assertTrue(GenericMLModelsSerializer.can_process(self.xgboost))
        self.assertTrue(GenericMLModelsSerializer.can_process(self.np_array))

        # Anything else
        self.assertFalse(GenericMLModelsSerializer.can_process(1))
        self.assertFalse(GenericMLModelsSerializer.can_process(int))
        self.assertFalse(GenericMLModelsSerializer.can_process("alala"))

    def test_dump_load_file(self):
        ser = GenericMLModelsSerializer()
        with tempfile.TemporaryFile('w+b') as tf:
            ser.dump(self.np_array, tf)
            tf.seek(0, sys_io.SEEK_SET)
            recovered_np_array = ser.load(tf)
        self.assertTrue(np.all(self.np_array == recovered_np_array))

        self.assertEqual(len(ser.get_context_dependencies()), 1)
        self.assertEqual(ser.get_context_dependencies()[0].dependency_id(), "numpy-==1.12.1")

    def test_dump_load_string(self):
        ser = GenericMLModelsSerializer()
        payload = ser.dumps(self.np_array)
        recovered_np_array = ser.loads(payload)
        self.assertTrue(np.all(self.np_array == recovered_np_array))

        self.assertEqual(len(ser.get_context_dependencies()), 1)
        self.assertEqual(ser.get_context_dependencies()[0].dependency_id(), "numpy-==1.12.1")


class GensimWord2VecTestCase(unittest.TestCase):

    def setUp(self):
        self.skreg = LinearRegression()
        self.skclf = RandomForestClassifier()
        self.xgboost = XGBClassifier()
        self.obj1k = GenericObject(1000)
        self.np_array = np.random.rand(1, 1000, 2000)
        self.wv_model = Word2Vec(RING_VERSE, size=10, window=3, min_count=1, workers=4)

    def test_class_method(self):

        self.assertTrue(GensimWord2VecModelsSerializer.serializer_id(), 'gensim')

    def test_can_process(self):

        # Expected to be processed
        self.assertTrue(GensimWord2VecModelsSerializer.can_process(self.wv_model))

        # Anything else
        self.assertFalse(GensimWord2VecModelsSerializer.can_process(self.skreg))
        self.assertFalse(GensimWord2VecModelsSerializer.can_process(self.skclf))
        self.assertFalse(GensimWord2VecModelsSerializer.can_process(self.xgboost))
        self.assertFalse(GensimWord2VecModelsSerializer.can_process(self.np_array))
        self.assertFalse(GensimWord2VecModelsSerializer.can_process(1))
        self.assertFalse(GensimWord2VecModelsSerializer.can_process(int))
        self.assertFalse(GensimWord2VecModelsSerializer.can_process("alala"))

    def test_dump_load_file(self):
        ser = GensimWord2VecModelsSerializer()
        with tempfile.TemporaryFile('w+b') as tf:
            ser.dump(self.wv_model, tf)
            tf.seek(0, sys_io.SEEK_SET)
            recovered_wv_model = ser.load(tf)

        self.assertTrue((self.wv_model.wv['one'] == recovered_wv_model.wv['one']).all())

        self.assertEqual(len(ser.get_context_dependencies()), 1)
        self.assertEqual(ser.get_context_dependencies()[0].dependency_id(), "gensim-==2.1.0")

    def test_dump_load_string(self):
        ser = GensimWord2VecModelsSerializer()
        payload = ser.dumps(self.wv_model)
        recovered_wv_model = ser.loads(payload)
        self.assertTrue((self.wv_model.wv['one'] == recovered_wv_model.wv['one']).all())

        self.assertEqual(len(ser.get_context_dependencies()), 1)
        self.assertEqual(ser.get_context_dependencies()[0].dependency_id(), "gensim-==2.1.0")

if __name__ == '__main__':
    unittest.main()
