import json
import tempfile
from zipfile import ZipFile
from datetime import datetime

from .exc import MLIOPackWrongFormat, SlotKeyError


class PackManifestSlot(object):

    def __init__(self, slot_key, sha256_hash, serializer, dependencies=None):
        """

        :param str slot_key: The identifier of the slot
        :param str sha256_hash:
        :param ml_utils.io.serializers.implementations.SerializerBase serializer:
        :param list[ml_utils.io.context_dependencies.ContextDependencyBase] dependencies:
        """
        if dependencies is None:
            dependencies = []

        self.slot_key = slot_key,
        self.serializer = serializer
        self.dependencies = dependencies
        self.sha256_hash = sha256_hash

    def pack_filename(self):
        """
        The internal filename of the pack
        :rtype: str
        """
        return "{}.slot".format(self.sha256_hash)

    @classmethod
    def from_dict(cls, slot_key, data, manifest_dependencies):
        """
        Recover an instance from dictionary format
        :param str slot_key: The key of this slot
        :param dict data:
        :param dict[str, ml_utils.io.context_dependencies.ContextDependencyBase] manifest_dependencies: All the
        dependencies declared in the PackManifest mapped by their id
        :rtype: PackManifestSlot
        """
        from .serializers import get_serializer_by_type

        slot_key = data['slot_key']

        # Check mandatory fields
        if 'sha256' not in data:
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
        cls(
            slot_key=slot_key,
            sha256_hash=data['sha256'],
            serializer=get_serializer_by_type(data['serializer']),
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
            'slot': self.slot_key,
            'sha256': self.sha256_hash,
            'serializer': self.serializer.serializer_type(),
            'dependencies': list(set(
                dep.dependency_id()
                for dep in self.dependencies
            )),
        }


