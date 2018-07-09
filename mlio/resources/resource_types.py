import logging as _logging
from functools import partial
import json

from mlio import io as mlio

from .exceptions import AlreadyBoundResourceError, UnboundResourceError, ResourceNotFoundError, ResourceNotLoadedError


logger = _logging.getLogger(__name__)


class ResourceBase(object):
    """
    Base class for implementing a resource that is persisted in a repository
    """

    def __init__(self, resource_id, filename):
        self._id = resource_id
        self.filename = filename
        self._manager = None

    @property
    def id(self):
        """:rtype: str"""
        return self._id

    @property
    def manager(self):
        """
        Get the bound resource manager. If not bound with a manager it will raise exception
        :rtype: mlio.resources.base.ResourceManager
        """
        if self._manager is None:
            raise UnboundResourceError("Cannot access resource manager of unbound resource '{}'".format(self.id))
        return self._manager

    def bind_manager(self, manager):
        """
        Bind a manager on the current resource object.
        :param mlio.resources.base.ResourceManager manager: The resource manager to bind on this
        resource at.
        """
        if self._manager is not None:
            raise AlreadyBoundResourceError("Tried to re-bind resource '{}' on a resource manager".format(self.id))
        logger.debug("Resource[{s.id}]: Bound to manager '{manager}'".format(s=self, manager=manager))
        self._manager = manager

    def load(self, reload=False):
        """
        Find and load the resource from the repositories
        :param bool reload: If True it will reload the resource even if it is already loaded
        """
        if self.is_loaded() and not reload:
            return  # Already loaded

        repository = self.manager.repositories.which(self.filename)
        if not repository:
            error_msg = "Resource[{s.id}]: Cannot find resource file \"{s.filename}\" in any repository".format(s=self)
            logger.warning(error_msg)
            raise ResourceNotFoundError(error_msg)

        resource_obj = self._load_object_impl(partial(repository.open, filename=self.filename))
        logger.info("Resource[{s.id}]: Loaded resource from repository '{r.id}'".format(s=self, r=repository))

        # Store to current object
        self.update_object(resource_obj)

    def dump(self, repository_id):
        """
        Dump current in-memory object into a repository
        :param str repository_id: The id of the repository to store the copy of the resource.
        """
        if not self.is_loaded():
            raise ResourceNotLoadedError("Resource[{s.id}]: Cannot dump a resource that is not loaded yet."
                                         .format(s=self))

        repository = self.manager.repositories[repository_id]

        logger.info("Resource[{s.id}]: Dumping resource to repository '{repository_id}'".format(
            s=self, repository_id=repository_id))

        self._dump_object_impl(
            obj=self.object,
            opener=partial(repository.open, filename=self.filename),
        )

    def update_object(self, obj):
        """
        Update the in-memory copy of the resource
        :rtype T obj: The new version of the object
        """
        setattr(self, 'resource_obj', obj)

    def _load_object_impl(self, opener):
        """
        The actual object loader that must be implemented by the subclass
        :param ()->typing.IO opener: A callable that can be used to open the resource. It is already bound with the
        filename and repository that must open and accepts arguments 'mode' and 'encoding' as defined in
        RepositoryBase.open()
        :return: The loaded object
        :rtype: T
        """
        raise NotImplementedError()

    def _dump_object_impl(self, obj, opener):
        """
        The actual object dumper that must be implemented by the subclass
        :param T obj: The actual object that must be dumped in the file.
        :param ()->typing.IO opener: A callable that can be used to open the resource. It is already bound with the
        filename and repository that must open and accepts arguments 'mode' and 'encoding' as defined in
        RepositoryBase.open()
        """
        raise NotImplementedError()

    def is_loaded(self):
        """
        Check if the resource is already loaded
        :rtype: bool
        """
        return hasattr(self, 'resource_obj')

    @property
    def object(self):
        """
        Get in-memory access of the resource object. If it is not loaded in memory it will try to reso
        :return: In-memory object of the resource
        """
        self.load()
        return getattr(self, 'resource_obj')

    def __str__(self, **extras):
        extras_str = " ".join(map(lambda item: "{item[0]}='{item[1]}'".format(item=item), extras.items()))
        return "<{s.__class__.__name__}[{s.id}] filename='{s.filename}'{extras} {bound}>".format(
            s=self,
            extras=" " + extras_str if extras else '',
            bound="BOUND" if self._manager is not None else 'UNBOUND'
        )

    def __repr__(self):
        return self.__str__()


class VocabularyResource(ResourceBase):
    """
    Resource handler for vocabularies.

    A vocabulary is a set of unique entities stored per line in a text file.
    """

    def __init__(self, *args, transformer=None, **kwargs):
        """
        :param args:
        :param (str)-> str transformer: A callable to transform vocabulary entries before storing them in memory.
        By default it uses str.lower.
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self._transformer = str.lower
        if transformer is not None:
            self._transformer = transformer

    def update_object(self, obj):
        # Check the type of the object
        if not isinstance(obj, set):
            raise TypeError("Expected 'set' type but instead '{}' was given.".format(type(obj)))
        super(VocabularyResource, self).update_object(obj)

    def _load_object_impl(self, opener):
        with opener(mode='r', encoding='utf-8') as f:
            return set(filter(None, (self._transformer(word).strip() for word in f if word)))

    def _dump_object_impl(self, obj, opener):
        with opener(mode='w', encoding='utf-8') as f:
            for entry in obj:
                print(entry.lower().strip(), file=f)


class MLIOResource(ResourceBase):
    """
    Resource handler for MLIO objects
    """

    def __init__(self, *args, slot_key=None, **kwargs):
        """
        Initialize the mlio resource handler
        :param str slot_key: The slot key to use for loading from mlio pack. If None it will use the default key.
        """
        super(MLIOResource, self).__init__(*args, **kwargs)
        self._slot_key = slot_key

    @property
    def slot_key(self):
        """:rtype: str"""
        return self._slot_key

    def _load_object_impl(self, opener):
        with opener(mode='rb') as f:
            if self._slot_key is None:
                return mlio.load(f)
            else:
                return mlio.load(f, slot_key=self._slot_key)

    def _dump_object_impl(self, obj, opener):
        # It seems that in python 3.6 you cannot open('a+b') and have random access
        # The following hack is a trick to assure that will open binary files without truncating them.
        opener(mode='a+').close()

        with opener(mode='r+b') as f:
            if self._slot_key is None:
                return mlio.dump(obj, f)
            else:
                return mlio.dump(obj, f, slot_key=self._slot_key)

    def __str__(self):
        return super(MLIOResource, self).__str__(slot_key=str(self._slot_key))


class DictionaryResource(ResourceBase):
    """
    Resource handler for text dictionary

    Dictionaries are expected to be stored in json format as dictionaries
    """

    def _load_object_impl(self, opener):
        with opener(mode='rt', encoding='utf-8') as f:
            return json.load(f)

    def update_object(self, obj):
        # Check the type of the object
        if not isinstance(obj, dict):
            raise TypeError("Expected dict type but instead '{}' was given.".format(type(obj)))
        super(DictionaryResource, self).update_object(obj)

    def _dump_object_impl(self, obj, opener):

        with opener(mode='wt', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False)
