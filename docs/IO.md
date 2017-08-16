## I/O Module
Toolkit to load and store ML related objects in files. The toolkit was initially designed to store trained models. 

## Interoperability
MLIO is similar to `pickle`, `joblib`, `json` etc, but instead of specializing in one
type of data model it follows different paths depending the type.

For an example if you try to dump a pure python object it will use `pickle` while
if you try to save [gensim](https://radimrehurek.com/gensim/) Word2Vec model
it will use `Word2Vec.load` method that is specialized for this purpose. All this
magic is performed transparently at `load` and `dump`.

## Execution context dependencies
Many python serializers like `pickle` or `joblib` depend on the state of execution
enviroment at the time of serialization. For example not all objects pickled with python 2
can be unpickled on python 3 environment. Another case is an object pickled with `sklearn 0.18` may not
work with `sklearn 0.19`. For this reason many of these libraries warn you that serialization-deserialization
must be performed in the same execution context.
 
MLIO comes with dependency descriptors that are automatically applied at
serialization stage. On de-serialization stage, **all dependencies are validated** in the
current execution environment and it will early-warn the user before execution reaches
an unstable state.

## Multi-slot pack of objects
MLIO stores objects in packs, where each object has its dedicated slot identified by an arbitrary string. 
The final pack is a zip file with a specific internal layout.

Some features of this pack format are:
* **data deduplication**: When two or more slots hold the same data, then only copy of them is stored in the pack.
This is specially useful if you want to create cheap slot alias.
* **data validation**: The sha256 hash of objects is stored along with their data. At de-serialization stage the 
data are validated.

## Simple API
MLIO API is simple and straigh-forward. The basic object `Pack`, is used to handle file-based object storages. There 
is no pack creation or initialization stage, as long as you have a file handler, you can use it as MLIO `Pack` object.

### Dump, load and remove an object
```python

from ml_utils.io import Pack

m1 = ...
m2 = ...
# Store objects in a new or existing pack file
with open('thefile', 'w+b') as f:
    with Pack(f) as pck:
        pck.dump('object-1', m1)
        pck.dump('object-2', m2)
    
...
# Recover objects
with open('thefile', 'r+b') as f:
    with Pack(f) as pck:
        if 'object-1' not in pck:
            raise RuntimeError('Cannot find object-1')
        m1_recovered = pck.load('object-1')
        
        if 'object-2' not in pck:
            raise RuntimeError('Cannot find object-2')
        m2_recovered = pck.load('object-2')
        
        # Delete one object
        pck.remove('object-1')
```

### Query metadata
```python
from ml_utils.io import Pack

# Open a pack file and read metadata
with open('thefile', 'w+b') as f:
    with Pack(f) as pck:
        print("Pack was created at: {}".format(pck.manifest_info.created_at))
        print("Pack was updated at: {}".format(pck.manifest_info.updated_at))
        print("Slots:")
        for slot_id, slot_info in pck.slots_info.items():
            print("{}: Serializer: {}, Hash: {}".format(slot_id, slot_info.serializer, slot_info.serialized_sha256_hash))
```

### Compatibility API
The MLIO can be used as a drop-in replacement for `pickle`, `json` or ect but it does not support the mutli-slot API. 
Still though packs that are created with compatibility API are fully compatible with the classic API.

 
 ```python
# Instead of pickle
# from pickle import load, dump

# MLIO can be used in the same way
from ml_utils.io import load, dump

model = Model()
with open('thefile', 'w+b') as f:
    dump(model, f)
    
with open('thefile', 'r+b') as f:
    model_recovered = load(f)
```
