import shutil
import io as sys_io
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
import tarfile

from .base import SerializerBase, get_object_root_module


class GensimWord2VecModelsSerializer(SerializerBase):
    """
    Gensim Word2Vec specific serializer. It will use gensim's internal function to load and store model
    """

    @classmethod
    def serializer_type(cls):
        return 'gensim-word2vec'

    def _add_gensim_module_version_dependency(self):
        """
        Add a dependency on the exact current version of gensim
        """
        self._add_module_version_dependency(
            'gensim',
            None
        )

    def dump(self, obj, fh):
        self._add_gensim_module_version_dependency()

        # Store gensim model inside a clean directory
        with TemporaryDirectory() as tmp_dir:

            root_file = str(Path(tmp_dir) / 'root.w2v')
            obj.save(root_file)

            # Create an archive of all generated files
            with NamedTemporaryFile(mode='w+b') as temp_file:
                tar_fh = tarfile.open(fileobj=temp_file, mode='w|')

                for entry in Path(tmp_dir).iterdir():
                    if entry.is_file():
                        tar_fh.add(str(entry), str(entry.name))

                tar_fh.close()

                # Store this archive in the slot
                temp_file.seek(0, sys_io.SEEK_SET)
                shutil.copyfileobj(temp_file, fh)

    def load(self, fh):
        from gensim.models import Word2Vec

        # Deflate tar in a temporary directory
        with tarfile.open(fileobj=fh, mode='r|') as tar_fh:
            with TemporaryDirectory() as tmp_dir:
                tmp_dir = Path(tmp_dir)
                tar_fh.extractall(tmp_dir)

                # Open root object
                return Word2Vec.load(str(tmp_dir / 'root.w2v'))

    def dumps(self, obj):
        self._add_gensim_module_version_dependency()

        # Create a temporary file and ask Word2Vec to write on this file
        with NamedTemporaryFile("r+b") as temp_fh:
            obj.save(temp_fh.name)
            # Read contents
            return temp_fh.read()

    def loads(self, payload):
        from gensim.models import Word2Vec

        # Create temporary file and dump payload
        with NamedTemporaryFile("r+b") as temp_fh:
            temp_fh.write(payload)
            temp_fh.flush()
            # Ask gensim to load model from file-system
            return Word2Vec.load(temp_fh.name)

    @classmethod
    def _is_gensim_word2vec(cls, obj):
        """
        Check if it is a Word2Vec gensim model
        :param Word2Vec|T obj: Any type of object
        :rtype: bool
        """
        from gensim.models import Word2Vec
        return isinstance(obj, Word2Vec)

    @classmethod
    def can_serialize(cls, obj):
        # First check the root module before import Word2Vec type. This permits to use this function
        # in python environment without gensim installed
        return get_object_root_module(obj) in {'gensim'} \
               and cls._is_gensim_word2vec(obj)
