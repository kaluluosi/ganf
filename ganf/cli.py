import asyncio
import glob
import sys
import typing as t
import click
import os

from click.core import Context
import tqdm
from ganf.record import Record

from ganf.utils import read_doc
from .config import (
    GLOBAL_OPENAI_CONFIG_FILE,
    GANF_DIR,
    OPENAI_CONFIG_FILE,
    GANF_CONFIG,
    IGNORE_FILE,
    OPENAI_CONFIG_FILE,
    GanfConfig,
    OpenAIConfig,
    load_ganf_config,
    load_gitignore,
    load_openai_config,
    ganf_config_var,
    openai_config_var,
    gitignore_var,
)
from .translator import RECORD_FILE, cost_accounting, translate_dir, translate_file


class OrderCommands(click.Group):
    def list_commands(self, ctx: Context) -> list[str]:
        return list(self.commands)


def openai_configurate(ctx: Context, param: click.Parameter, value: str) -> None:
    value = (
        value if os.path.exists(value) else GLOBAL_OPENAI_CONFIG_FILE
    )  # 如果本地配置不存在就用全局配置

    # 如果全局都不存在就转而去执行openai配置设置向导了
    if not os.path.exists(value):
        answer = click.confirm(f"没有配置openai.toml，是否现在配置？", default=True, abort=True)
        if answer:
            _global = click.confirm("是否使用全局配置？", default=True, abort=True)
            ctx.invoke(setup, g=_global)

        sys.exit()
    else:
        load_openai_config(value)


openai_config_option = click.option(
    "--openai",
    type=click.Path(exists=False),
    default=OPENAI_CONFIG_FILE,
    callback=openai_configurate,
    show_default=True,
    help="openai配置文件",
)


def ganf_configurate(ctx: Context, param: click.Parameter, value: str) -> None:
    if not os.path.exists(value):
        click.echo(f"当前目录没有配置文件，请使用 `ganf init` 命令创建配置文件。")
        sys.exit()
    load_ganf_config(value)


ganf_config_option = click.option(
    "-c",
    "--config",
    type=click.Path(exists=False),
    default=GANF_CONFIG,
    is_eager=True,
    callback=ganf_configurate,
    show_default=True,
    help="配置文件",
)


def ignore_configure(ctx: Context, param: click.Parameter, value: str):
    if os.path.exists(value):
        load_gitignore(value, os.path.dirname(value))
    else:
        click.echo("没有.ignore文件，将对所有文档进行翻译。")


gitignore_option = click.option(
    "-i",
    "--ignore",
    type=click.Path(exists=False),
    default=IGNORE_FILE,
    is_eager=True,
    callback=ignore_configure,
    show_default=True,
    help="忽略列表",
)


@click.group(cls=OrderCommands)
def main(*args, **kwargs):
    """
    基于openai的批量文档翻译工具
    """


@main.command()
@click.option("-l", "--local", is_flag=True, help="全局配置")
def setup(local: bool, *args, **kwargs):
    """
    配置openai.toml全局配置文件。
    """

    def _create_config(save_to: str):
        config = OpenAIConfig()
        data = config.model_dump()
        for k, v in data.items():
            v = click.prompt(k, default=v, show_default=True)
            data[k] = v

        config = OpenAIConfig.model_validate(data)
        config.save(save_to)
        click.echo(save_to)

    if not local:
        click.echo("正在配置全局配置文件...")
        if not os.path.exists(GLOBAL_OPENAI_CONFIG_FILE):
            os.makedirs(GANF_DIR, exist_ok=True)
        else:
            click.echo("全局配置文件已存在，请删除后再试。")
            sys.exit()

        _create_config(GLOBAL_OPENAI_CONFIG_FILE)
    else:
        click.echo("正在配置项目配置文件...")
        if not os.path.exists(OPENAI_CONFIG_FILE):
            _create_config(OPENAI_CONFIG_FILE)
        else:
            click.echo("项目配置文件已存在，请删除后再试。")
            sys.exit()


