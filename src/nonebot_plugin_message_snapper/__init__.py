from typing import Any
from pathlib import Path
from datetime import datetime

from nonebot import logger, require, get_driver, on_command
from nonebot.plugin import PluginMetadata
from nonebot.exception import FinishedException
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment, GroupMessageEvent

require("nonebot_plugin_htmlrender")
require("nonebot_plugin_localstore")

from nonebot_plugin_htmlrender import template_to_pic

from .cache import (
    load_cache,
    save_cache,
    get_group_info_cache,
    set_group_info_cache,
    get_member_info_cache,
    set_member_info_cache,
)
from .config import Config, plugin_config

__plugin_meta__ = PluginMetadata(
    name="消息快照",
    description="将引用的消息转换为图片发送",
    usage="回复一条消息并发送 /snap 命令，即可将该消息转换为图片",
    type="application",
    homepage="https://github.com/Xwei1645/nonebot-plugin-message-snapper",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

TEMPLATE_PATH = Path(__file__).parent / "templates"
DEFAULT_TEMPLATE = "default.html"
DEFAULT_FONT_FAMILY = (
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
    '"Helvetica Neue", Arial, "PingFang SC", '
    '"Hiragino Sans GB", "Microsoft YaHei", sans-serif'
)

AVATAR_URL = "https://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"

snap = on_command("snap", block=True)


@get_driver().on_startup
async def _on_startup() -> None:
    await load_cache()
    logger.info("缓存加载完成")


@get_driver().on_shutdown
async def _on_shutdown() -> None:
    await save_cache()
    logger.info("缓存保存完成")


def get_template_name() -> str:
    custom_template = plugin_config.message_snapper_template
    if not custom_template:
        return DEFAULT_TEMPLATE
    template_file = TEMPLATE_PATH / custom_template
    if template_file.exists():
        return custom_template
    logger.warning(f"自定义模板 {custom_template} 不存在，使用默认模板")
    return DEFAULT_TEMPLATE


def get_font_family() -> str:
    return plugin_config.message_snapper_font_family or DEFAULT_FONT_FAMILY


async def get_group_info(bot: Bot, group_id: int) -> dict[str, Any]:
    cached = get_group_info_cache(group_id)
    if cached is not None:
        return cached

    try:
        info = await bot.get_group_info(group_id=group_id)
        set_group_info_cache(group_id, info)
        return info
    except Exception:
        return {"group_name": "未知群", "member_count": 0}


async def get_member_info(bot: Bot, group_id: int, user_id: int) -> dict[str, Any]:
    cached = get_member_info_cache(group_id, user_id)
    if cached is not None:
        return cached

    try:
        info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
        set_member_info_cache(group_id, user_id, info)
        return info
    except Exception:
        return {}


@snap.handle()
async def handle_snap(bot: Bot, event: GroupMessageEvent) -> None:
    if event.reply is None:
        await snap.finish("请回复一条消息后再使用 /snap 命令")

    reply = event.reply
    sender = reply.sender
    group_id = event.group_id
    user_id = sender.user_id or 0

    sender_name = sender.card or sender.nickname or "未知用户"
    message_segments = extract_message_segments(reply.message)
    message_content = extract_text_content(reply.message)
    single_image_only = is_single_image_message(message_segments)

    if not message_segments:
        await snap.finish("无法获取消息内容，可能包含不支持的消息类型")

    time_str = datetime.fromtimestamp(reply.time).strftime("%Y-%m-%d %H:%M")

    group_info = await get_group_info(bot, group_id)
    group_name = group_info.get("group_name", "未知群")
    member_count = group_info.get("member_count", 0)

    member_info = await get_member_info(bot, group_id, user_id)
    if member_info:
        level = member_info.get("level", "") or ""
        title = member_info.get("title", "") or ""
        role = member_info.get("role", "") or ""
        card = member_info.get("card", "") or ""
        nickname = member_info.get("nickname", "") or ""
        sender_name = card or nickname or "未知用户"
    else:
        level = sender.level or ""
        title = sender.title or ""
        role = sender.role or ""

    avatar_url = AVATAR_URL.format(user_id=user_id)
    template_name = get_template_name()
    font_family = get_font_family()

    try:
        img_bytes = await template_to_pic(
            template_path=str(TEMPLATE_PATH),
            template_name=template_name,
            templates={
                "font_family": font_family,
                "group_name": group_name,
                "member_count": member_count,
                "avatar_url": avatar_url,
                "sender_name": sender_name,
                "sender_id": user_id,
                "level": level,
                "title": title,
                "role": role,
                "message_segments": message_segments,
                "single_image_only": single_image_only,
                "message_content": message_content,
                "time": time_str,
            },
        )
    except FinishedException:
        raise
    except Exception as e:
        logger.error(f"生成消息快照失败: {e}")
        await snap.finish(f"生成图片失败: {e!s}")

    logger.info(f"成功生成消息快照: 用户 {sender_name}({user_id})")
    await snap.finish(MessageSegment.image(img_bytes))


def extract_message_segments(message: Message) -> list[dict[str, str]]:
    if not isinstance(message, Message):
        content = str(message).strip()
        return [{"type": "text", "content": content}] if content else []

    parts = []
    for seg in message:
        if seg.type == "text":
            text = seg.data.get("text", "")
            if text:
                parts.append({"type": "text", "content": text})
        elif seg.type == "image":
            image_url = seg.data.get("url") or seg.data.get("file") or ""
            if image_url:
                parts.append({"type": "image", "content": image_url})
            else:
                parts.append({"type": "text", "content": "[图片]"})
        elif seg.type == "face":
            face_id = seg.data.get("id", 0)
            parts.append({"type": "text", "content": f"[表情:{face_id}]"})
        elif seg.type == "emoji":
            parts.append({"type": "text", "content": seg.data.get("text", "[emoji]")})
        elif seg.type == "at":
            qq = seg.data.get("qq", "")
            parts.append({"type": "text", "content": f"@{qq}"})
        else:
            parts.append({"type": "text", "content": f"[{seg.type}]"})

    return parts


def extract_text_content(message: Message) -> str:
    parts = []
    for seg in extract_message_segments(message):
        if seg["type"] == "image":
            parts.append("[图片]")
        else:
            parts.append(seg["content"])
    return "".join(parts).strip()


def is_single_image_message(message_segments: list[dict[str, str]]) -> bool:
    return (
        len(message_segments) == 1
        and message_segments[0].get("type") == "image"
        and bool(message_segments[0].get("content"))
    )
