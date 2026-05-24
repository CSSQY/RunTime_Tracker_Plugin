"""
Run Time Tracker Plugin - 完整功能插件

一个对接时间跟踪应用程序的插件，用于麦麦监控您的设备使用时间。

作者：CSSQY
版本：1.2.0

支持 Command 和 Tool 组件，调用 RunTime Tracker API 获取设备使用数据。
"""

import re
from typing import Any, Dict, Optional, Tuple

from maibot_sdk import MaiBotPlugin, Command, Tool
from maibot_sdk.types import ToolParameterInfo, ToolParamType

from .utils import (
    get_devices,
    get_device_recent,
    get_device_stats,
    get_weekly_stats,
    get_ai_summary,
    format_devices_list,
    format_recent_records,
    format_stats,
    format_weekly_stats,
    format_ai_summary,
)


class RunTimeTrackerPlugin(MaiBotPlugin):
    """RunTime Tracker 插件 - 查询设备使用时间"""

    async def on_load(self) -> None:
        """插件加载完成"""

    async def on_unload(self) -> None:
        """插件卸载前"""

    async def on_config_update(self, scope: str, config_data: Dict[str, Any], version: str) -> None:
        """配置热更新"""

    async def _get_plugin_config(self, key: str, default: Any = None) -> Any:
        """从插件自身 config.toml 读取配置值（支持点分隔路径）。"""
        plugin_config = await self.ctx.call_capability("config.get_plugin")
        current = plugin_config
        try:
            for part in key.split("."):
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            return current
        except Exception:
            return default

    @Command(
        "runtime",
        description="查询设备使用时间统计",
        pattern=r"^/runtime(?:\s+(?P<subcmd>\w+)(?:\s+(?P<args>.*))?)?$",
    )
    async def runtime_command(
        self,
        stream_id: str = "",
        matched_groups: dict | None = None,
        raw_message: str = "",
        **kwargs,
    ) -> Tuple[bool, Optional[str], bool]:
        matched_groups = matched_groups or {}
        subcmd = matched_groups.get("subcmd", "")
        args = matched_groups.get("args") or ""

        admin_only = await self._get_plugin_config("security.admin_only")
        admin_users = await self._get_plugin_config("security.admin_users")

        if admin_only:
            user_id = str(kwargs.get("user_id", "") or "")
            if not user_id:
                await self.ctx.send.text("无法获取用户身份", stream_id)
                return False, "无法获取用户身份", True

            if not admin_users:
                await self.ctx.send.text("未配置管理员用户列表", stream_id)
                return False, "未配置管理员", True

            admin_list = [u.strip() for u in admin_users.split(",")]
            is_admin = user_id in admin_list

            if not is_admin:
                await self.ctx.send.text(f"此功能仅限管理员使用 (当前用户ID: {user_id})", stream_id)
                return False, "权限不足", True

        api_base_url = await self._get_plugin_config("api.base_url")
        secret = await self._get_plugin_config("api.secret")
        default_device = await self._get_plugin_config("api.default_device")

        if not api_base_url:
            await self.ctx.send.text("错误：未配置 API 地址，请在插件配置中设置 api.base_url", stream_id)
            return False, "未配置 API 地址", True

        if not secret:
            await self.ctx.send.text("错误：未配置 API 密钥，请在插件配置中设置 api.secret", stream_id)
            return False, "未配置 API 密钥", True

        if not subcmd:
            await self.ctx.send.text(
                "📱 RunTime Tracker 使用指南：\n\n"
                "/runtime devices - 查看所有设备\n"
                "/runtime recent <设备名> - 查看最近记录\n"
                "/runtime stats <设备名> [日期] - 查看单日统计\n"
                "/runtime weekly <设备名> [周偏移] - 查看周统计",
                stream_id,
            )
            return True, "显示帮助信息", True

        if subcmd == "devices":
            result = await get_devices(api_base_url, secret)
            if result is None:
                await self.ctx.send.text("获取设备列表失败，请检查 API 配置", stream_id)
                return False, "获取设备列表失败", True
            formatted = format_devices_list(result)
            await self.ctx.send.text(formatted, stream_id)
            return True, "获取设备列表成功", True

        if subcmd == "recent":
            device_id = (args or "").strip() or default_device
            if not device_id:
                await self.ctx.send.text("请指定设备名：/runtime recent <设备名>", stream_id)
                return False, "未指定设备", True
            result = await get_device_recent(api_base_url, secret, device_id)
            if result is None:
                await self.ctx.send.text(f"获取 {device_id} 的最近记录失败", stream_id)
                return False, "获取最近记录失败", True
            formatted = format_recent_records(result, device_id)
            await self.ctx.send.text(formatted, stream_id)
            return True, "获取最近记录成功", True

        if subcmd == "stats":
            parts = (args or "").strip().split(maxsplit=1)
            device_id = default_device
            date = None

            if len(parts) == 1:
                arg = parts[0]
                if arg:
                    if re.match(r"^\d{4}-\d{2}-\d{2}$", arg):
                        date = arg
                    else:
                        device_id = arg
            elif len(parts) > 1:
                device_id = parts[0] or default_device
                date = parts[1]

            if not device_id:
                await self.ctx.send.text("请指定设备名：/runtime stats <设备名> [日期]", stream_id)
                return False, "未指定设备", True
            if not date:
                from datetime import date as date_type
                date = date_type.today().isoformat()
            result = await get_device_stats(api_base_url, secret, device_id, date)
            if result is None:
                await self.ctx.send.text(
                    f"获取 {device_id} 在 {date} 的统计失败，请检查日期格式（YYYY-MM-DD）",
                    stream_id,
                )
                return False, "获取统计失败", True
            formatted = format_stats(result, device_id, date)
            await self.ctx.send.text(formatted, stream_id)
            return True, "获取统计成功", True

        if subcmd == "weekly":
            parts = (args or "").strip().split(maxsplit=1)
            device_id = parts[0] if parts else ""
            week_offset = 0
            if len(parts) > 1:
                try:
                    week_offset = int(parts[1])
                except ValueError:
                    pass
            device_id = device_id or default_device
            if not device_id:
                await self.ctx.send.text("请指定设备名：/runtime weekly <设备名> [周偏移]", stream_id)
                return False, "未指定设备", True
            result = await get_weekly_stats(api_base_url, secret, device_id, week_offset)
            if result is None:
                await self.ctx.send.text(f"获取 {device_id} 的周统计失败", stream_id)
                return False, "获取周统计失败", True
            formatted = format_weekly_stats(result, device_id, week_offset)
            await self.ctx.send.text(formatted, stream_id)
            return True, "获取周统计成功", True

        await self.ctx.send.text(f"未知子命令：{subcmd}，请使用 /runtime 查看帮助", stream_id)
        return False, f"未知子命令: {subcmd}", True

    @Tool(
        "get_device_list",
        description="获取所有已注册设备的列表及当前状态，包括设备名称、当前应用、运行状态、电池电量等",
        parameters=[],
    )
    async def get_device_list_tool(self, **kwargs) -> Dict[str, Any]:
        api_base_url = await self._get_plugin_config("api.base_url")
        secret = await self._get_plugin_config("api.secret")

        if not api_base_url:
            return {"name": "get_device_list", "content": "错误：未配置 API 地址"}
        if not secret:
            return {"name": "get_device_list", "content": "错误：未配置 API 密钥"}

        result = await get_devices(api_base_url, secret)
        if result is None:
            return {"name": "get_device_list", "content": "获取设备列表失败，请检查 API 配置"}
        return {"name": "get_device_list", "content": format_devices_list(result)}

    @Tool(
        "get_device_recent",
        description="获取指定设备最近30条应用切换记录，包括应用名称、时间戳和运行状态",
        parameters=[
            ToolParameterInfo(
                name="device_id",
                param_type=ToolParamType.STRING,
                description="设备唯一标识符，如：手机、平板",
                required=True,
            ),
        ],
    )
    async def get_device_recent_tool(self, device_id: str = "", **kwargs) -> Dict[str, Any]:
        if not device_id:
            return {"name": "get_device_recent", "content": "错误：缺少设备ID参数"}

        api_base_url = await self._get_plugin_config("api.base_url")
        secret = await self._get_plugin_config("api.secret")

        if not api_base_url:
            return {"name": "get_device_recent", "content": "错误：未配置 API 地址"}
        if not secret:
            return {"name": "get_device_recent", "content": "错误：未配置 API 密钥"}

        result = await get_device_recent(api_base_url, secret, device_id)
        if result is None:
            return {"name": "get_device_recent", "content": f"获取 {device_id} 的最近记录失败"}
        return {"name": "get_device_recent", "content": format_recent_records(result, device_id)}

    @Tool(
        "get_device_stats",
        description="获取指定设备某天的使用统计数据，包括总使用时长、各应用使用时长、每小时使用时长",
        parameters=[
            ToolParameterInfo(
                name="device_id",
                param_type=ToolParamType.STRING,
                description="设备唯一标识符",
                required=True,
            ),
            ToolParameterInfo(
                name="date",
                param_type=ToolParamType.STRING,
                description="查询日期，格式 YYYY-MM-DD，默认为当天",
                required=False,
            ),
        ],
    )
    async def get_device_stats_tool(self, device_id: str = "", date: str = "", **kwargs) -> Dict[str, Any]:
        if not device_id:
            return {"name": "get_device_stats", "content": "错误：缺少设备ID参数"}

        if not date:
            from datetime import date as date_type
            date = date_type.today().isoformat()

        api_base_url = await self._get_plugin_config("api.base_url")
        secret = await self._get_plugin_config("api.secret")

        if not api_base_url:
            return {"name": "get_device_stats", "content": "错误：未配置 API 地址"}
        if not secret:
            return {"name": "get_device_stats", "content": "错误：未配置 API 密钥"}

        result = await get_device_stats(api_base_url, secret, device_id, date)
        if result is None:
            return {"name": "get_device_stats", "content": f"获取 {device_id} 在 {date} 的统计失败"}
        return {"name": "get_device_stats", "content": format_stats(result, device_id, date)}

    @Tool(
        "get_weekly_stats",
        description="获取指定设备某周的统计数据（7天内每个应用的每日使用时间）",
        parameters=[
            ToolParameterInfo(
                name="device_id",
                param_type=ToolParamType.STRING,
                description="设备唯一标识符",
                required=True,
            ),
            ToolParameterInfo(
                name="week_offset",
                param_type=ToolParamType.INTEGER,
                description="周偏移，0=本周，-1=上周，-2=上上周",
                required=False,
            ),
        ],
    )
    async def get_weekly_stats_tool(self, device_id: str = "", week_offset: int = 0, **kwargs) -> Dict[str, Any]:
        if not device_id:
            return {"name": "get_weekly_stats", "content": "错误：缺少设备ID参数"}

        api_base_url = await self._get_plugin_config("api.base_url")
        secret = await self._get_plugin_config("api.secret")

        if not api_base_url:
            return {"name": "get_weekly_stats", "content": "错误：未配置 API 地址"}
        if not secret:
            return {"name": "get_weekly_stats", "content": "错误：未配置 API 密钥"}

        result = await get_weekly_stats(api_base_url, secret, device_id, week_offset)
        if result is None:
            return {"name": "get_weekly_stats", "content": f"获取 {device_id} 的周统计失败"}
        return {"name": "get_weekly_stats", "content": format_weekly_stats(result, device_id, week_offset)}

    @Tool(
        "get_ai_summary",
        description="获取指定设备最近生成的 AI 使用总结，包含设备使用行为的智能分析",
        parameters=[
            ToolParameterInfo(
                name="device_id",
                param_type=ToolParamType.STRING,
                description="设备唯一标识符",
                required=True,
            ),
        ],
    )
    async def get_ai_summary_tool(self, device_id: str = "", **kwargs) -> Dict[str, Any]:
        if not device_id:
            return {"name": "get_ai_summary", "content": "错误：缺少设备ID参数"}

        api_base_url = await self._get_plugin_config("api.base_url")
        secret = await self._get_plugin_config("api.secret")

        if not api_base_url:
            return {"name": "get_ai_summary", "content": "错误：未配置 API 地址"}
        if not secret:
            return {"name": "get_ai_summary", "content": "错误：未配置 API 密钥"}

        result = await get_ai_summary(api_base_url, secret, device_id)
        if result is None:
            return {"name": "get_ai_summary", "content": f"获取 {device_id} 的 AI 总结失败"}
        return {"name": "get_ai_summary", "content": format_ai_summary(result, device_id)}


def create_plugin():
    return RunTimeTrackerPlugin()
