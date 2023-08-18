# Ganf

基于OpenAI的文档批量翻译工具，用来批量的翻译mkdocs、sphinx相关文档。
本工具没有内置OpenAI的Api key，你需要自己去购买OpenAI或者Azure OpenAI的服务。

> **note** 后续考虑支持POT等多语言文本的翻译（主要是要支持差异比对增量翻译）


# 安装

> pip install ganf


# 快速开始

在你想要翻译的docs目录下调用 `init` 命令配置翻译策略

```shell
ganf init
```

翻译整个文档项目
```shell
ganf build
```

