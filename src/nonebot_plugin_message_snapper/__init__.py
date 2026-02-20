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
    reply_preview = await extract_reply_preview(bot, reply.message, group_id)
    message_segments = await extract_message_segments(bot, group_id, reply.message)
    message_content = await extract_text_content(bot, group_id, reply.message)
    single_image_only = is_single_image_message(message_segments)

    if not message_segments and reply_preview is None:
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
                "reply_preview": reply_preview,
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


def format_time(timestamp: Any) -> str:
    try:
        return datetime.fromtimestamp(float(timestamp)).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError, OSError):
        return "未知时间"


async def extract_reply_preview(bot: Bot, message: Message, group_id: int) -> dict[str, Any] | None:
    if not isinstance(message, Message):
        return None

    for seg in message:
        if seg.type != "reply":
            continue
        message_id = seg.data.get("id")
        if message_id is None:
            return None
        try:
            quoted = await bot.get_msg(message_id=int(message_id))
        except Exception as e:
            logger.warning(f"获取引用消息失败: {e}")
            return None

        sender = quoted.get("sender", {}) if isinstance(quoted, dict) else {}
        sender_name = (
            sender.get("card")
            or sender.get("nickname")
            or str(sender.get("user_id") or "未知用户")
        )
        quoted_message = normalize_message_payload(quoted.get("message", ""))
        segments = await extract_message_segments(bot, group_id, quoted_message)
        content = await extract_text_content(bot, group_id, quoted_message)
        return {
            "sender_name": sender_name,
            "time": format_time(quoted.get("time", 0)),
            "segments": segments,
            "content": content or "[消息]",
        }
    return None


def normalize_message_payload(payload: Any) -> Message:
    if isinstance(payload, Message):
        return payload
    if isinstance(payload, str):
        return Message(payload)
    if isinstance(payload, list):
        segments: list[MessageSegment] = []
        for item in payload:
            if isinstance(item, MessageSegment):
                segments.append(item)
                continue
            if isinstance(item, dict):
                seg_type = item.get("type")
                seg_data = item.get("data", {})
                if isinstance(seg_type, str) and isinstance(seg_data, dict):
                    segments.append(MessageSegment(seg_type, seg_data))
                    continue
            logger.warning(f"忽略无法解析的消息段: {item!r}")
        return Message(segments)
    if isinstance(payload, dict):
        seg_type = payload.get("type")
        seg_data = payload.get("data", {})
        if isinstance(seg_type, str) and isinstance(seg_data, dict):
            return Message([MessageSegment(seg_type, seg_data)])
    return Message(str(payload))


async def extract_message_segments(bot: Bot, group_id: int, message: Message) -> list[dict[str, str]]:
    message = normalize_message_payload(message)

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
            name = ""
            user_id = None
            if isinstance(qq, int):
                user_id = qq
            else:
                try:
                    user_id = int(qq)
                except Exception:
                    user_id = None
            if user_id is not None:
                member_info = await get_member_info(bot, group_id, user_id)
                card = member_info.get("card", "") or ""
                nickname = member_info.get("nickname", "") or ""
                name = card or nickname or str(user_id)
            else:
                name = qq or ""
            # leave no space between @ and nickname, but add a trailing space after nickname
            parts.append({"type": "text", "content": f"@{name} "})
        elif seg.type == "reply":
            continue
        else:
            parts.append({"type": "text", "content": f"[{seg.type}]"})

    # Merge adjacent text segments so that mentions and following text stay on the same line
    merged: list[dict[str, str]] = []
    for p in parts:
        if merged and p["type"] == "text" and merged[-1]["type"] == "text":
            prev = merged[-1]["content"]
            cur = p["content"]
            # Collapse boundary whitespace into a single space to avoid newlines or multiple spaces
            merged[-1]["content"] = prev.rstrip() + " " + cur.lstrip()
        else:
            merged.append(p.copy())

    return merged


async def extract_text_content(bot: Bot, group_id: int, message: Message) -> str:
    parts = []
    for seg in await extract_message_segments(bot, group_id, message):
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