class PackManifest(object):
    """
    Handler for Manifest registry of the pack
    """

    PROTOCOL_VERSION = 2
    MANIFEST_FILENAME = "Manifest.json"

    def __init__(self, meta_data=None, dependencies=None, slots=None, created_at=None, updated_at=None):
        """
        Construct a new manifest object
        :param dict[str,str]|None meta_data:
        :param list[ml_utils.io.context_dependencies.ContextDependencyBase]|None dependencies:
        :param list[PackManifestSlot]|None slots:
        :param datetime|None created_at:
        :param datetime|None updated_at:
        """
        if meta_data is None:
            meta_data = {}

        if created_at is None:
            created_at = datetime.utcnow()
        if updated_at is None:
            updated_at = datetime.utcnow()

        if dependencies is None:
            dependencies = {}
        else:
            dependencies = {
                dep.dependency_id(): dep
                for dep in dependencies
            }

        if slots is None:
            slots = {}
        else:
            slots = {
                slot.slot_key: slot
                for slot in slots
            }

        self._meta_data = meta_data
        self._created_at = created_at
        self._updated_at = updated_at
        self._dependencies = dependencies
        self._slots = slots

    @property
    def meta_data(self):
        return self._meta_data

    @property
    def dependencies(self):
        """:rtype: dict[str, ml_utils.io.context_dependencies.ContextDependencyBase] """
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
        """
        :rtype: dict[str, PackManifestSlot]
        """
        return self._slots

    def touch_updated_at(self):
        """
        Touch updated at timestamp with current timestamp
        """
        self._updated_at = datetime.utcnow()

    @classmethod
    def _dependencies_from_dict(cls, dependencies_dict):
        """
        Load dependencies from dict data and return objects
        :param dict[str, str] data:
        :rtype: dict[str, ml_utils.io.context_dependencies.ContextDependencyBase]
        """
        from .context_dependencies import get_dependency_by_type, UnknownContextDependencyType

        # Check type of data
        if not isinstance(dependencies_dict, dict):
            raise MLIOPackWrongFormat("Manifest file is mal-formatted and cannot load dependencies.")

        dependencies = []
        for dep_id, dep_data in dependencies_dict.items():
            dep_type = dep_data.get('type')
            try:
                dep_class = get_dependency_by_type(dep_type)
            except UnknownContextDependencyType as e:
                raise MLIOPackWrongFormat("Unknown dependency of type: {}".format(dep_type))

            try:
                dep_obj = dep_class.from_dict(dep_data)
            except:
                raise MLIOPackWrongFormat("Cannot load dependency with id: {}".format(dep_id))

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
        :param dict[str, str] slots_dict: The slots dictionary
        :param  dict[str, ml_utils.io.context_dependencies.ContextDependencyBase] manifest_dependencies: The manifest
        dependencies
        :rtype: list[PackManifestSlot]
        """

        # Check type of data
        if not isinstance(slots_dict, dict):
            raise MLIOPackWrongFormat("Manifest file is mal-formatted and cannot be load slots.")

        return {
            slot_key: PackManifestSlot.from_dict(
                slot_key=slot_key,
                data=slot_data,
                manifest_dependencies=manifest_dependencies
            )
            for slot_key, slot_data in slots_dict
        }

    @classmethod
    def from_dict(cls, data):
        """
        Recover a PackManifest instance from a dictionary format
        :rtype: PackManifest
        """

        # Recover dependencies
        dependencies = cls._dependencies_from_dict(data.get('dependencies', {}))

        # Recover slots
        slots = cls._slots_from_dict(data.get('slots', {}), dependencies)

        # Extract timestamp from metadata
        return PackManifest(
            meta_data=data.get('meta_data', {}).get('user'),
            dependencies=list(dependencies.values()),
            slots=slots
        )

    def _metadata_to_dict(self):
        """
        Convert meta data storage to dictionary object
        :rtype: dict
        """
        from copy import deepcopy
        meta = deepcopy(self._meta_data)
        meta['created_at'] = self.created_at.timestamp()
        meta['updated_at'] = self.updated_at.timestamp()
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
            'slots': [
                slot.to_dict()
                for slot in self._slots.values()
            ]
        }


class Pack(object):
    """
    MLIO pack that is capable to dump and load ML related objects in unique slots

    The object can be used as a context manager also
    """

    def __init__(self, file_handler):
        self._file_handler = file_handler
        self._zip_fh = ZipFile(self._file_handler, 'a')
        self._manifest = self._load_or_create_manifest()

    def _load_or_create_manifest(self, timestamp):
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
        Update
        :return:
        """
        if manifest is None:
            manifest = self._manifest
        manifest_json = json.dumps(manifest.to_dict())
        self._zip_fh.writestr(PackManifest.MANIFEST_FILENAME, manifest_json)

    def __enter__(self):
        """
        :rtype: Pack
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Close zip
        self.close()

    def close(self):
        """
        Close the pack handler. This will not close the file object
        """
        self._zip_fh.close()

    def list_slots(self):
        return self._manifest.slots.values()

    def metadata(self):
        return self._manifest.meta_data

    def update_metadata(self, key, value):
        return self._manifest.meta_data

    def dump_slot(self, slot_key, obj):
        from .serializers import find_suitable_serializer
        from ._lib import hash_file_object

        if self.has_slot(slot_key):
            raise SlotKeyError("Cannot overwrite slot with id: {}".format(slot_key))

        # Find suitable serializer
        serializer = find_suitable_serializer(obj)

        with tempfile.NamedTemporaryFile('r+b') as temp_fh:

            # Serialize
            serializer.dump(temp_fh, obj)
            sha256_hash = hash_file_object(temp_fh)

            # Calculate sha256
            slot = PackManifestSlot(
                slot_key=slot_key,
                sha256_hash=sha256_hash,
                serializer=serializer.serializer_type(),
                dependencies=serializer.get_context_dependencies()
            )

            # Calculate sha256 hash
            self._zip_fh.write(temp_fh.name, arcname=slot.pack_filename())

        # Inject dependencies on metadata

        raise NotImplementedError()

    def load_slot(self, slot_key):
        raise NotImplementedError()

    def remove_slot(self, slot_key):
        raise NotImplementedError()

    def has_slot(self, slot_key):
        return slot_key in self._manifest.slots
