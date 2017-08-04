import unittest
from xgboost import XGBClassifier
from gensim.models import Word2Vec
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier


from ml_utils.io.serializers._registry import (get_serializer_by_type, find_suitable_serializer, UnknownSerializer,
                                               register_serializer)
from ml_utils.io.serializers.base import SerializerBase
from ml_utils.io.serializers.generic import DefaultSerializer, GenericMLModelsSerializer
from ml_utils.io.serializers.gensim import GensimWord2VecModelsSerializer


from tests.io.generic import GenericObject
from tests.io.serializers.data import RING_VERSE


class IntSerializer(SerializerBase):
    """
    Custom Int serializer
    """
    @classmethod
    def serializer_type(cls):
        return 'int'

    @classmethod
    def can_serialize(cls, obj):
        return isinstance(obj, int)


class SerializersRegistryTestCase(unittest.TestCase):

    def test_get_serializer_by_id(self):

        gensim_ser_class = get_serializer_by_type('gensim-word2vec')
        self.assertIs(gensim_ser_class, GensimWord2VecModelsSerializer)

        default_ser_class = get_serializer_by_type('default')
        self.assertIs(default_ser_class, DefaultSerializer)

    def test_get_serializer_by_id_unknown(self):

        with self.assertRaises(UnknownSerializer):
            get_serializer_by_type('unknown')

    def test_find_suitable_serializer(self):

        skreg = LinearRegression()
        skclf = RandomForestClassifier()
        xgboost = XGBClassifier()
        obj1k = GenericObject(1000)
        np_array = np.random.rand(1, 1000, 2000)
        wv_model = Word2Vec(RING_VERSE, size=10, window=3, min_count=1, workers=4)

        self.assertIs(find_suitable_serializer(skreg),
                      GenericMLModelsSerializer)
        self.assertIs(find_suitable_serializer(skclf),
                      GenericMLModelsSerializer)
        self.assertIs(find_suitable_serializer(xgboost),
                      GenericMLModelsSerializer)
        self.assertIs(find_suitable_serializer(obj1k),
                      DefaultSerializer)
        self.assertIs(find_suitable_serializer(np_array),
                      GenericMLModelsSerializer)
        self.assertIs(find_suitable_serializer(wv_model),
                      GensimWord2VecModelsSerializer)

    def test_custom_serializer(self):

        skreg = LinearRegression()
        skclf = RandomForestClassifier()
        i = 1

        self.assertIs(find_suitable_serializer(skreg),
                      GenericMLModelsSerializer)
        self.assertIs(find_suitable_serializer(skclf),
                      GenericMLModelsSerializer)
        self.assertIs(find_suitable_serializer(i),
                      DefaultSerializer)

        register_serializer(IntSerializer)

        self.assertIs(find_suitable_serializer(skreg),
                      GenericMLModelsSerializer)
        self.assertIs(find_suitable_serializer(skclf),
                      GenericMLModelsSerializer)
        self.assertIs(find_suitable_serializer(i),
                      IntSerializer)


if __name__ == '__main__':
    unittest.main()
