from ._registry import get_serializer_by_id, find_suitable_serializer, register_serializer
from . import implementations

# Register serializer by importance
register_serializer(implementations.GensimWord2VecModelsSerializer)
register_serializer(implementations.GenericMLModelsSerializer)
register_serializer(implementations.DefaultSerializer)


__all__ = [
    'get_serializer_by_id',
    'find_suitable_serializer',
    'register_serializer'
]