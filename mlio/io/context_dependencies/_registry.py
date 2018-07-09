from collections import OrderedDict

__dependency_type_registry = OrderedDict()


class UnknownContextDependencyType(KeyError):
    """
    Exception raised when an unknown context dependency was asked to be used.
    """
    pass


def get_dependency_by_type(ctx_dep_type):
    """
    Find a context dependency based on its id
    :rtype: str ctx_dep_type: The id of the serializer as it was provided by Serializer.serializer_type()
    :return: The serializer
    :rtype: mlio.io.context_dependencies.ContextDependencyBase
    """
    if ctx_dep_type in __dependency_type_registry:
        return __dependency_type_registry[ctx_dep_type]

    raise UnknownContextDependencyType("Unknown context dependency with type: {}".format(ctx_dep_type))


def register_dependency_type(ctx_dep_class):
    """
    Register a new context dependency type in registry
    :param mlio.io.context_dependencies.ContextDependencyBase ctx_dep_class: The context dependency class to
    register
    :return: The context dependency class itself, so that it can be used as class decorator function
    """

    global __dependency_type_registry
    __dependency_type_registry[ctx_dep_class.dependency_type()] = ctx_dep_class
    return ctx_dep_class