@main.command()
@click.argument("source_dir", type=click.Path(exists=True))
def init(source_dir: str):
    """
    初始化翻译项目
    """
    if os.path.exists(GANF_CONFIG):
        click.echo("ganf 配置文件已存在")
        sys.exit()

    dist_dir = click.prompt(
        "输出目录",
        default="./",
        show_default=True,
        type=click.Path(exists=False, dir_okay=True, file_okay=False),
    )
    extensions = click.prompt(
        "扩展名(逗号分隔)",
        default="md",
        show_default=True,
        type=click.Path(exists=False),
        value_proc=lambda v: v.split(","),
    )

    locales = click.prompt(
        "翻译语言(逗号分隔)",
        default="zh",
        show_default=True,
        value_proc=lambda v: v.split(","),
    )

    config = GanfConfig(
        source_dir=source_dir, dist_dir=dist_dir, extensions=extensions, locales=locales
    )
    config.save(GANF_CONFIG)

    # 创建一个默认忽略文件
    with open(IGNORE_FILE, "w") as f:
        lines = ["*.*\n", *[f"!*.{extension}\n" for extension in extensions]]
        f.writelines(lines)


@main.command()
@ganf_config_option
@gitignore_option
@openai_config_option
def cost(*args, **kwargs):
    """
    计算整个项目翻译成本
    """
    openai_config = openai_config_var.get()
    ganf_config = ganf_config_var.get()
    ignore = gitignore_var.get()

    record_path = os.path.join(ganf_config.dist_dir, RECORD_FILE)
    if os.path.exists(record_path):
        # 输出目录有记录文件就读取
        record = Record.load(record_path)
    else:
        # 输出目录没有记录文件就新建一个记录
        record = Record()

    total_cost = 0
    total_tokens = 0
    cost = openai_config.cost
    files = list(
        filter(
            lambda f: not ignore(f) and record.is_modified(f),
            glob.glob(f"{ganf_config.source_dir}/**/*.*", recursive=True),
        )
    )
    bar = tqdm.tqdm(files, desc="计算成本", postfix="$0")

    total_files = len(files)

    for doc_path in bar:
        doc = read_doc(doc_path)
        doc_cost, tokens = cost_accounting(doc, cost)
        total_cost += doc_cost
        total_tokens += len(tokens)
        bar.set_postfix_str(f"${total_cost}")

    locale_count = len(ganf_config.locales)

    click.echo(f"Total:{total_files}")
    click.echo(f"Tokens:{total_tokens}")
    click.echo(f"{locale_count} Language Cost:${locale_count*total_cost}")


@main.command()
@ganf_config_option
@gitignore_option
@openai_config_option
@click.option("-q", "--quiet", is_flag=True, default=False, help="是否静默执行，不询问成本")
@click.pass_context
def build(ctx: Context, quiet: bool, *args, **kwargs):
    """
    根据ganf.toml配置翻译整个项目
    """
    if not quiet:
        ctx.invoke(cost)
        click.confirm("是否继续翻译？", abort=True)

    ganf_config = ganf_config_var.get()

    # 因为openai的并发限制，无法并发太多的请求
    async def _main():
        for locale in ganf_config.locales:
            await translate_dir(ganf_config.source_dir, ganf_config.dist_dir, locale)

    asyncio.run(_main())


@main.command()
@openai_config_option
@click.argument("file", type=click.Path(file_okay=True, dir_okay=False))
@click.option("-l", "--locale", default="zh", help="翻译到哪个语言")
@click.option(
    "-o", "--output", default="", help="输出文件路径，默认在文件名后面加上语言码，例如 README.zh.md。"
)
@click.option("-p", "--prompt", multiple=True, help="翻译提示，用来微调翻译质量用")
@click.option("-q", "--quiet", is_flag=True, default=False, help="是否静默执行，不询问成本")
def translate(
    file: str,
    locale: str = "zh",
    output: str = "",
    prompt: list[str] = [],
    quiet: bool = False,
    *args,
    **kwargs,
):
    """
    翻译单个文件
    """
    if not quiet:
        openai_config = openai_config_var.get()
        cost = openai_config.cost

        doc = read_doc(file)
        cost, tokens = cost_accounting(doc, cost)
        click.echo(f"Tokens:{len(tokens)}")
        click.echo(f"Cost:${cost}")
        click.confirm("是否继续翻译？", abort=True)

    if not output:
        basename = os.path.basename(file)
        name, ext = os.path.splitext(basename)
        output = f"./{name}.{locale}{ext}"

    asyncio.run(translate_file(file, output, locale, prompt))
