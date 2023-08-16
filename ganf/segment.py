"""
文本滑动窗口工具类

由于openai接口最大单次请求只支持8000个token，因此超过8000个token的文章需要分段发送翻译。然而直接粗暴的按文本长度截断会导致破坏语义，甚至破坏单词。
因此需要按行、按句，根据累计的token数来做一个滑动窗口。

思路是用生成器的方式，产出文章片段。
"""
import nltk

# 自然语言工具，下载分词器
nltk.download("punkt")


def segments(doc: str, max_tokens: int):
    """将大文本按max_tokens大小分片

    Args:
        doc (str): 文本
        max_tokens (int, optional): 单片最大tokens数.

    Yields:
        str: 单片文本
    """

    # 先将文章按行切割（切割后换行符没了）
    lines = doc.splitlines()

    cur_segment = ""
    total_token = 0

    for line in lines:
        tokens = nltk.word_tokenize(line)
        token_count = len(tokens)
        if total_token + token_count > max_tokens:
            # 将要超过最大token
            yield cur_segment + "\n"  # 返回之前缓存的片
            cur_segment = line + "\n"  # 当前行设置为当前片
            total_token = token_count
        else:
            # 没超过最大token数就继续累加
            cur_segment += line + "\n"
            total_token += token_count

    yield cur_segment
