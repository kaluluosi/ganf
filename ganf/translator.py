import asyncio
import glob
import os
import shutil
from typing import Callable
import openai
from openai.error import Timeout
import nltk
from pydantic import RootModel, BaseModel
from tqdm.asyncio import trange, tqdm
from tqdm import tqdm as std_tqdm
from .config import GitignoreMethod, openai_config_var, ganf_config_var, gitignore_var
from .segment import segments
from .record import Record
from .utils import read_doc, write_doc, file_md5

RECORD_FILE = "record.json"

START_PROMPT = """
你现在是一个{extension}文档翻译器。
你必须满足以下几点：
不要破坏{extension}语法。
不要将原文的标点符号转换成中文标点符号（非常重要）。
要区分术语和说明文本，不用翻译术语。
"[链接名]:(..路径)"碰到这种格式不要修改英文冒号！
只翻译描述性语言文本，{extension}代码不要做任何修改。
不要破坏python sphinx文档相关语法标记。
翻译的结果要能通过sphinx linter
rst引用标记前后要加空格隔开
{prompts}

我下面会把整个{extension}文档发送给你，你按照原来文档的格式翻译成{locale}语言返回给我。
"""


class Message(BaseModel):
    role: str
    content: str


class MessageList(RootModel[list[Message]]):
    ...


async def chat_completion(messages: MessageList):
    openai_config = openai_config_var.get()

    while True:
        try:
            if openai_config.api_type == "azure":
                response = await openai.ChatCompletion.acreate(
                    deployment_id=openai_config.deployment_id,
                    model=openai_config.model,
                    messages=messages.model_dump(),
                )
            else:
                response = await openai.ChatCompletion.acreate(
                    model=openai_config.model, messages=messages.model_dump()
                )
            txt = response["choices"][0]["message"]["content"]
            return txt
        except (Timeout, openai.APIError) as e:
            print(f"冷却{openai_config.cooldown}s")
            print(e)
            await asyncio.sleep(openai_config.cooldown)


async def translate(
    content: str, extension: str, locale: str, prompt: list[str], max_tokens: int = 100
) -> str:
    """将内容翻译成目标语言。

    Args:
        content (str): 文本内容
        extension (str): 文件扩展名，给AI参考避免将没必要翻译的语法符号翻译
        locale (str): 目标语言

    Returns:
        str: 翻译结果文本
    """

    translated_txt = ""

    segs = list(segments(content, max_tokens))

    result = await tqdm.gather(
        *[
            chat_completion(
                MessageList(
                    [
                        Message(
                            role="system",
                            content=START_PROMPT.format(
                                extension=extension,
                                locale=locale,
                                prompts=prompt,
                            ),
                        ),
                        Message(role="user", content=seg),
                    ]
                )
            )
            for seg in segs
        ],
        desc="翻译中...",
        leave=False,
    )
    translated_txt += "".join(result)

    return translated_txt


def cost_accounting(doc: str, cost: float):
    """统计翻译成本"""
    tokens = nltk.word_tokenize(doc)
    cost += len(tokens) * (cost / 1000)
    return cost, tokens


async def translate_dir(
    input_dir_path: str,
    output_dir_path: str | None = None,
    locale: str = "zh",
):
    """将整个目录递归翻译，然后按照原目录结构翻译保存到dest_dir_path目录下。"""

    if not os.path.isdir(input_dir_path):
        raise ValueError(f"{input_dir_path} is not a directory.")

    if output_dir_path and not os.path.isdir(output_dir_path):
        raise ValueError(f"{output_dir_path} is not a directory.")

    gitignore = gitignore_var.get()
    ganf_config = ganf_config_var.get()
    openai_config = openai_config_var.get()

    input_dir_path = os.path.normpath(input_dir_path)
    output_dir_path = os.path.normpath(output_dir_path)
    output_dir_path = os.path.join(output_dir_path, locale)

    record_path = os.path.join(output_dir_path, RECORD_FILE)
    record = Record.load(record_path) or Record()

    doc_paths = glob.glob(os.path.join(input_dir_path, "/**/*.*"), recursive=True)

    bar = tqdm(doc_paths, desc=locale)

    for doc_path in bar:
        bar.set_postfix_str(doc_path)

        output_doc = doc_path.replace(input_dir_path, output_dir_path, 1)
        extension = os.path.splitext(doc_path)[1]

        if not os.path.exists(output_doc):
            # 目标目录没有这个文件，那么就拷贝过去
            dist_dir = os.path.dirname(output_doc)
            if not os.path.exists(dist_dir):
                os.makedirs(dist_dir, exist_ok=True)
            shutil.copy(doc_path, output_doc)

        if gitignore(doc_path):
            # 被忽略
            continue
        elif not record.is_modified(doc_path):
            continue
        else:
            doc = read_doc(doc_path)

            txt = await translate(
                doc,
                extension=extension,
                locale=locale,
                max_tokens=openai_config.max_tokens,
                prompt=ganf_config.prompts,
            )

            write_doc(output_doc, txt)
            record.add(doc_path)
            record.save(record_path)


async def translate_file(
    file_path: str,
    output_path: str | None = None,
    locale: str = "zh",
    prompt: list[str] = [],
):
    """
    翻译单个文件
    """
    openai_config = openai_config_var.get()

    basename, extension = os.path.splitext(file_path)
    output_path = output_path or f"{basename}.{locale}{extension}"

    doc = read_doc(file_path)
    txt = await translate(
        doc,
        extension=extension,
        locale=locale,
        max_tokens=openai_config.max_tokens,
        prompt=prompt,
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    write_doc(output_path, txt)
