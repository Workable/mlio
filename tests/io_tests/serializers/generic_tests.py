import unittest
import tempfile
import io as sys_io
import packaging
from unittest import mock

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
import numpy as np

from mlio.io.serializers.generic import (DefaultSerializer, GenericMLModelsSerializer)
from tests.io_tests.generic import GenericObject


class DefaultSerializerTestCase(unittest.TestCase):

    def setUp(self):
        self.skreg = LinearRegression()
        self.skclf = RandomForestClassifier()
        self.xgboost = XGBClassifier()
        self.obj1k = GenericObject(1000)

    def test_class_method(self):

        self.assertTrue(DefaultSerializer.serializer_type(), 'default')

    def test_can_process(self):

        self.assertTrue(DefaultSerializer.can_serialize(int(1)))
        self.assertTrue(DefaultSerializer.can_serialize(int))
        self.assertTrue(DefaultSerializer.can_serialize("alala"))
        self.assertTrue(DefaultSerializer.can_serialize(self.skreg))
        self.assertTrue(DefaultSerializer.can_serialize(self.skclf))
        self.assertTrue(DefaultSerializer.can_serialize(self.xgboost))

    def test_dump_load_file(self):

        ser = DefaultSerializer()
        with tempfile.TemporaryFile('w+b') as tf:

            ser.dump(self.obj1k, tf)
            tf.seek(0, sys_io.SEEK_SET)
            recovered_obj1j = ser.load(tf)
        self.assertDictEqual(self.obj1k.data, recovered_obj1j.data)

        self.assertEqual(len(ser.get_context_dependencies()), 0)

    def test_dump_load_bytes(self):

        ser = DefaultSerializer()

        payload = ser.dumps(self.obj1k)
        self.assertIsInstance(payload, bytes)

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

        self.assertTrue(GenericMLModelsSerializer.serializer_type(), 'generic-ml-models')

    def test_can_process(self):

        # Expected to be processed
        self.assertTrue(GenericMLModelsSerializer.can_serialize(self.skreg))
        self.assertTrue(GenericMLModelsSerializer.can_serialize(self.skclf))
        self.assertTrue(GenericMLModelsSerializer.can_serialize(self.xgboost))
        self.assertTrue(GenericMLModelsSerializer.can_serialize(self.np_array))

        # Anything else
        self.assertFalse(GenericMLModelsSerializer.can_serialize(1))
        self.assertFalse(GenericMLModelsSerializer.can_serialize(int))
        self.assertFalse(GenericMLModelsSerializer.can_serialize("alala"))

    @mock.patch('mlio.io.serializers.base.get_installed_module_version')
    def test_dump_load_file(self, mocked_get_installed_module_version):
        mocked_get_installed_module_version.return_value = packaging.version.parse('0.12.1')

        ser = GenericMLModelsSerializer()
        with tempfile.TemporaryFile('w+b') as tf:
            ser.dump(self.np_array, tf)
            tf.seek(0, sys_io.SEEK_SET)
            recovered_np_array = ser.load(tf)
        self.assertTrue(np.all(self.np_array == recovered_np_array))

        self.assertEqual(len(ser.get_context_dependencies()), 1)
        self.assertEqual(ser.get_context_dependencies()[0].dependency_id(), "module-version:numpy-~=0.12.1")

    @mock.patch('mlio.io.serializers.base.get_installed_module_version')
    def test_dump_load_string(self, mocked_get_installed_module_version):
        mocked_get_installed_module_version.return_value = packaging.version.parse('0.12.1')
        ser = GenericMLModelsSerializer()
        payload = ser.dumps(self.np_array)
        recovered_np_array = ser.loads(payload)
        self.assertTrue(np.all(self.np_array == recovered_np_array))

        self.assertEqual(len(ser.get_context_dependencies()), 1)
        self.assertEqual(ser.get_context_dependencies()[0].dependency_id(), "module-version:numpy-~=0.12.1")


if __name__ == '__main__':
    unittest.main()
