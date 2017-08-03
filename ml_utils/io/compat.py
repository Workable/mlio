from .pack import Pack


def dump(model, fp, slot_key=None):
    """
    Dump an in-memory object to a filesystem pack
    :param T model: Any object that must be serialized
    :param typing.IO fp: A file object to store the final pack
    :param str slot_key: The key of the slot to save the model in. If None it will save it on the default slot
    "_default"
    """
    if slot_key is None:
        slot_key = "_default"

    with Pack(fp) as mlio_pack:
        mlio_pack.dump_to_slot(slot_key, model)


def load(fp, slot_key=None):
    """
    Load an object from a serialized pack file
    :param typing.IO fp: The file object to load pack from
    :param slot_key: The key of the slot where the model is saved. If None it will
    try to load the default slot "_default"
    :return: The recovered object
    """
    if slot_key is None:
        slot_key = "default"

    with Pack(fp) as mlio_pack:
        return mlio_pack.load_from_slot(slot_key)