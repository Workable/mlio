import unittest
from unittest import mock
import tempfile
import io as sys_io
import packaging.version
from pathlib import Path

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from gensim.models import Word2Vec
import numpy as np

from mlio.io.serializers.gensim import GensimWord2VecModelsSerializer
from tests.io_tests.generic import GenericObject
from tests.io_tests.serializers.data import RING_VERSE


class GensimWord2VecTestCase(unittest.TestCase):

    def setUp(self):
        self.skreg = LinearRegression()
        self.skclf = RandomForestClassifier()
        self.xgboost = XGBClassifier()
        self.obj1k = GenericObject(1000)
        self.np_array = np.random.rand(1, 1000, 2000)
        self.wv_model = Word2Vec(RING_VERSE, size=10, window=3, min_count=1, workers=4)

    def test_class_method(self):
        self.assertTrue(GensimWord2VecModelsSerializer.serializer_type(), 'gensim')

    def test_can_process(self):
        # Expected to be processed
        self.assertTrue(GensimWord2VecModelsSerializer.can_serialize(self.wv_model))

        # Anything else
        self.assertFalse(GensimWord2VecModelsSerializer.can_serialize(self.skreg))
        self.assertFalse(GensimWord2VecModelsSerializer.can_serialize(self.skclf))
        self.assertFalse(GensimWord2VecModelsSerializer.can_serialize(self.xgboost))
        self.assertFalse(GensimWord2VecModelsSerializer.can_serialize(self.np_array))
        self.assertFalse(GensimWord2VecModelsSerializer.can_serialize(1))
        self.assertFalse(GensimWord2VecModelsSerializer.can_serialize(int))
        self.assertFalse(GensimWord2VecModelsSerializer.can_serialize("alala"))

    @mock.patch('mlio.io.serializers.base.get_installed_module_version')
    def test_dump_load_file(self, mocked_get_installed_module_version):
        mocked_get_installed_module_version.return_value = packaging.version.parse('0.14.1')

        ser = GensimWord2VecModelsSerializer()
        with tempfile.TemporaryFile('w+b') as tf:
            ser.dump(self.wv_model, tf)
            tf.seek(0, sys_io.SEEK_SET)
            recovered_wv_model = ser.load(tf)

        self.assertTrue((self.wv_model.wv['one'] == recovered_wv_model.wv['one']).all())

        self.assertEqual(len(ser.get_context_dependencies()), 1)
        self.assertEqual(ser.get_context_dependencies()[0].dependency_id(), "module-version:gensim-~=0.14.1")

    def test_dump_load_file_integrated(self):
        from mlio.io.compat import load, dump

        ser = GensimWord2VecModelsSerializer()
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(Path(tmp_dir) / 'model.w2v', 'wb') as f:
                dump(self.wv_model, f)

            with open(Path(tmp_dir) / 'model.w2v', 'rb') as f:
                recovered_wv_model = load(f)

        self.assertTrue((self.wv_model.wv['one'] == recovered_wv_model.wv['one']).all())

    @mock.patch('mlio.io.serializers.base.get_installed_module_version')
    def test_dump_load_string(self, mocked_get_installed_module_version):
        mocked_get_installed_module_version.return_value = packaging.version.parse('0.14.1')
        ser = GensimWord2VecModelsSerializer()
        payload = ser.dumps(self.wv_model)
        recovered_wv_model = ser.loads(payload)
        self.assertTrue((self.wv_model.wv['one'] == recovered_wv_model.wv['one']).all())

        self.assertEqual(len(ser.get_context_dependencies()), 1)
        self.assertEqual(ser.get_context_dependencies()[0].dependency_id(), "module-version:gensim-~=0.14.1")


if __name__ == '__main__':
    unittest.main()
