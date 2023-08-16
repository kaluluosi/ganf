import hashlib


def read_doc(file_path: str):
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def write_doc(file_path: str, content: str):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def file_md5(file_path: str):
    doc = read_doc(file_path)
    return hashlib.md5(doc.encode())
