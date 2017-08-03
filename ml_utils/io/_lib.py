import hashlib


def file_as_blockiter(file, block_size=65536):
    """
    Treat a file handler as block generator of bytes
    :param typing.IO file: The file object
    :param int block_size: The size of each block
    :return:
    """
    with file:
        block = file.read(block_size)
        while len(block) > 0:
            yield block
            block = file.read(block_size)


def hash_file_object(file, hasher=hashlib.sha256):
    """
    Calculate SHA256 hash for a file object
    :param typing.IO file: The file object to read date from
    :param T hasher: The hasher constructor
    :rtype: str
    """
    h = hasher()

    for block in file_as_blockiter(file):
        h.update(block)

    return h.hexdigest()
