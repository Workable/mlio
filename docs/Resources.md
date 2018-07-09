## Resources

`Resources` package is a registry of resource objects that are dynamically discovered and loaded from a prioritized list
of sources, called repositories. In contrast with `MLIO`, which is memory type-driven serializer, `Resources` is
file format-driven that can solve the problem of efficient resource lookup and loading in memory.

**Highlight features:**
* Different resource types
* Resolution from multiple repositories
* Abstract repository concept
  - Selective write protection
  - File-like object to access filename
  - Path traversal protection
  - Auto creation of sub directories.
* Ability to declare custom resource and repository types


### The Resource
The principal concept of a resources is the `Resource`. A `Resource` is identified by an `id`, it has a specific
`filename` and when it is `loaded` it holds the reference to the memory copy, named `object`.

The life-cycle of a resource starts at the moment that it is declared in a `ResourceManager`. At this state the resource
is not loaded and it is not guaranteed that its file can be resolved. On the first request to access the `object` reference the resource
will ask the `ResourceManager` to resolve its file identified by `filename` in the registered `repositories`. If this
procedure succeeds then the copy will be persisted in memory until the end of manager's life-cycle.

#### Resource resolution

One of the main features is the ability to use multiple repositories at the same. The repositories are declared
in a priority order so that **the manager will first look on the highest priority and will continue to the rest of the
repositories until the resource is finally found**.

The resource is discovered based on its `filename` so it is critical **that two different resources should hold
two different `filename`s.**

#### Resource types
Library supports different resource types that can be loaded and dumped to files.

* `Vocabulary`: Typical text files where each lines contains a unique term.
* `Dictionaries`: A map from one term to another that are store in json format.
* `MLIO`: Objects serialized using the MLIO library. Can load and store from different keys.


### API
There are 3 basic concepts in the API, the `Resource`, the `Repository` and the `ResourceManager`. A manager can hold
information about multiple `Resource`s that can be looked up in multiple `Repository`s.

The intended usage is to initialize a resource manager and declare its resources and repositories so that the rest
of the application will resolve and lazily load the resource object by only referencing with their `id`.

### Example 1: Declare a manager and resolve its resources

```python
from mlio.resources import ResourceManager, repositories, resource_types

manager = ResourceManager()

# Declare resources
manager.add_resource(resource_types.DictionaryResource('word2sent', 'other/word2sent.json')
manager.add_resource(resource_types.MLIOResource('clf_for_words', 'models/classifiers.mlpck', slot_key='clf_for_words'))

# Declare repositories
manager.repositories.add_first(repositories.LocalDirectoryRepository('default_home', '~/.config/projectX'))


# ...

# To access the actual object you just need to reference wit the key
results = manager['clf_for_words'].predict(X)  # It is only at the first reference that will be loaded
```

### Example 2: Eager loading of all resources

There are some cases where we want to load all resources in memory. This is usually useful if you want to have
a predictable user-experience where at the point of request the resource is already in-memory.

Another example is to perform efficient forking. In this case we want to load all resources in memory before
actual forking happens so that the forked processes will have their resources in memory space.
In some OS, like Linux, the memory will not even be copied but referenced until a write operations is performed, providing
an efficient way to load the same resources in multiple processes.

```python
from mlio.resources import ResourceManager

manager = ResourceManager()

...  # Declare resources and repositories

# Ask to load all resources eagerly
manager.load_resources()
```

### Example 3: Inspect state of resources

In typical usage the item getter operator is used to fetch the actual resource object, e.g. `manager['resource id']`.
This operation triggers the chain of resource loading, unless it is already loaded, however sometimes it is desired
to only inspect the state of a resource without fetching the object.

```python
manager = ResourceManager()

...  # Declare resources and repositories

# Instead of getting the object you can get the handler using the `resources` attribute
print(manager.resources['id'].is_loaded())

# You can access the attributes of the object like `filename` or get the type
print(manager.resources['id'].filename)
print(type(manager.resources['id']))

# You can ask to load or even forcefully reload the resource
manager.resources['id'].load(reload=True)
```

### Example 4: Update the object and store in repository

Another common operation is to prepare a repository by storing resources. Resource manager
provides an API to update the memory copy of a resource and dump it in a repository. This will
respect the policies of the repository such as `read-only`, construct intermediate
folders, serialize data, and store the object in the declared `filename`.


```python
manager = ResourceManager()

...  # Declare resources and repositories

# Before writing to the repository we need to update its memory copy
manager.resources['resource_id'].update_object(new_object)

# To actually store the resource we need to select the target repository
manager.resources['resource_id'].dump('target_repo_id')

```

### Example 5: \[Advanced\] Implement custom resource type
In order to support new resource types, you need to subclass `ResourceBase` and implement
the **dumping** and **loading** functions. These functions provide a callable `opener`
that is used to open a file-like object in the repository without needed to provide the filename.

For example if we wanted to create the simple `Text` resource type.

```python
from mlio.resources.resource_types import ResourceBase

class TextResource(ResourceBase):

    def _load_object_impl(self, opener):
        with opener(mode='r', encoding='utf-8') as f:
            return f.read()

    def _dump_object_impl(self, obj, opener):
        with opener(mode='w', encoding='utf-8') as f:
            f.write(obj)
```

### Example 6: \[Advanced\] Implement custom repository type
Repositories need to implement two actions, a) check if a filename exists in the
repository, b) return a file-like object for a specific file-name. Extra checks
like path traversal are expected to be implemented in the subclass.

For example if we wanted to create a draft `Zip` repository.

```python
from mlio.resources.repositories import RepositoryBase
from zipfile import ZipFile


class ZipRepository(RepositoryBase):

    def __init__(self, repository_id, writtable, file_object):
        super().__init__(repository_id, writtable)
        self.file_object = file_object

        mode = 'a' if writtable else 'r'
        self._zip_fh = ZipFile(self._file_handler, mode)

    def has(self, filename):
        for zip_entry in self._zip_fh.infolist():
            if filename == zip_entry.filename:
                return True
        return False

     def _open_impl(self, filename, mode='r', encoding=None):
        # Extra checks are expected in a real implementation
        # Manual process the text encoding if it is provided.
        return self._zip_fh.open(filename, mode)
```
