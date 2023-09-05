import asyncio
import glob
import os
import shutil
import sys
import click
from pydantic import BaseModel
from typing import Any, Callable
from contextvars import ContextVar
from click import Context
from tqdm import tqdm
from ganf.config import (
    GANF_CONF,
    GLOBAL_OPENAI_CONF,
    GANF_DIR,
    META_CONF,
    OPENAI_CONF,
    GanfConfig,
    MetaConfig,
    OpenAIConfig,
)
from gitignore_parser import parse_gitignore
from ganf.translator import Translator
from ganf.util import read_file, write_file

IGNORE_FILE = ".ganfignore"

IsIgnoreFunction = Callable[[str], bool]

openai_conf_var = ContextVar[OpenAIConfig]("openai_conf_var")


class CostInfo(BaseModel):
    cost: float = 0
    tokens: int = 0


class OrderCommands(click.Group):
    def list_commands(self, ctx: Context) -> list[str]:
        return list(self.commands)


def openai_configurate(ctx: Context, param: click.Parameter, value: str) -> Any:
    if not os.path.exists(value):
        click.echo(f"配置文件{value}不存在，转为使用全局配置。")
        value = GLOBAL_OPENAI_CONF
        # 如果全局都不存在就转而去执行openai配置设置向导了
        if not os.path.exists(value):
            answer = click.confirm(f"没有配置openai.toml，是否现在配置？", default=True, abort=True)
            if answer:
                local = click.confirm("是否使用本地配置？(否将创建全局配置)", default=True, abort=True)
                ctx.invoke(openai, local=local)

            sys.exit()

    openai_conf = OpenAIConfig.load(value)
    return openai_conf


openai_config_option = click.option(
    "--openai",
    type=click.Path(exists=False),
    default=OPENAI_CONF,
    callback=openai_configurate,
    show_default=True,
    help="openai配置文件",
)


def ganf_configurate(ctx: Context, param: click.Parameter, value: str) -> Any:
    if not os.path.exists(value):
        click.echo(f"当前目录没有配置文件，请使用 `ganf init` 命令创建配置文件。")
        sys.exit()

    ctx.default_map = ctx.default_map or {}
    ganf_config = GanfConfig.load(value)
    return ganf_config


ganf_config_option = click.option(
    "-c",
    "--config",
    type=click.Path(exists=False),
    default=GANF_CONF,
    callback=ganf_configurate,
    show_default=True,
    help="配置文件",
)


def ignore_configure(ctx: Context, param: click.Parameter, value: str):
    if os.path.exists(value):
        ignore = parse_gitignore(value)

        def _inner_ignore(path: str):
            dirname = os.path.dirname(path)
            return ignore(dirname) or ignore(path)

        return _inner_ignore
    else:
        click.echo("没有.ignore文件，将对所有文档进行翻译。")
        return lambda path: False


ganfignore_option = click.option(
    "-i",
    "--ignore",
    type=click.Path(exists=False),
    default=IGNORE_FILE,
    callback=ignore_configure,
    show_default=True,
    help="忽略列表",
)


def get_meta_config(path: str):
    if os.path.exists(path):
        return MetaConfig.load(path)
    else:
        return MetaConfig(file_name=path)


@click.group(cls=OrderCommands)
def main():
    """
    Ganf 文档翻译工具
    """


def openai_conf_wizard(save_to: str):
    config = OpenAIConfig()
    data = config.model_dump()
    for k, v in data.items():
        v = click.prompt(k, default=v, show_default=True)
        data[k] = v

    config = OpenAIConfig.model_validate(data)
    config.save(save_to)
    click.echo(save_to)


@main.command()
@click.option("--local", "-l", default=False, flag_value=True, help="全局还是本地")
def openai(local: bool):
    """
    创建 openai配置文件
    """

    if not local:
        click.echo("正在配置全局配置文件...")
        if not os.path.exists(GLOBAL_OPENAI_CONF):
            os.makedirs(GANF_DIR, exist_ok=True)
        else:
            click.echo("全局配置文件已存在，请删除后再试。")
            click.echo(GLOBAL_OPENAI_CONF)
            sys.exit()

        openai_conf_wizard(GLOBAL_OPENAI_CONF)
    else:
        click.echo("正在配置项目配置文件...")
        if not os.path.exists(OPENAI_CONF):
            openai_conf_wizard(OPENAI_CONF)
        else:
            click.echo("项目配置文件已存在，请删除后再试。")
            sys.exit()


