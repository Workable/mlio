from collections import OrderedDict

__serializers_registry = OrderedDict()


class UnknownObjectType(KeyError):
    """
    Exception raised when unknown object is asked to be serialized.
    """
    pass


class UnknownSerializer(KeyError):
    """
    Exception raised when an unknown serialized was asked to be used.
    """
    pass


def find_suitable_serializer(obj):
    """
    Find serializer that is suitable for this operation
    :param T obj: The object that needs to be serialized
    :return: The first suitable serializer for this type of object
    :rtype: mlio.io.serializers.implementations.SerializerBase
    """

    for serializer in __serializers_registry.values():
        if serializer.can_serialize(obj):
            return serializer

    raise UnknownObjectType("Cannot find a suitalble serializer for object of type {}".format(type(object)))


def get_serializer_by_type(serializer_type):
    """
    Find a serialized based on its type
    :rtype: str serializer_type: The unique type of the serializer as it was provided by Serializer.serializer_type()
    :return: The serializer
    :rtype: mlio.io.serializers.implementations.SerializerBase
    """
    if serializer_type in __serializers_registry:
        return __serializers_registry[serializer_type]

    raise UnknownSerializer("Unknown serializer with id: {}".format(serializer_type))


def register_serializer(serializer):
    """
    Register a serializer in registry
    :param mlio.io.serializers.SerializerBase serializer:
    :return: The serializer itself, so that it can be used as class decorator function
    """

    global __serializers_registry
    __serializers_registry[serializer.serializer_type()] = serializer
    __serializers_registry.move_to_end(serializer.serializer_type(), last=False)

    return serializer
