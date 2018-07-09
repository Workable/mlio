import os
import logging as _logging
from collections import OrderedDict

from .exceptions import RepositoryReadOnlyError, RepositoryPathTraversalError


logger = _logging.getLogger(__name__)


class RepositoryBase(object):
    """
    Base class for implementing repository handlers
    """

    def __init__(self, repository_id, writable=False):
        """
        Initialize the repository handler
        :param str repository_id: The unique id of the repository
        :param bool writable: A flag if this repository can be written
        """
        self._id = repository_id
        self._writable = bool(writable)

    @property
    def id(self):
        """:rtype: str"""
        return self._id

    @property
    def is_writable(self):
        """:rtype: bool"""
        return self._writable

    def has(self, filename):
        """
        Check that this repository has a file
        :param str filename: The relative file path of the looking file.
        :rtype: bool
        """
        raise NotImplementedError()

    def open(self, filename, mode='r', encoding=None,):
        """
        Open a file-like object for a filename in the repository
        :param str filename: The filename in the repository
        :param str mode: The opening mode. See python builtin open()
        :param str encoding: The encoding to be used for text files. See python builtin open()
        :rtype: typing.IO[bytes] | typing.IO[str]
        """
        if not self.is_writable and ('w' in mode or '+' in mode or 'a' in mode):
            error_msg = "Repository[{s.id}]: Cannot open filename '{filename}' for writing because " \
                        "repository is readonly".format(s=self, filename=filename)
            logger.error(error_msg)
            raise RepositoryReadOnlyError(error_msg)

        logger.debug("Repository[{s.id}]: Requested to open '{filename}' with mode='{mode}', encoding='{encoding}')"
                     .format(s=self, filename=filename, mode=mode, encoding=encoding))
        return self._open_impl(
            filename=filename,
            mode=mode,
            encoding=encoding
        )

    def _open_impl(self, filename, mode='r', encoding=None):
        """
        The actual file opener that must be implemented by the subclass

        See RepositoryBase.open() for description of function arguments as it follows exactly the same API.
        """
        raise NotImplementedError()

    def __str__(self, **extras):
        extras_str = " ".join(map(lambda item: "{item[0]}='{item[1]}'".format(item=item), extras.items()))
        return "<{s.__class__.__name__}[{s.id}]{extras}{readonly}>".format(
            s=self,
            extras=" " + extras_str if extras else '',
            readonly=' Read-Only' if not self.is_writable else ''
        )

    def __repr__(self):
        return self.__str__()


class LocalDirectoryRepository(RepositoryBase):
    """
    Repository based on a directory of the local filesystem

    The repository has path traversal protection, and will auto-create directories when a relative
    path is opened for any kind of writing mode.
    """

    def __init__(self, repository_id, directory_path, writable=False):
        """
        Initialize repository handler
        :param str repository_id: The unique id of the repository
        :param str | os.PathLike directory_path: The path of the directory on the local filesystem
        :param bool writable: A flag if this repository can be written
        """
        super(LocalDirectoryRepository, self).__init__(repository_id=repository_id, writable=writable)

        directory_path = os.path.abspath(directory_path)
        if not os.path.isdir(directory_path):
            raise ValueError("Repository[{s.id}]: Cannot access directory: {dir_path}".format(
                s=self,
                dir_path=directory_path))

        self._directory_path = directory_path

    @property
    def directory_path(self):
        """:rtype: str"""
        return self._directory_path

    def _file_absolute_path(self, filename):
        """
        Get the full absolute path of a filename
        :param str filename: The filename of the path
        :rtype: str
        """
        while filename.startswith('/'):
            filename = filename[1:]
        result_path = os.path.abspath(os.path.join(self.directory_path, filename))

        # Check that the final path is inside our repository
        if self.directory_path != os.path.commonprefix([result_path, self.directory_path]) or \
                result_path == self.directory_path:
            raise RepositoryPathTraversalError("Filename '{}' tried to violate directory path".format(filename))

        return result_path

    def has(self, filename):
        return os.path.isfile(self._file_absolute_path(filename))

    def _open_impl(self, filename, mode='r', encoding=None):
        full_path = self._file_absolute_path(filename)
        logger.debug("Repository[{s.id}]: Resolved '{filename}' under path '{full_path}'"
                     .format(s=self, filename=filename, full_path=full_path))

        # Auto create sub-directories if they do not exist
        if 'w' in mode or 'a' in mode:
            dir_path = os.path.dirname(full_path)
            if not os.path.exists(dir_path):
                logger.debug("Repository[{s.id}]: Creating non-existing sub-path '{dir_path}'".format(
                    s=self, dir_path=dir_path))
                os.makedirs(dir_path, exist_ok=True)

        return open(self._file_absolute_path(filename), mode=mode, encoding=encoding)

    def __str__(self):
        return super(LocalDirectoryRepository, self).__str__(directory=str(self.directory_path))


class RepositoriesContainer(object):
    """
    Container of repositories respecting a priority list on access time.
    """

    def __init__(self):
        """
        Initialize an empty container
        """
        self._repos_by_id = OrderedDict()

    def has(self, repository_id):
        """
        Check that a repository with a specific id exists in container
        :param str repository_id: The id of the repository
        :rtype: bool
        """
        return repository_id in self._repos_by_id

    def where(self, filename):
        """
        It will try to find a filename in repositories respecting the list of repositories
        :param str filename: The filename we are looking for
        :return: A list of repository ids that the filename was found. First item is of the highest priority
        :rtype: list[RepositoryBase]
        """
        return [
            repository
            for repository in self._repos_by_id.values()
            if repository.has(filename)
        ]

    def which(self, filename):
        """
        Get the first repository that has the requested filename. If not found it will return None
        :rtype: None | RepositoryBase
        """
        repos = self.where(filename=filename)
        if not repos:
            return None
        return repos[0]

    def _add(self, repository, add_last=True):
        """
        Add a repository in the container
        :param RepositoryBase repository: The repository object to be added
        :param bool add_last: If true it will be added in the end of the list otherwise it will be first.
        """

        if repository.id in self._repos_by_id:
            raise KeyError("RepositoryBase already exists with id: {}".format(repository.id))

        self._repos_by_id[repository.id] = repository
        self._repos_by_id.move_to_end(repository.id, last=add_last)

    def add_last(self, repository):
        """
        Add a repository in the end of the container (lowest priority)
        :param RepositoryBase repository: The repository object to be added
        """
        self._add(repository=repository, add_last=True)

    def add_first(self, repository):
        """
        Add a repository at the beginning of the container (highest priority)
        :param RepositoryBase repository: The repository object to be added
        """
        self._add(repository=repository, add_last=False)

    def __contains__(self, item):
        return item in self._repos_by_id

    def __iter__(self):
        return iter(self._repos_by_id.values())

    def __getitem__(self, item):
        """:rtype: RepositoryBase"""
        return self._repos_by_id[item]

    def __len__(self):
        return len(self._repos_by_id)

    def __str__(self):
        return "<RepositoryContainer: #{total} repositories>".format(total=len(self))

    __repr__ = __str__
