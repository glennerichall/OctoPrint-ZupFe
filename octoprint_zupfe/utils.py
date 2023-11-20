import hashlib


def compute_md5(file_path):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(4096), b""):
            md5.update(block)
    return md5.hexdigest()
