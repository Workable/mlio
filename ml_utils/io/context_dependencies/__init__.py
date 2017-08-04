import packaging.version
import packaging.specifiers
import importlib
import copy

from ._registry import register_dependency_type, get_dependency_by_type, UnknownContextDependencyType


def get_installed_module_version(module_name):
    """
    Get the installed version of a module
    :param str module_name: The name of the root package
    :return: The version as declared inside the source code
    :rtype: packaging.version.Version
    """
    module = importlib.import_module(module_name)
    return packaging.version.parse(module.__version__)


class ContextDependencyBase(object):
    """
    Generic context dependency base class
    """

    def __init__(self, **params):
        """
        Default constructor that will
        :param params:
        """
        self._params = {}
        self.set_params(**params)

    def set_params(self, **kwargs):
        """
        Set the parameters of the context dependency
        :param kwargs: Parameters are expected in keyword argument format
        """
        self._params.update(kwargs)

    def get_params(self):
        """
        Get all the parameters of the context dependency
        :return: A dictionary with all parameters (values MUST be jsonable)
        :rtype: dict
        """
        return self._params

    def __getattr__(self, item):
        return self._params[item]

    @classmethod
    def dependency_type(cls):
        """
        Get the identifier of the type
        :rtype: str
        """
        raise NotImplementedError()

    def is_satisfied(self):
        """
        Check if this dependency is satisfied under the current execution context
        :rtype: bool
        """
        raise NotImplementedError()

    def dependency_id(self):
        """
        The dependency id of the described dependecy. The id must be unique but must collide with dependencies
        of the same type of different instances
        :rtype: str
        """
        raise NotImplementedError()

    def to_dict(self):
        """
        Convert dependency to dictionary representation format that is json compatible
        :rtype: dict
        """
        document = copy.deepcopy(self.get_params())
        document['type'] = self.dependency_type()
        return document

    @classmethod
    def from_dict(cls, data):
        """
        Reconstruct object from a dictionary representation object
        :param dict data: The data as were encoded by to_dict
        :return: A newly constructed object that has these parameters
        :rtype: ContextDependencyBase
        """
        if data.get('type', None) != cls.dependency_type():
            raise ValueError("The provided data where not of the same dependency type.")

        dependency = cls()
        dependency.set_params(**data)
        return dependency


@register_dependency_type
class ModuleVersionContextDependency(ContextDependencyBase):

    def __init__(self, module_name, accepted_versions):
        """
        Initialize a module version context dependency
        :param str module_name: The name of the module
        :param str accepted_versions: Specification of accepted version. The spec must follow PEP-440
        """
        super().__init__(module_name=module_name, accepted_versions=accepted_versions)
        self.module_name = module_name
        self.version_specs = packaging.specifiers.SpecifierSet(accepted_versions)

    def get_params(self):
        return {
            'module_name': self.module_name,
            'version_specs': self.version_specs
        }

    def set_params(self, module_name, accepted_versions, **others_kwargs):
        accepted_versions = packaging.specifiers.SpecifierSet(accepted_versions)
        super().set_params(module_name=module_name, accepted_versions=accepted_versions)

    @classmethod
    def dependency_type(cls):
        return 'module-version'

    def is_satisfied(self):
        current_version = get_installed_module_version(self.module_name)
        return current_version in self.version_specs

    def dependency_id(self):
        return "{dep_type}:{s.module_name!s}-{s.version_specs!s}".format(
            dep_type=self.dependency_type(),
            s=self)

    def __str__(self):
        return "Module {s.module_name!s} must be of version: {s.version_specs!s}".format(s=self)
