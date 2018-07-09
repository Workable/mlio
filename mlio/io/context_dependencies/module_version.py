import importlib
import packaging.version
import packaging.specifiers

from .base import ContextDependencyBase
from ._registry import register_dependency_type


def get_installed_module_version(module_name):
    """
    Get the installed version of a module
    :param str module_name: The name of the root package
    :return: The version as declared inside the source code
    :rtype: packaging.version.Version
    """
    module = importlib.import_module(module_name)
    return packaging.version.parse(module.__version__)


@register_dependency_type
class ModuleVersionContextDependency(ContextDependencyBase):
    """
    Context dependency to record a module version and check compatibility
    """

    def __init__(self, module_name, version_specs):
        """
        Initialize a module version context dependency
        :param str module_name: The name of the module
        :param str version_specs: Specification of accepted version. The spec must follow PEP-440
        """
        self._version_specs_obj = None
        if not module_name:
            raise ValueError("Module must be defined in order to check compatibility")
        super().__init__(module_name=module_name, version_specs=version_specs)

    @property
    def version_specs(self):
        """:rtype: packaging.specifiers.SpecifierSet """
        return self._version_specs_obj

    def set_params(self, module_name, version_specs):
        super().set_params(module_name=module_name, version_specs=version_specs)
        self._version_specs_obj = packaging.specifiers.SpecifierSet(version_specs)

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
