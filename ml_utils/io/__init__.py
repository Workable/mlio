import os
import json
from zipfile import ZipFile

from .base import MLIOPackWrongFormat
from .pack import PackManifest, Pack



def dump_old(model, fp):
    """
    Dump a new model to the filesystem
    :param T model: Any ML model that must be serialized
    :param File fp: A file object to store the model
    :return:
    """
    with ZipFile(fp, 'a') as zip_fp:

        # Try to load existing manifest file
        if PackManifest.MANIFEST_FILENAME in zip_fp.namelist():
            manifest_data = zip_fp.read(PackManifest.MANIFEST_FILENAME).decode('utf-8')
            manifest = PackManifest.from_dict(json.loads(manifest_data))
        else:
            manifest = PackManifest()

        manifest = {
            'version': __protocol_version,
            'modules': get_installed_modules_version(),
        }

        zip_fp.writestr(__MANIFEST_FILE, json.dumps(manifest))

        with tempfile.NamedTemporaryFile('wb') as tmpf:
            joblib.dump(model, tmpf)
            tmpf.seek(0)
            zip_fp.write(tmpf.name, arcname=__model_file)


def dump(model, fp, slot_key=None):
    """
    Dump a new model to the filesystem
    :param T model: Any ML model that must be serialized
    :param File fp: A file object to store the model
    :return:
    """
    if slot_key is None:
        slot_key = "_default"

    with Pack(fp, 'a') as mlio_pack:
        mlio_pack.dump_to_slot(slot_key, model)



def load(fp):
    """
    Load a model from the filesystem
    :param File fp: The file handler to load model from
    :return: The loaded model
    """
    with ZipFile(fp, 'r') as zip_fp:
        if __MANIFEST_FILE not in zip_fp.namelist():
            raise MLIOPackWrongFormat('No manifest in pack file')

        # Read manifest file
        manifest = json.loads(zip_fp.read(__MANIFEST_FILE).decode('utf-8'))

        assert_versions_match({
                'version': __protocol_version,
                'modules': get_installed_modules_version()
            }, manifest)

        with tempfile.TemporaryDirectory('wb') as tmpf:
            zip_fp.extract(__model_file, tmpf)
            object = joblib.load(os.path.join(tmpf, __model_file))

        return object
