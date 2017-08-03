import json
import tempfile
from zipfile import ZipFile
from datetime import datetime


class SlotNotFoundError(KeyError):
    """
    Exception raised on case of key error
    """
    pass


class PackManifestSlot(object):

    def __init__(self, slot_key, sha256_hash, serializer_id, dependencies=None):
        """

        :param str slot_key: The identifier of the slot  
        :param str sha256_hash:
        :param str serializer_id:
        :param list[ml_utils.io.context_dependencies.ContextDependencyBase] dependencies:
        """
        from .serializers import get_serializer_by_id

        if dependencies is None:
            dependencies = []

        self.slot_key = slot_key,
        self.serializer = get_serializer_by_id(serializer_id)
        self.dependencies = dependencies
        self.sha256_hash = sha256_hash

    def to_dict(self):
        """
        Convert slot to jsonable dictionary
        :rtype: dict
        """
        return {
            'slot': self.slot_key,
            'sha256': self.sha256_hash,
            'serializer': self.serializer.serializer_id(),
            'dependencies': list(set(
                dep.dependency_id()
                for dep in self.dependencies
            )),
        }

    def pack_filename(self):
        """
        The internal filename of the pack
        :rtype: str
        """
        return "{}.slot".format(self.sha256_hash)

    @classmethod
    def from_dict(cls, data):
        cls(
            slot_key=data['slot_key'],
            sha256_hash=data['sha256'],
            serializer_id=data['serializer'],
            dependencies=[]  # TODO: No idea what to do here
        )


class PackManifest(object):

    PROTOCOL_VERSION = 2
    MANIFEST_FILENAME = "Manifest.json"

    def __init__(self, meta_data=None, dependencies=None):
        if meta_data is None:
            meta_data = {}

        if dependencies is None:
            dependencies = []

        self._meta_data = meta_data
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()
        self._dependencies = dependencies
        self._slots = {}

    @property
    def meta_data(self):
        return self._meta_data

    @property
    def dependencies(self):
        """:rtype: list[ml_utils.io.context_dependencies.ContextDependencyBase] """
        return self._dependencies

    @property
    def created_at(self):
        """:rtype: datetime """
        return self._created_at

    @@property
    def updated_at(self):
        """:rtype: datetime """
        return self._updated_at

    @property
    def slots(self):
        """
        :rtype: dict[str, PackManifestSlot]
        """
        return self._slots

    @classmethod
    def from_dict(cls, data):
        """
        :rtype: PackManifest
        """
        pass

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
        return {
            'version': self.PROTOCOL_VERSION,
            'meta': self._metadata_to_dict(),
            'dependencies': {
                dep.dependency_id(): dep.to_dict()
                for dep in self.dependencies
            },
            'slots': [
                slot.to_dict()
                for slot in self._slots.values()
            ]
        }

class Pack(object):
    """
    MLIO pack that is capable to dump and load ML related objects in unique slots
    """

    def __init__(self, file_handler, timestamp=None):
        self._file_handler = file_handler
        self._zip_fh = ZipFile(self._file_handler, 'a')
        self._manifest = self._load_or_create_manifest(timestamp=timestamp)

    def _load_or_create_manifest(self, timestamp):
        """
        :rtype: PackManifest
        """
        # Try to load existing manifest file
        if PackManifest.MANIFEST_FILENAME in self._zip_fh.namelist():
            manifest_data = self._zip_fh.read(PackManifest.MANIFEST_FILENAME).decode('utf-8')
            manifest = PackManifest.from_dict(json.loads(manifest_data))
        else:
            manifest = PackManifest(timestamp=timestamp)
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

    def dump_to_slot(self, slot_key, obj):
        from .serializers import find_suitable_serializer
        from ._lib import hash_file_object

        if slot_key in self._manifest.slots:
            raise SlotNotFoundError("Cannot overwrite slot with id: {}".format(slot_key))

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
                serializer_id=serializer.serializer_id(),
                dependencies=serializer.get_context_dependencies()
            )

            # Calculate sha256 hash
            self._zip_fh.write(temp_fh.name, arcname=slot.pack_filename())

        # Inject dependencies on metadata

        raise NotImplementedError()

    def load_from_slot(self, slot_key):
        raise NotImplementedError()

    def remove_slot(self, slot_key):
        raise NotImplementedError()
