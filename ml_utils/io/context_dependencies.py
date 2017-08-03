import packaging.version
import packaging.specifiers
import importlib


def get_installed_module_version(module_name):
    """
    Get the installed version of a module
    :param str module_name: The name of the root package
    :return: The version as declared inside the source code
    :rtype: str
    """
    module = importlib.import_module(module_name)
    return packaging.version.parse(module.__version__)


class ContextDependencyBase(object):
    """
    Generic context dependency base class
    """

    @classmethod
    def dependency_type(cls):
        raise NotImplementedError()

    def is_satisfied(self):
        raise NotImplementedError()

    def dependency_id(self):
        """
        The dependency id of the described dependecy. The id must be unique but must collide with dependencies
        of the same type of different instances
        :rtype: str
        """
        raise NotImplementedError()


class ModuleVersionContextDependency(object):

    def __init__(self, module_name, accepted_versions):
        """
        Initialize a module version context dependency
        :param str module_name: The name of the module
        :param str accepted_versions:
        """
        self.module_name = module_name
        self.version_specs = packaging.specifiers.SpecifierSet(accepted_versions)

    @classmethod
    def dependency_type(cls):
        return 'module-version'

    def is_satisfied(self):
        """
        Check if the dependency is satisfied in current running context
        :rtype: bool
        """
        current_version = get_installed_module_version(self.module_name)
        return current_version in self.version_specs

    def dependency_id(self):
        return "{s.module_name!s}-{s.version_specs!s}".format(s=self)

    def __str__(self):
        return "Module {s.module_name!s} must be of version: {s.version_specs!s}".format(s=self)