@main.command()
@openai_config_option
@ganf_config_option
@ganfignore_option
def cost(openai: OpenAIConfig, config: GanfConfig, ignore: IsIgnoreFunction):
    """
    计算ganf项目的翻译成本
    """
    # 这一步检查不是必须的，只是做个防御和方便类型检查
    if config.file_name is None or not os.path.exists(config.file_name):
        click.echo("ganf.toml不存在")
        sys.exit()

    # ganf.toml可能不是在当前目录里，因此要将工作目录切换到ganf.toml所在目录
    # ganf.toml所在目录绝对路径
    dirname = os.path.dirname(os.path.abspath(config.file_name))
    # 将当前工作目录切换到ganf.toml所在目录
    os.chdir(dirname)

    # 原文档路径
    source_dir = config.source_dir
    # 通配符递归原文档
    files = glob.glob(os.path.join(source_dir, "**", "*.*"), recursive=True)

    bar_locale = tqdm(config.to_locales, desc="所有语言", leave=True)

    total_cost = CostInfo()

    translator = Translator(openai)
    locale_cost_map: dict[str, CostInfo] = {}

    for locale in bar_locale:
        locale_cost_map[locale] = locale_cost = CostInfo()

        dist_dir = os.path.join(config.dist_dir, locale)
        meta_conf_path = os.path.join(dist_dir, META_CONF)
        meta_config = get_meta_config(meta_conf_path)

        bar_locale.set_postfix_str(locale)

        # 过滤掉葫芦和已翻译文件
        def _filter(path: str):
            if ignore(path):  # 忽略
                return False

            if meta_config.is_modified(path):  # 被修改
                return True
            else:
                return False

        bar_calc = tqdm(filter(_filter, files), desc="计算...", leave=True)

        for file_path in bar_calc:
            content = read_file(file_path)
            c, t = translator.cost_calculate(content)
            locale_cost.cost += c
            locale_cost.tokens += t

        total_cost.cost += locale_cost.cost
        total_cost.tokens += locale_cost.tokens

    click.echo(f"总翻译语言: {len(config.to_locales)}")
    click.echo(f"总费用: ${total_cost.cost:.3f}")
    click.echo(f"总token数: {total_cost.tokens}")

    click.echo("-" * 10)

    for locale, cost in locale_cost_map.items():
        click.echo(f"{locale} cost:${cost.cost:.3f} tokens:{cost.tokens}")


@main.command()
@openai_config_option
@ganf_config_option
@ganfignore_option
def build(openai: OpenAIConfig, config: GanfConfig, ignore: IsIgnoreFunction):
    """
    构建ganf翻译
    """

    if config.file_name is None or not os.path.exists(config.file_name):
        click.echo("ganf.toml不存在")
        sys.exit()

    # ganf.toml可能不是在当前目录里，因此要将工作目录切换到ganf.toml所在目录
    # ganf.toml所在目录绝对路径
    dirname = os.path.dirname(os.path.abspath(config.file_name))
    # 将当前工作目录切换到ganf.toml所在目录
    os.chdir(dirname)

    # 原文档绝对路径
    source_dir = config.source_dir

    # 通配符递归原文档
    files = glob.glob(os.path.join(source_dir, "**", "*.*"), recursive=True)

    translator = Translator(openai)

    def _build():
        bar_locale = tqdm(config.to_locales, desc="所有语言", leave=True)

        for locale in bar_locale:
            dist_dir = os.path.join(config.dist_dir, locale)

            meta_conf_path = os.path.join(dist_dir, META_CONF)

            meta_config = get_meta_config(meta_conf_path)
            bar_locale.set_postfix_str(locale)

            def _filter(path: str):
                if ignore(path):  # 忽略
                    return False

                if meta_config.is_modified(path):  # 被修改
                    return True
                else:
                    return False

            bar_tran = tqdm(files, desc="翻译...", leave=True)

            for file_path in bar_tran:
                save_to = file_path.replace(source_dir, dist_dir)

                if not os.path.exists(save_to):
                    # 目标目录没有这个文件，那么就拷贝过去
                    dist_dir = os.path.dirname(save_to)
                    if not os.path.exists(dist_dir):
                        os.makedirs(dist_dir, exist_ok=True)
                    shutil.copy(file_path, save_to)

                if _filter(file_path) == False:
                    continue
                else:
                    content = read_file(file_path)
                    translated_content = translator.translate(
                        content, config.from_locale, locale, config.prompts
                    )
                    # 替换输出目录，保持目录结构
                    write_file(translated_content, save_to)

                    # 更新md5，并保存
                    meta_config.update(file_path)
                    meta_config.save()

    _build()
