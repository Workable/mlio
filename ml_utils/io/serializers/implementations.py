import pickle
import io as sys_io
import shutil
from tempfile import TemporaryFile, NamedTemporaryFile

import joblib

from ..context_dependencies import ModuleVersionContextDependency, get_installed_module_version


def get_object_root_module(obj):
    """
    Get the obj module version
    :param T obj: Any object
    :rtype: str
    :return The root module of the object's type
    """
    return type(obj).__module__.split('.')[0]


class SerializerBase(object):
    """
    Base class for defining a serializer
    """

    def __init__(self):
        """
        Default constructor
        """
        self._context_dependencies = []

    def get_context_dependencies(self):
        """
        Get the list with all context dependencies
        :rtype: list[ml_utils.io.context_dependencies.ContextDependencyBase]
        """
        return self._context_dependencies

    def reset_context_dependencies(self):
        """
        Reset the list of context dependencies
        """
        self._context_dependencies = []

    def _add_module_version_dependency(self, module_name, version_spec=None):
        """
        Add context dependency for a specific module version
        :param str module_name: The name of the module to add dependency
        :param str|None version_spec: The specification of the version as defined by PEP440, if None
         it will try to resolve the current running version
        """
        if version_spec is None:
            version_spec = "~={!s}".format(get_installed_module_version(module_name))

        self._context_dependencies.append(
            ModuleVersionContextDependency(module_name, version_spec)
        )

    def _add_current_python_version_dependency(self, version_spec=None):
        """
        Add context dependency for current python version
        :param str|None version_spec: The specification of the version as defined by PEP440, if None
         it will try to resolve the current running version
        """
        raise NotImplementedError()
        if version_spec is None:
            version_spec = "~={!s}".format(get_installed_module_version(module_name))

        self._context_dependencies.append(
            ModuleVersionContextDependency(module_name, version_spec)
        )

    @classmethod
    def serializer_id(cls):
        """
        Get a unique id for the serializer type
        :return:
        """
        raise NotImplementedError()

    @classmethod
    def can_process(cls, obj):
        """
        Check if this serializer can serialize a specific type of object
        :param T obj: The object to be serialized
        :rtype: True
        """
        raise NotImplementedError()

    def load(self, fh):
        """
        Load an object from a serialized format in the filesystem
        :param typing.IO fh: File-like object
        :return: The recovered object
        :rtype: T
        """
        raise NotImplementedError()

    def dump(self, obj, fh):
        """
        Save an object to a serialized format in the filesystem
        :param T obj: The object to save on the filesystem.
        :param typing.IO fh: File-like object
        """
        raise NotImplementedError()

    def loads(self, payload):
        """
        Same as load() but it will read the serialized format from a string
        :param str payload: The serialized payload
        :return: The recovered object
        :rtype: T
        """
        raise NotImplementedError()

    def dumps(self, obj):
        """
        Same as dump() but it will return the serialized format in a string
        :param T obj: The object to serialize
        :return: The serialized payload
        :rtype: str
        """
        raise NotImplementedError()


class EmulateStringOperationsMixIn(object):
    """
    MixIn for serializers to add (emulated) support for load and dump on strings
    """

    def dumps(self, obj):
        with TemporaryFile("w+b") as f:
            self.dump(obj, f)
            f.seek(0, sys_io.SEEK_SET)
            return f.read()

    def loads(self, payload):
        with TemporaryFile("w+b") as f:
            f.write(payload)
            f.seek(0, sys_io.SEEK_SET)
            return self.load(f)


class DefaultSerializer(EmulateStringOperationsMixIn, SerializerBase):
    """
    Default serializer for anything based on pickle
    """

    @classmethod
    def serializer_id(cls):
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
    def can_process(cls, obj):
        return True


class GenericMLModelsSerializer(EmulateStringOperationsMixIn, SerializerBase):
    """
    Generic ML serializer that will acccept sklearn, numpy and xgboost objects of any type.
    It uses joblib to perform the operation
    """

    @classmethod
    def serializer_id(cls):
        return 'generic-ml-models'

    def dump(self, obj, fh):
        self._add_module_version_dependency(
            get_object_root_module(obj)
        )
        return joblib.dump(obj, fh)

    def load(self, fh):
        return joblib.load(fh)

    @classmethod
    def can_process(cls, obj):
        return get_object_root_module(obj) in {'sklearn', 'numpy', 'xgboost'}


class GensimWord2VecModelsSerializer(SerializerBase):
    """
    Gensim Word2Vec specific serializer. It will use gensim's internal function to load and store model
    """
    @classmethod
    def serializer_id(cls):
        return 'gensim-word2vec'

    def _add_gensim_module_version_dependency(self):
        """
        Add a dependency on the exact current version of gensim
        """
        self._add_module_version_dependency(
            'gensim',
            None
        )

    def dump(self, obj, fh):
        self._add_gensim_module_version_dependency()
        return obj.save(fh)

    def load(self, fh):
        from gensim.models import Word2Vec

        with NamedTemporaryFile('w+b') as temp_fh:
            shutil.copyfileobj(fh, temp_fh)
            temp_fh.flush()
            return Word2Vec.load(temp_fh.name)

    def dumps(self, obj):
        self._add_gensim_module_version_dependency()

        # Create a temporary file and ask Word2Vec to write on this file
        with NamedTemporaryFile("r+b") as temp_fh:
            obj.save(temp_fh.name)
            # Read contents
            return temp_fh.read()

    def loads(self, payload):
        from gensim.models import Word2Vec

        # Create temporary file and dump payload
        with NamedTemporaryFile("r+b") as temp_fh:
            temp_fh.write(payload)
            temp_fh.flush()
            # Ask gensim to load model from file-system
            return Word2Vec.load(temp_fh.name)
        
    @classmethod
    def _is_gensim_word2vec(cls, obj):
        """
        Check if it is a Word2Vec gensim model
        :param Word2Vec|T obj: Any type of object
        :rtype: bool
        """
        from gensim.models import Word2Vec
        return isinstance(obj, Word2Vec)

    @classmethod
    def can_process(cls, obj):
        # By first check the root module before import Word2Vec type. This permits to use this function
        # in python environment without gensim installed
        return get_object_root_module(obj) in {'gensim'} \
               and cls._is_gensim_word2vec(obj)
