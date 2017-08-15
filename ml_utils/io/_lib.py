import hashlib


def file_as_blockiter(file, block_size=65536):
    """
    Treat a file handler as block generator of bytes
    :param typing.FileIO[bytes] file: The file object
    :param int block_size: The size of each block
    :return: A generator that can be used to iterate block chunks
    """
    block = file.read(block_size)
    while len(block) > 0:
        yield block
        block = file.read(block_size)


def hash_file_object(file, hasher=hashlib.sha256):
    """
    Calculate SHA256 hash for a file object
    :param typing.FileIO[bytes] file: The file object to read date from
    :param typing.Callable hasher: Factory function for the hasher object
    :rtype: str
    """
    h = hasher()

    for block in file_as_blockiter(file):
        h.update(block)

    return h.hexdigest()
