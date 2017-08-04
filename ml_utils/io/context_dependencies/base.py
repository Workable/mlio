import copy


class ContextDependencyBase(object):
    """
    Context dependency base class
    """

    def __init__(self, **params):
        """
        Default constructor that will forward all keyword arguments as dependency parameters
        :param params:
        """
        self._params = {}
        self.set_params(**params)

    def set_params(self, **kwargs):
        """
        Set the parameters of this context dependency
        :param kwargs: Parameters are expected in keyword argument format
        """
        self._params.update(kwargs)

    def get_params(self):
        """
        Get all the parameters of the context dependency
        :return: A dictionary with all parameters (values MUST be jsonable)
        :rtype: dict
        """
        return self._params

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            if attr in self._params:
                return self._params[attr]
            raise  # If not found in our dictionary just re-reraise

    @classmethod
    def dependency_type(cls):
        """
        Get the identifier of the type
        :rtype: str
        """
        raise NotImplementedError()

    def dependency_id(self):
        """
        The dependency id of the described dependecy. The id must be unique but must collide with dependencies
        of the same type of different instances
        :rtype: str
        """
        raise NotImplementedError()

    def is_satisfied(self):
        """
        Check if this dependency is satisfied under the current execution context
        :rtype: bool
        """
        raise NotImplementedError()

    def to_dict(self):
        """
        Convert dependency to dictionary representation format that is json compatible
        :rtype: dict
        """
        document = copy.deepcopy(self.get_params())
        document['type'] = self.dependency_type()
        return document

    @classmethod
    def from_dict(cls, data):
        """
        Reconstruct object from a dictionary representation object
        :param dict data: The data as were encoded by to_dict
        :return: A newly constructed object that has these parameters
        :rtype: ContextDependencyBase
        """
        if data.get('type', None) != cls.dependency_type():
            raise ValueError("The provided data where not of the same dependency type.")

        # Filter out the type entry
        copied_data = {
            k: v
            for k, v in data.items()
            if k != 'type'
        }

        dependency = cls(**copied_data)
        return dependency
