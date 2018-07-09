
class RepositoryReadOnlyError(Exception):
    """
    Exception that is raised if an attempt was made to write on a readonly repository
    """


class UnboundResourceError(RuntimeError):
    """
    Exception that is raised if a resource is not bound to a manager
    """
    pass


class AlreadyBoundResourceError(RuntimeError):
    """
    Exception that is raised on binding a resource that is already bound to a manager
    """
    pass


class RepositoryPathTraversalError(PermissionError):
    """
    Exception that is raised when a relative path results in a path traversal security problem.
    """
    pass


class ResourceNotFoundError(RuntimeError):
    """
    Exception that is raised if a resource was not found
    """
    pass


class ResourceNotLoadedError(RuntimeError):
    """
    Exception that is raised if a required resource is not loaded
    """
    pass
