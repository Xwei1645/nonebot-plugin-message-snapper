from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    message_snapper_template: str = ""
    message_snapper_font_family: str = ""
    message_snapper_group_info_cache_hours: float = 72.0
    message_snapper_member_info_cache_hours: float = 72.0


plugin_config: Config = get_plugin_config(Config)
