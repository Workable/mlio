from ._registry import get_serializer_by_type, find_suitable_serializer, register_serializer
from . import generic, gensim

# Register serializer by importance (Last more important)
register_serializer(generic.DefaultSerializer)
register_serializer(generic.GenericMLModelsSerializer)
register_serializer(gensim.GensimWord2VecModelsSerializer)


__all__ = [
    'get_serializer_by_type',
    'find_suitable_serializer',
    'register_serializer'
]
