import openai
import nltk
from tqdm import tqdm
from pydantic import BaseModel, RootModel
from ganf.segment import segments
from ganf.config import GLOBAL_OPENAI_CONF, OpenAIConfig


INIT_PROMPT = """
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

我下面会把整个{extension}发送给你，你按照原来文档的格式翻译成{locale}语言返回给我。

"""


class Message(BaseModel):
    role: str
    content: str


MessageList = RootModel[list[Message]]


class Translator:
    def __init__(self, openai_conf: OpenAIConfig | str = GLOBAL_OPENAI_CONF) -> None:
        if isinstance(openai_conf, str):
            self.openai_conf = OpenAIConfig.load(openai_conf)
        else:
            self.openai_conf = openai_conf

        openai.api_key = self.openai_conf.api_key
        openai.api_base = self.openai_conf.api_base
        openai.api_type = self.openai_conf.api_type
        openai.api_version = self.openai_conf.api_version

    def chat_completion(self, messages: MessageList):
        if openai.api_type == "azure":
            response = openai.ChatCompletion.create(
                deployment_id=self.openai_conf.deployment_id,
                model=self.openai_conf.model,
                messages=messages.model_dump(),
            )
        else:
            response = openai.ChatCompletion.create(
                model=self.openai_conf.model, messages=messages.model_dump()
            )

        txt = response["choices"][0]["message"]["content"]  # type: ignore
        return txt

    def translate(
        self, content: str, from_locale: str, to_locale: str, prompts: list[str]
    ):
        translated_content: list[str] = []

        segs = segments(
            content, max_tokens=self.openai_conf.max_tokens, language=from_locale
        )

        for seg in tqdm(segs, desc="翻译中..."):
            if not seg.strip():
                translated_content.append(seg)
                continue

            result = self.chat_completion(
                MessageList(
                    [
                        Message(
                            role="system",
                            content=INIT_PROMPT.format(
                                locale=to_locale,
                                extension=".md",
                                prompts=prompts,
                            ),
                        ),
                        Message(role="user", content=seg),
                    ]
                )
            )
            translated_content.append(result)

        return "".join(translated_content)

    def cost_calculate(self, content: str):
        tokens = nltk.word_tokenize(content)
        cost = len(tokens) * (self.openai_conf.cost_per_k_token / 1000)
        return cost, len(tokens)
