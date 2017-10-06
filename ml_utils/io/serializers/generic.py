import pickle
import io as sys_io
from tempfile import TemporaryFile

import joblib

from .base import EmulateStringOperationsMixIn, SerializerBase, get_object_root_module


class DefaultSerializer(EmulateStringOperationsMixIn, SerializerBase):
    """
    Default serializer for anything based on pickle
    """

    @classmethod
    def serializer_type(cls):
        return 'default'

    def dump(self, obj, fh):
        pickle.dump(obj, fh)

    def load(self, fh):
        return pickle.load(fh)

    def loads(self, payload):
        with TemporaryFile("w+b") as f:
            f.write(payload)
            f.seek(0, sys_io.SEEK_SET)
            return self.load(f)

    @classmethod
    def can_serialize(cls, obj):
        return True


class GenericMLModelsSerializer(EmulateStringOperationsMixIn, SerializerBase):
    """
    Generic ML serializer that will accept sklearn, numpy and xgboost objects of any type.
    It uses joblib to perform the operation
    """

    @classmethod
    def serializer_type(cls):
        return 'generic-ml-models'

    def dump(self, obj, fh):
        self._add_module_version_dependency(
            get_object_root_module(obj)
        )
        return joblib.dump(obj, fh)

    def load(self, fh):
        return joblib.load(fh)

    @classmethod
    def can_serialize(cls, obj):
        return get_object_root_module(obj) in {'sklearn', 'numpy', 'xgboost'}
