import logging as _logging
from mlio.resources.exceptions import ResourceNotFoundError
from .repositories import RepositoriesContainer


logger = _logging.getLogger(__name__)


class ResourceManager:
    """
    A registry of resource objects that are dynamically discovered and loaded from a prioritized list of
    sources (called repositories).
    """

    def __init__(self):
        """
        Instantiate a new resource manager
        """

        self._resources = {}  # type: dict[str, mlio.resources.resource_types.ResourceBase]

        self._repositories = RepositoriesContainer()

    @property
    def repositories(self):
        """ :rtype: RepositoriesContainer """
        return self._repositories

    @property
    def resources(self):
        """ :rtype: dict[str, mlio.resources.resource_types.ResourceBase]"""
        return self._resources

    def has_resource(self, resource_id):
        """
        Check if the resource exist in the manager
        :param str resource_id: The identifier of the resource
        :rtype: bool
        """
        return resource_id in self._resources

    __contains__ = has_resource

    def add_resource(self, resource):
        """
        Add a new resource in the manager. The id of the resource must be unique in this manager and the resource
        object must not be registered in any other manager.
        :param mlio.resources.resource_types.ResourceBase resource: The resource object to be added.
        """
        if self.has_resource(resource.id):
            logger.warning("There is already a resource with this resource repository_id: {}".format(resource.id))
            raise KeyError("There is already a resource with this resource repository_id: {}".format(resource.id))

        self._resources[resource.id] = resource
        resource.bind_manager(self)
        logger.info("Resource '{}' has been added to the resource manager {}".format(resource.id, self))

    def __getitem__(self, resource_id):
        """:rtype: mlio.resources.resource_types.ResourceBase"""
        if resource_id not in self._resources:
            raise ResourceNotFoundError("Cannot find resource '{}' in resource manager".format(resource_id))
        return self._resources[resource_id].object

    def load_resources(self, resource_ids=None):
        """
        Load resource from the repository in memory. Resources that are already loaded will be skipped.
        :param None|List[str] resource_ids: If None it will try to load all resources, otherwise it will load
        only the ids of the resources that where listed
        """
        if not resource_ids:
            resource_ids = self._resources.keys()
        else:
            # Validate that all keys exist
            for resource_id in resource_ids:
                if resource_id not in self:
                    raise ResourceNotFoundError("Cannot find resource '{}' in resource manager".format(resource_id))

        for resource_id in resource_ids:
            self.resources[resource_id].load()

    def __str__(self):
        return "<ResourceManager: #{total_resources} resources in #{total_repos} repositories>".format(
            total_repos=len(self.repositories),
            total_resources=len(self._resources)
        )

    def __repr__(self):
        return self.__str__()
