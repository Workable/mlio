import io as sys_io
from tempfile import TemporaryFile

from ..context_dependencies.module_version import ModuleVersionContextDependency, get_installed_module_version


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
        Get the list with all context dependencies that where injected at serialization stage
        :rtype: list[mlio.io.context_dependencies.ContextDependencyBase]
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

    def _add_python_version_dependency(self, version_spec=None):
        """
        Add context dependency for specific python version
        :param str|None version_spec: The specification of the version as defined by PEP440, if None
         it will try to resolve the current running version
        """
        raise NotImplementedError()  # This is not an abstract method, just pending context dependency implementation

    @classmethod
    def serializer_type(cls):
        """
        Get a unique id for the serializer type
        :return:
        """
        raise NotImplementedError()

    @classmethod
    def can_serialize(cls, obj):
        """
        Check if this serializer can serialize a specific type of object
        :param T obj: The object to be serialized
        :rtype: bool
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
        Same as load() but it will read the serialized format from a bytes
        :param bytes payload: The serialized payload
        :return: The recovered object
        :rtype: T
        """
        raise NotImplementedError()

    def dumps(self, obj):
        """
        Same as dump() but it will return the serialized format in a bytes
        :param T obj: The object to serialize
        :return: The serialized payload
        :rtype: bytes
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
