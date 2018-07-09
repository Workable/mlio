# ML I/O 
MLIO is a toolkit for easy I/O operations on machine learning projects. It tries to solve the problem of unified
serialization framework as well as that of resource discovery and loading for local or remote storages.

## Installation

MLIO is written on _Python >=3.6_ and can be installed using `pip` either from public 
[PyPI](https://test.pypi.org/project/pypi/) index or from git repository:

```sh
pip install mlio
```

## Usage
MLIO is split in two independent modules, the one is for asset management and the other for serialization. In a
typical ML project usually both layers are needed.

 * [Resources](docs/Resources.md): Registry of resource objects that are dynamically discovered and loaded from 
 a prioritized list of sources, called repositories.
 * [IO](docs/IO.md): The raw interface to serialize models and data to filesystem.

## License

See the [LICENSE](LICENSE.md) file for license rights and limitations (MIT).
