import json
import tempfile
import sys
import io as sys_io
import warnings
from zipfile import ZipFile
from datetime import datetime, timedelta, timezone

from .exc import MLIOPackWrongFormat, SlotKeyError, MLIODependenciesNotSatisfied, MLIOPackSlotWrongChecksum


class PackManifestSlot(object):
    """
    Representation model for a slot of the pack's manifest
    """

    def __init__(self, slot_key, serializer, serialized_sha256_hash, dependencies=None):
        """
        Initialize a new slot
        :param str slot_key: The unique identifier of the slot in the pack
        :param mlio.io.serializers.base.SerializerBase serializer: The serializer object that can
        be used to unserialize slot
        :param str serialized_sha256_hash: The hash of the serialized data
        :param typing.Iterable[mlio.io.context_dependencies.base.ContextDependencyBase] dependencies: A list of
        all context dependencies that this slot requires in order to un-serialize
        """
        from .context_dependencies.base import ContextDependencyBase

        if dependencies is None:
            dependencies = []

        for dep in dependencies:
            if not isinstance(dep, ContextDependencyBase):
                raise TypeError("Dependencies must be given in object instance of ContextDependecy. Instead {!r} was "
                                "given".format(dep))
        self.slot_key = slot_key
        self.serializer = serializer
        self._dependencies = {
            dep.dependency_id(): dep
            for dep in dependencies
        }
        self.serialized_sha256_hash = serialized_sha256_hash

    @property
    def dependencies(self):
        """:rtype: dict[str, mlio.io.context_dependencies.base.ContextDependencyBase]"""
        return self._dependencies

    def find_unsatisfied_dependencies(self):
        """
        Get the list with unsatisfied dependencies on the current execution context
        :return: A list with the dependencies ids
        :rtype: list[str]
        """
        return [
            dep_id
            for dep_id, dep in self.dependencies.items()
            if not dep.is_satisfied()
        ]

    @property
    def pack_object(self):
        """
        The internal name of the data object in the pack
        :rtype: str
        """
        return "{}.slot".format(self.serialized_sha256_hash)

    @classmethod
    def from_dict(cls, slot_key, data, manifest_dependencies):
        """
        Recover an instance from dictionary format
        :param str slot_key: The key of this slot
        :param dict data: Dictionary with all metadata of the manifest slot
        :param dict[str, mlio.io.context_dependencies.base.ContextDependencyBase] manifest_dependencies: All the
        dependencies declared in the PackManifest mapped by their id
        :rtype: PackManifestSlot
        """
        from .serializers import get_serializer_by_type

        # Check mandatory fields
        if 'serialized_sha256_hash' not in data:
            raise MLIOPackWrongFormat(
                "Cannot load slot: {} because it is missing hash field".format(slot_key))
        if 'serializer' not in data:
            raise MLIOPackWrongFormat(
                "Cannot load slot: {} because of unknown serializer".format(slot_key))

        # Check dependency ids
        dependencies_ids = set(data.get('dependencies', []))
        unknown_dependencies = dependencies_ids - set(manifest_dependencies.keys())
        if unknown_dependencies:
            raise MLIOPackWrongFormat("Cannot load slot: {} because of the following unknown dependencies: {}".format(
                slot_key,
                unknown_dependencies
            ))

        # Load slot
        return cls(
            slot_key=slot_key,
            serialized_sha256_hash=data['serialized_sha256_hash'],
            serializer=get_serializer_by_type(data['serializer'])(),
            dependencies=[
                manifest_dependencies[dep_id]
                for dep_id in dependencies_ids
            ])

    def to_dict(self):
        """
        Convert instance to jsonable dictionary
        :rtype: dict
        """
        return {
            'serialized_sha256_hash': self.serialized_sha256_hash,
            'serializer': self.serializer.serializer_type(),
            'dependencies': list(self.dependencies.keys())
        }


