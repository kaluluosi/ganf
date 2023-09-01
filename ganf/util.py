from hashlib import md5


def file_md5(file_path: str):
    """
    计算文件的md5值
    这个实现目前不支持超大文件（几个G那种）
    :param file_path: 文件路径
    :return: md5值
    """
    with open(file_path, "rb") as f:
        md5_obj = md5()
        md5_obj.update(f.read())
        md5_value = md5_obj.hexdigest()
        return md5_value
