import os


def file_path(filename):
    """
    Resolve the absolute path to fixture file
    :param str filename: Filename of the fixture file
    :rtype: str
    """
    fpath = os.path.join(
        os.path.dirname(__file__),
        filename
    )

    if not os.path.isfile(fpath):
        raise ValueError("Cannot find fixture: {}".format(filename))

    return fpath