class PackManifest(object):
    """
    Representation model for Manifest registry of the pack
    """

    PROTOCOL_VERSION = 2
    MANIFEST_FILENAME = "manifest.json"

    def __init__(self, dependencies=None, slots=None, created_at=None, updated_at=None):
        """
        Initialize a new manifest instance
        :param typing.Iterable[mlio.io.context_dependencies.base.ContextDependencyBase]|None dependencies: The list
        with dependencies that this slot holds
        :param typing.Iterable[PackManifestSlot]|None slots: The list with slots that this pack holds
        :param datetime|None created_at: The datetime this pack was created. If None it will be set to
        current time
        :param datetime|None updated_at: The datetime this pack was updated. If None it will be set to
        current time
        """

        if created_at is None:
            created_at = datetime.utcnow()
        if updated_at is None:
            updated_at = datetime.utcnow()

        if dependencies is None:
            dependencies = []

        if slots is None:
            slots = []

        self._created_at = created_at
        self._updated_at = updated_at
        self._dependencies = {
                dep.dependency_id(): dep
                for dep in dependencies
            }
        self._slots = {
                slot.slot_key: slot
                for slot in slots
            }

    @property
    def dependencies(self):
        """:rtype: dict[str, mlio.io.context_dependencies.base.ContextDependencyBase] """
        return self._dependencies

    @property
    def created_at(self):
        """:rtype: datetime """
        return self._created_at

    @property
    def updated_at(self):
        """:rtype: datetime """
        return self._updated_at

    @property
    def slots(self):
        """ :rtype: dict[str, PackManifestSlot] """
        return self._slots

    def insert_slot(self, slot):
        """
        Insert a new slot in the manifest. This function will also update Manifest's dependencies registry.

        :param PackManifestSlot slot: The slot object to be inserted
        """
        if slot.slot_key in self.slots:
            raise SlotKeyError("Slot already exists with the same key: {}".format(slot.slot_key))

        # Extend dependencies
        for dep_id, dep in slot.dependencies.items():
            if dep_id not in self.dependencies:
                self._dependencies[dep_id] = dep

        self._slots[slot.slot_key] = slot

    def remove_slot(self, slot_key):
        """
        Remove a slot from manifest file. It will also clean-up dangling dependencies that are not referenced by
        any other slot
        :param str slot_key: The key of the slot to be removed
        """
        if slot_key not in self.slots:
            raise SlotKeyError("Cannot remove non-existing slot {}.".format(slot_key))

        # Remove slot
        del self.slots[slot_key]

        # Remove dangling dependencies
        self._cleanup_dangling_dependencies()

    def touch_updated_at(self):
        """
        Touch updated at timestamp with current timestamp
        """
        self._updated_at = datetime.utcnow()

    def _cleanup_dangling_dependencies(self):
        """
        Find dependencies that are note referenced by any slot and remove them
        """
        import itertools

        # Find all referenced dependency ids
        referenced_dep_ids = set(itertools.chain(*[
            slot.dependencies.keys()
            for slot in self.slots.values()
        ]))

        # Calculate the dangling by subtracting referenced
        dangling_dep_ids = set(self.dependencies.keys()) - referenced_dep_ids

        # Remove dangling
        for dep_id in dangling_dep_ids:
            del self.dependencies[dep_id]

    @classmethod
    def _dependencies_from_dict(cls, dependencies_dict):
        """
        Load dependencies from dict data and return objects
        :param dict[str, dict[str, str]] dependencies_dict: Data of dependencies mapped per their id
        :rtype: dict[str, mlio.io.context_dependencies.ContextDependencyBase]
        """
        from .context_dependencies import get_dependency_by_type, UnknownContextDependencyType

        # Check type of data
        if not isinstance(dependencies_dict, dict):
            raise MLIOPackWrongFormat("Manifest file is mal-formatted and cannot load dependencies.")

        dependencies = {}
        for dep_id, dep_data in dependencies_dict.items():
            dep_type = dep_data.get('type')
            try:
                dep_class = get_dependency_by_type(dep_type)
            except UnknownContextDependencyType as e:
                raise MLIOPackWrongFormat("Unknown dependency of type: {}".format(dep_type))

            try:
                dep_obj = dep_class.from_dict(dep_data)
            except Exception as e:
                raise MLIOPackWrongFormat("Cannot load dependency with id: {} because {}"
                                          .format(dep_id, e))

            if dep_obj.dependency_id() != dep_id:
                raise MLIOPackWrongFormat("Dependency with id: {} seems to have wrong id! Expecting: {}".format(
                    dep_id,
                    dep_obj.dependency_id()))
            dependencies[dep_id] = dep_obj

        return dependencies

    @classmethod
    def _slots_from_dict(cls, slots_dict, manifest_dependencies):
        """
        Load slots from dict data and return objects
        :param dict[str, dict] slots_dict: Description dictionary mapped per slot key
        :param  dict[str, mlio.io.context_dependencies.ContextDependencyBase] manifest_dependencies: The manifest
        dependencies
        :rtype: list[PackManifestSlot]
        """

        # Check type of data
        if not isinstance(slots_dict, dict):
            raise MLIOPackWrongFormat("Manifest file is mal-formatted and cannot be load slots.")

        return [
            PackManifestSlot.from_dict(
                slot_key=slot_key,
                data=slot_data,
                manifest_dependencies=manifest_dependencies
            )
            for slot_key, slot_data in slots_dict.items()
        ]

    @classmethod
    def from_dict(cls, data):
        """
        Recover a PackManifest instance from a dictionary format
        :rtype: PackManifest
        """

        # Check version
        if data.get('version', None) != 2:
            raise MLIOPackWrongFormat("An incompatible pack version was provided")

        # Recover dependencies
        dependencies = cls._dependencies_from_dict(data.get('dependencies', {}))

        # Recover slots
        slots = cls._slots_from_dict(data.get('slots', {}), dependencies)

        # Recover meta-data
        created_at = data.get('meta', {}).get('created_at', None)
        if created_at is not None:
            created_at = datetime.utcfromtimestamp(created_at).replace(tzinfo=timezone(timedelta(0)))

        updated_at = data.get('meta', {}).get('updated_at', None)
        if updated_at is not None:
            updated_at = datetime.utcfromtimestamp(updated_at).replace(tzinfo=timezone(timedelta(0)))

        # Extract timestamp from metadata
        return PackManifest(
            dependencies=list(dependencies.values()),
            slots=slots,
            created_at=created_at,
            updated_at=updated_at
        )

    def _metadata_to_dict(self):
        """
        Convert meta data storage to dictionary object
        :rtype: dict
        """
        meta = dict()
        meta['created_at'] = self.created_at.timestamp()
        meta['updated_at'] = self.updated_at.timestamp()
        meta['python'] = sys.version
        return meta

    def to_dict(self):
        """
        Convert current PackManifest instance to a jsonable dictionary format.
        :rtype: dict
        """
        return {
            'version': self.PROTOCOL_VERSION,
            'meta': self._metadata_to_dict(),
            'dependencies': {
                dep.dependency_id(): dep.to_dict()
                for dep in self.dependencies.values()
            },
            'slots': {
                slot.slot_key: slot.to_dict()
                for slot in self._slots.values()
            }
        }


