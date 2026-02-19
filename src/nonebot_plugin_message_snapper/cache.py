import json
from typing import Any
from pathlib import Path
from datetime import datetime

from nonebot import logger, require

require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store

from .config import plugin_config

_cache_file: Path = store.get_plugin_cache_file("cache.json")

_group_info_cache: dict[int, tuple[float, dict[str, Any]]] = {}
_member_info_cache: dict[tuple[int, int], tuple[float, dict[str, Any]]] = {}


def _get_cache_seconds(cache_type: str) -> float:
    if cache_type == "group":
        return plugin_config.message_snapper_group_info_cache_hours * 3600
    return plugin_config.message_snapper_member_info_cache_hours * 3600


async def load_cache() -> None:
    global _group_info_cache, _member_info_cache

    if not _cache_file.exists():
        return

    try:
        import aiofiles

        async with aiofiles.open(_cache_file, encoding="utf-8") as f:
            data = json.loads(await f.read())

        now = datetime.now().timestamp()

        for k, v in data.get("group_info", {}).items():
            if now - v[0] < _get_cache_seconds("group"):
                _group_info_cache[int(k)] = (v[0], v[1])

        for k, v in data.get("member_info", {}).items():
            if now - v[0] < _get_cache_seconds("member"):
                gid, uid = map(int, k.split(":"))
                _member_info_cache[(gid, uid)] = (v[0], v[1])

        logger.debug(
            f"加载缓存: 群信息 {len(_group_info_cache)} 条, "
            f"成员信息 {len(_member_info_cache)} 条"
        )
    except Exception as e:
        logger.warning(f"加载缓存失败: {e}")


async def save_cache() -> None:
    try:
        _cache_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "group_info": {str(k): [v[0], v[1]] for k, v in _group_info_cache.items()},
            "member_info": {
                f"{k[0]}:{k[1]}": [v[0], v[1]] for k, v in _member_info_cache.items()
            },
        }

        import aiofiles

        async with aiofiles.open(_cache_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False))

    except Exception as e:
        logger.warning(f"保存缓存失败: {e}")


def get_group_info_cache(group_id: int) -> dict[str, Any] | None:
    if group_id in _group_info_cache:
        cached_time, cached_data = _group_info_cache[group_id]
        if datetime.now().timestamp() - cached_time < _get_cache_seconds("group"):
            return cached_data
        del _group_info_cache[group_id]
    return None


def set_group_info_cache(group_id: int, data: dict[str, Any]) -> None:
    _group_info_cache[group_id] = (datetime.now().timestamp(), data)


def get_member_info_cache(group_id: int, user_id: int) -> dict[str, Any] | None:
    cache_key = (group_id, user_id)
    if cache_key in _member_info_cache:
        cached_time, cached_data = _member_info_cache[cache_key]
        if datetime.now().timestamp() - cached_time < _get_cache_seconds("member"):
            return cached_data
        del _member_info_cache[cache_key]
    return None


def set_member_info_cache(group_id: int, user_id: int, data: dict[str, Any]) -> None:
    _member_info_cache[(group_id, user_id)] = (datetime.now().timestamp(), data)
