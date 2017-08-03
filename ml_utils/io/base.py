import importlib
from datetime import datetime

from .serializers import get_serializer_by_id


class MLIOError(IOError):
    """
    Base class for ML loading/unloading errors
    """


class MLIOPackWrongFormat(MLIOError):
    """
    Exception to be raised in case of load error
    """
    pass


class ModelVersionError(MLIOError):
    """
    Exception to be raised in case of model version error
    """
    pass


def assert_versions_match(expected, actual):
    """
    Compares two different dictionaries containing module and protocol versions. Raises a ModelLoadError
    if there's an inconsistency.
    :param dict expected: the expected versions.
    :param dict actual:  the actual versions.
    :
    """

    # Check protocol versions
    if expected.get('version') != actual.get('version'):
        raise ModelVersionError(
            "File was packed with an older version: {}".format(actual.get('version')))

    # Check modules version
    expected_module_versions = expected.get('modules', {})
    actual_module_versions = actual.get('modules', {})
    for module_name, packed_version in actual_module_versions.items():
        installed_version = expected_module_versions.get(module_name, None)
        if installed_version != packed_version:
            raise ModelVersionError(
                "Different version of module \"{module}\" was used to pack the model."
                "Packed version: {packed}, Installed version: {installed}".format(
                    module=module_name,
                    packed=packed_version,
                    installed=installed_version
                ))