class Pack(object):
    """
    Representation model of IO pack. A Pack can be used to dump and load ML related objects
    in uniquely identified slots

    This object implements the context manager interface so that it can be used as:

    with open('pack.zip', 'w+b') as fp
        with Pack(fp) as pck:
            print(pck.list_slots())
    """

    def __init__(self, file_handler):
        """
        Initialize a new or existing pack
        :param typing.FileIO[bytes] file_handler: A file-like object that will be stored the pack. The file
         is expected to be opened in binary mode
        """

        # Check type of file object
        if 'b' not in getattr(file_handler, 'mode', ''):
            if hasattr(file_handler, 'buffer'):
                file_handler = file_handler.buffer.raw
            else:
                raise ValueError("The file object must be opened in binary mode")

        self._file_handler = file_handler
        self._zip_fh = ZipFile(self._file_handler, 'a')
        self._manifest = self._load_or_create_manifest()

    def _load_or_create_manifest(self):
        """
        :rtype: PackManifest
        """
        # Try to load existing manifest file
        if PackManifest.MANIFEST_FILENAME in self._zip_fh.namelist():
            manifest_data = self._zip_fh.read(PackManifest.MANIFEST_FILENAME).decode('utf-8')
            manifest = PackManifest.from_dict(json.loads(manifest_data))
        else:
            manifest = PackManifest()
            self._update_manifest(manifest)
        return manifest

    def _update_manifest(self, manifest=None):
        """
        Update the manifest file inside the pack. This will also update the updated_at
        timestamp
        """
        if manifest is None:
            manifest = self._manifest
        manifest.touch_updated_at()

        manifest_json = json.dumps(manifest.to_dict())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._zip_fh.writestr(PackManifest.MANIFEST_FILENAME, manifest_json)

    def _existing_pack_objects(self):
        """
        Get a list of existing stored objects in the pack.

        Because ZipFile does not permit removing items, we consider zero sized objects as non-existing
        :return: A list of existing pack objects
        :rtype: set(str)
        """

        # ZipFile keeps duplicate entries but only the last one is effective
        object_sizes = {}
        for zip_entry in self._zip_fh.infolist():
            if zip_entry.filename == PackManifest.MANIFEST_FILENAME:
                continue
            object_sizes[zip_entry.filename] = zip_entry.file_size

        return set(
            object_name
            for object_name, object_size in object_sizes.items()
            if object_size
        )

    def _cleanup_dangling_pack_objects(self):
        """
        Find pack objects that are not referenced by any slot and remove them
        :return: The list of found dangling objects
        :rtype: set(str)
        """

        referenced_objects = set(
            slot.pack_object
            for slot in self.slots_info.values()
        )

        unreferenced_objects = self._existing_pack_objects() - referenced_objects
        for pack_object in unreferenced_objects:
            # Zero contents of object from archive
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self._zip_fh.writestr(pack_object, b'')

        return unreferenced_objects

    def __enter__(self):
        """:rtype: Pack"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Close zip
        self.close()

    def close(self):
        """
        Close the pack handler. This will not close the file object
        """
        self._zip_fh.close()

    @property
    def slots_info(self):
        """
        Get information about slots
        :rtype: dict[str, PackManifestSlot]
        """
        return self._manifest.slots

    @property
    def manifest_info(self):
        """
        Get information about manifest
        :rtype: PackManifest
        """
        return self._manifest

    def has_slot(self, slot_key):
        """
        Check if a slot exists in the pack
        :param str slot_key: The key of the slot to check for
        :rtype: bool
        """
        return slot_key in self._manifest.slots

    def dump(self, slot_key, obj):
        """
        Dump an object in a pack slot
        :param str slot_key: The key of the slot
        :param T obj: The object to be serialized and stored in the pack
        """
        from .serializers import find_suitable_serializer
        from ._lib import hash_file_object

        if self.has_slot(slot_key):
            raise SlotKeyError("Cannot overwrite slot with id: {}".format(slot_key))

        # Find suitable serializer
        serializer = find_suitable_serializer(obj)()

        with tempfile.NamedTemporaryFile('w+b') as temp_fh:

            # Serialize
            serializer.dump(obj, temp_fh)

            # Calculate sha256
            temp_fh.seek(0, sys_io.SEEK_SET)
            sha256_hash = hash_file_object(temp_fh)

            # Calculate slot metadata
            slot = PackManifestSlot(
                slot_key=slot_key,
                serialized_sha256_hash=sha256_hash,
                serializer=serializer,
                dependencies=serializer.get_context_dependencies()
            )

            # Check if there is already a pack object (dedup)
            if slot.pack_object not in self._existing_pack_objects():
                # Store pack object
                temp_fh.seek(0, sys_io.SEEK_SET)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self._zip_fh.write(temp_fh.name, arcname=slot.pack_object)

            # Update manifest
            self._manifest.insert_slot(slot)
            self._update_manifest()

    def load(self, slot_key):
        """
        Load a serialized object from a slot in the pack
        :param str slot_key: The key of the slot to load object from
        :return: The unserialized object
        """
        from ._lib import hash_file_object

        if not self.has_slot(slot_key):
            raise SlotKeyError("There is no slot with name {}".format(slot_key))
        slot = self.slots_info[slot_key]

        # Test that dependencies are satisfied
        unsatisfied_dep_ids = slot.find_unsatisfied_dependencies()

        if unsatisfied_dep_ids:
            raise MLIODependenciesNotSatisfied(
                "Cannot load because dependencies: {} are not satisfied "
                .format(", ".join(unsatisfied_dep_ids)))

        # Check file hash
        with self._zip_fh.open(slot.pack_object, 'r') as fp:

            sha256 = hash_file_object(fp)
            if sha256 != slot.serialized_sha256_hash:
                raise MLIOPackSlotWrongChecksum(
                    "Cannot load slot: {} as the serialized data seems corrupted"
                    .format(slot_key))

        # Load object
        with self._zip_fh.open(slot.pack_object, 'r') as fp:
            return slot.serializer.load(fp)

    def remove(self, slot_key):
        """
        Remove a serialized object from a slot
        :param str slot_key: The key of the slot to remove
        """
        if not self.has_slot(slot_key):
            raise SlotKeyError("There is no slot with name {}".format(slot_key))

        # Delete meta data from manifest file
        self._manifest.remove_slot(slot_key)
        self._update_manifest()

        # Remove dangling objects
        self._cleanup_dangling_pack_objects()

    def __contains__(self, item):
        return self.has_slot(item)
