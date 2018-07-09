
class SlotKeyError(KeyError):
    """
    Exception raised in case of key error
    """
    pass


class MLIOPackWrongFormat(ValueError):
    """
    Exception raised in case of pack parsing error
    """
    pass


class MLIODependenciesNotSatisfied(RuntimeError):
    """
    Exception raised if a model cannot be loaded because dependencies are not satisfied
    """
    pass


class MLIOPackSlotWrongChecksum(RuntimeError):
    """
    Exception raised if checksum is wrong in a slot
    """
    pass
