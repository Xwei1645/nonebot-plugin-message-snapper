<div align="center">
    <a href="https://v2.nonebot.dev/store">
    <img src="https://raw.githubusercontent.com/fllesser/nonebot-plugin-template/refs/heads/resource/.docs/NoneBotPlugin.svg" width="310" alt="logo"></a>

## ✨ nonebot-plugin-message-snapper ✨
[![LICENSE](https://img.shields.io/github/license/Xwei1645/nonebot-plugin-message-snapper.svg)](./LICENSE)
[![pypi](https://img.shields.io/pypi/v/nonebot-plugin-message-snapper.svg)](https://pypi.python.org/pypi/nonebot-plugin-message-snapper)
[![python](https://img.shields.io/badge/python-3.10|3.11|3.12|3.13-blue.svg)](https://www.python.org)
[![uv](https://img.shields.io/badge/package%20manager-uv-black?style=flat-square&logo=uv)](https://github.com/astral-sh/uv)
<br/>
[![ruff](https://img.shields.io/badge/code%20style-ruff-black?style=flat-square&logo=ruff)](https://github.com/astral-sh/ruff)
[![pre-commit](https://results.pre-commit.ci/badge/github/Xwei1645/nonebot-plugin-message-snapper/master.svg)](https://results.pre-commit.ci/latest/github/Xwei1645/nonebot-plugin-message-snapper/master)

</div>

## 📖 介绍

Message Snapper 是一个可用于自动生成 QQ 群聊中单条消息伪截图的 NoneBot 插件。

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-message-snapper --upgrade
使用 **pypi** 源安装

    nb plugin install nonebot-plugin-message-snapper --upgrade -i "https://pypi.org/simple"
使用**清华源**安装

    nb plugin install nonebot-plugin-message-snapper --upgrade -i "https://pypi.tuna.tsinghua.edu.cn/simple"


</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details open>
<summary>uv</summary>

    uv add nonebot-plugin-message-snapper
安装仓库 master 分支

    uv add git+https://github.com/Xwei1645/nonebot-plugin-message-snapper@master
</details>

<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-message-snapper
安装仓库 master 分支

    pdm add git+https://github.com/Xwei1645/nonebot-plugin-message-snapper@master
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-message-snapper
安装仓库 master 分支

    poetry add git+https://github.com/Xwei1645/nonebot-plugin-message-snapper@master
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_message_snapper"]

</details>

<details>
<summary>使用 nbr 安装(使用 uv 管理依赖可用)</summary>

[nbr](https://github.com/fllesser/nbr) 是一个基于 uv 的 nb-cli，可以方便地管理 nonebot2

    nbr plugin install nonebot-plugin-message-snapper
使用 **pypi** 源安装

    nbr plugin install nonebot-plugin-message-snapper -i "https://pypi.org/simple"
使用**清华源**安装

    nbr plugin install nonebot-plugin-message-snapper -i "https://pypi.tuna.tsinghua.edu.cn/simple"

</details>


## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

| 配置项  | 必填  | 默认值 |   说明   |
| :-----: | :---: | :----: | :------: |
| `message_snapper_template` | 否 | - | 自定义模板文件 |
| `message_snapper_font_family` | 否 | - | 用于渲染图片的字体家族 |
| `message_snapper_group_info_cache_hours` | 否 | `72.0` | 群信息缓存时长（小时） |
| `message_snapper_member_info_cache_hours` | 否 | `72.0` | 群成员信息缓存时长（小时） |

## 🎉 使用
### 指令表
| 指令  | 权限  | 需要@ | 范围  |   说明   |
| :---: | :---: | :---: | :---: | :------: |
| 'snap' 并引用一条消息 | 群成员  |  否   | 群聊  | 生成被引用消息的伪截图 |

### 🎨 效果图
没有效果图
