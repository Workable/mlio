from .pack import Pack

_DEFAULT_SLOT = "_default"


def dump(model, fp, slot_key=_DEFAULT_SLOT):
    """
    Dump an in-memory object to a filesystem pack
    :param T model: Any object that must be serialized
    :param typing.IO fp: A file object to store the final pack
    :param str slot_key: The key of the slot to save the model in. If None it will save it on the default slot
    """

    with Pack(fp) as mlio_pack:
        if mlio_pack.has_slot(slot_key):
            mlio_pack.remove(slot_key)
        mlio_pack.dump(slot_key, model)


def load(fp, slot_key=_DEFAULT_SLOT):
    """
    Load an object from a serialized pack file
    :param typing.IO fp: The file object to load pack from
    :param slot_key: The key of the slot where the model is saved. If None it will try to load the default slot.
    :return: The recovered object
    """

    with Pack(fp) as mlio_pack:
        return mlio_pack.load(slot_key)
