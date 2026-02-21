from nonebot import get_driver, on_command
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, GroupMessageEvent
from nonebot_plugin_message_snapper_core import MessageSnapper

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

_snapper = MessageSnapper(
    template=plugin_config.message_snapper_template or "default.html",
    font_family=plugin_config.message_snapper_font_family or None,
    group_cache_hours=plugin_config.message_snapper_group_info_cache_hours,
    member_cache_hours=plugin_config.message_snapper_member_info_cache_hours,
)

snap = on_command("snap", block=True)


@get_driver().on_startup
async def _on_startup() -> None:
    await _snapper.load_cache()


@get_driver().on_shutdown
async def _on_shutdown() -> None:
    await _snapper.save_cache()


@snap.handle()
async def handle_snap(bot: Bot, event: GroupMessageEvent) -> None:
    if event.reply is None:
        await snap.finish("请回复一条消息后再使用 /snap 命令")

    reply = event.reply
    sender = reply.sender
    group_id = event.group_id
    user_id = sender.user_id or 0

    try:
        img_bytes = await _snapper.generate_snapshot(
            bot=bot,
            group_id=group_id,
            user_id=user_id,
            message=reply.message,
            time=reply.time,
            sender_name=sender.card or sender.nickname or "未知用户",
            sender_level=sender.level,
            sender_title=sender.title,
            sender_role=sender.role,
        )
    except ValueError as e:
        await snap.finish(str(e))
    except Exception as e:
        await snap.finish(f"生成图片失败: {e!s}")

    await snap.finish(MessageSegment.image(img_bytes))
