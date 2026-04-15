"""
Run Time Tracker Plugin - 完整功能插件

一个对接时间跟踪应用程序的插件，用于麦麦监控您的设备使用时间。

作者：CSSQY
版本：1.1.0

支持 Command 和 Tool 组件，调用 RunTime Tracker API 获取设备使用数据。
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Type

from src.plugin_system import (
    BasePlugin,
    register_plugin,
    BaseCommand,
    BaseTool,
    ComponentInfo,
    ToolParamType,
    ConfigField,
)
from src.common.logger import get_logger

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

logger = get_logger("Run_Time_Tracker_plugin")


class RunTimeTrackerPluginCommand(BaseCommand):
    """命令响应组件 - 支持多子命令"""

    command_name = "runtime"
    command_description = "查询设备使用时间统计"
    command_pattern = r"^/runtime(?:\s+(?P<subcmd>\w+)(?:\s+(?P<args>.*))?)?$"

    async def execute(self) -> Tuple[bool, Optional[str], bool]:
        subcmd = self.matched_groups.get("subcmd", "")
        args = self.matched_groups.get("args") or ""

        admin_only = self.get_config("security.admin_only", False)
        admin_users = self.get_config("security.admin_users", "")

        if admin_only:
            admin_users = self.get_config("security.admin_users", "")
            if not admin_users:
                await self.send_text("未配置管理员用户列表")
                return False, "未配置管理员", True

            user_id = ""
            msg = getattr(self, "message", None)
            if msg:
                info = getattr(msg, "message_info", None)
                if info:
                    user_info = getattr(info, "user_info", None)
                    if user_info:
                        uid = getattr(user_info, "user_id", "")
                        if uid is not None:
                            user_id = str(uid)

            if not user_id:
                await self.send_text(f"无法获取用户身份 (当前: {user_id})")
                return False, "无法获取用户身份", True

            admin_list = [u.strip() for u in admin_users.split(",")]
            is_admin = user_id in admin_list

            if not is_admin:
                await self.send_text(f"此功能仅限管理员使用 (当前用户ID: {user_id})")
                return False, "权限不足", True

        api_base_url = self.get_config("api.base_url", "")
        secret = self.get_config("api.secret", "")
        default_device = self.get_config("api.default_device", "")

        if not api_base_url:
            await self.send_text("错误：未配置 API 地址，请在插件配置中设置 api.base_url")
            return False, "未配置 API 地址", True

        if not secret:
            await self.send_text("错误：未配置 API 密钥，请在插件配置中设置 api.secret")
            return False, "未配置 API 密钥", True

        if not subcmd:
            await self.send_text(
                "📱 RunTime Tracker 使用指南：\n\n"
                "/runtime devices - 查看所有设备\n"
                "/runtime recent <设备名> - 查看最近记录\n"
                "/runtime stats <设备名> [日期] - 查看单日统计\n"
                "/runtime weekly <设备名> [周偏移] - 查看周统计"
            )
            return True, "显示帮助信息", True

        if subcmd == "devices":
            result = await get_devices(api_base_url, secret)
            if result is None:
                await self.send_text("获取设备列表失败，请检查 API 配置")
                return False, "获取设备列表失败", True
            formatted = format_devices_list(result)
            await self.send_text(formatted)
            return True, "获取设备列表成功", True

        if subcmd == "recent":
            device_id = (args or "").strip() or default_device
            if not device_id:
                await self.send_text("请指定设备名：/runtime recent <设备名>")
                return False, "未指定设备", True
            result = await get_device_recent(api_base_url, secret, device_id)
            if result is None:
                await self.send_text(f"获取 {device_id} 的最近记录失败")
                return False, "获取最近记录失败", True
            formatted = format_recent_records(result, device_id)
            await self.send_text(formatted)
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
                await self.send_text("请指定设备名：/runtime stats <设备名> [日期]")
                return False, "未指定设备", True
            if not date:
                from datetime import date as date_type
                date = date_type.today().isoformat()
            result = await get_device_stats(api_base_url, secret, device_id, date)
            if result is None:
                await self.send_text(f"获取 {device_id} 在 {date} 的统计失败，请检查日期格式（YYYY-MM-DD）")
                return False, "获取统计失败", True
            formatted = format_stats(result, device_id, date)
            await self.send_text(formatted)
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
                await self.send_text("请指定设备名：/runtime weekly <设备名> [周偏移]")
                return False, "未指定设备", True
            result = await get_weekly_stats(api_base_url, secret, device_id, week_offset)
            if result is None:
                await self.send_text(f"获取 {device_id} 的周统计失败")
                return False, "获取周统计失败", True
            formatted = format_weekly_stats(result, device_id, week_offset)
            await self.send_text(formatted)
            return True, "获取周统计成功", True

        await self.send_text(f"未知子命令：{subcmd}，请使用 /runtime 查看帮助")
        return False, f"未知子命令: {subcmd}", True


class GetDeviceListTool(BaseTool):
    """获取所有设备列表工具"""

    name = "get_device_list"
    description = "获取所有已注册设备的列表及当前状态，包括设备名称、当前应用、运行状态、电池电量等"
    parameters = []
    available_for_llm = True

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        api_base_url = self.get_config("api.base_url", "")
        secret = self.get_config("api.secret", "")

        if not api_base_url:
            return {"name": self.name, "content": "错误：未配置 API 地址"}
        if not secret:
            return {"name": self.name, "content": "错误：未配置 API 密钥"}

        result = await get_devices(api_base_url, secret)
        if result is None:
            return {"name": self.name, "content": "获取设备列表失败，请检查 API 配置"}
        return {"name": self.name, "content": format_devices_list(result)}


class GetDeviceRecentTool(BaseTool):
    """获取设备最近记录工具"""

    name = "get_device_recent"
    description = "获取指定设备最近30条应用切换记录，包括应用名称、时间戳和运行状态"
    parameters = [
        ("device_id", ToolParamType.STRING, "设备唯一标识符，如：手机、平板", True, None),
    ]
    available_for_llm = True

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        device_id = function_args.get("device_id", "")
        if not device_id:
            return {"name": self.name, "content": "错误：缺少设备ID参数"}

        api_base_url = self.get_config("api.base_url", "")
        secret = self.get_config("api.secret", "")

        if not api_base_url:
            return {"name": self.name, "content": "错误：未配置 API 地址"}
        if not secret:
            return {"name": self.name, "content": "错误：未配置 API 密钥"}

        result = await get_device_recent(api_base_url, secret, device_id)
        if result is None:
            return {"name": self.name, "content": f"获取 {device_id} 的最近记录失败"}
        return {"name": self.name, "content": format_recent_records(result, device_id)}


class GetDeviceStatsTool(BaseTool):
    """获取设备单日统计工具"""

    name = "get_device_stats"
    description = "获取指定设备某天的使用统计数据，包括总使用时长、各应用使用时长、每小时使用时长"
    parameters = [
        ("device_id", ToolParamType.STRING, "设备唯一标识符", True, None),
        ("date", ToolParamType.STRING, "查询日期，格式 YYYY-MM-DD，默认为当天", False, None),
    ]
    available_for_llm = True

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        device_id = function_args.get("device_id", "")
        if not device_id:
            return {"name": self.name, "content": "错误：缺少设备ID参数"}

        date = function_args.get("date")
        if not date:
            from datetime import date as date_type
            date = date_type.today().isoformat()

        api_base_url = self.get_config("api.base_url", "")
        secret = self.get_config("api.secret", "")

        if not api_base_url:
            return {"name": self.name, "content": "错误：未配置 API 地址"}
        if not secret:
            return {"name": self.name, "content": "错误：未配置 API 密钥"}

        result = await get_device_stats(api_base_url, secret, device_id, date)
        if result is None:
            return {"name": self.name, "content": f"获取 {device_id} 在 {date} 的统计失败"}
        return {"name": self.name, "content": format_stats(result, device_id, date)}


class GetWeeklyStatsTool(BaseTool):
    """获取设备周统计工具"""

    name = "get_weekly_stats"
    description = "获取指定设备某周的统计数据（7天内每个应用的每日使用时间）"
    parameters = [
        ("device_id", ToolParamType.STRING, "设备唯一标识符", True, None),
        ("week_offset", ToolParamType.INTEGER, "周偏移，0=本周，-1=上周，-2=上上周", False, 0),
    ]
    available_for_llm = True

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        device_id = function_args.get("device_id", "")
        if not device_id:
            return {"name": self.name, "content": "错误：缺少设备ID参数"}

        week_offset = function_args.get("week_offset", 0)

        api_base_url = self.get_config("api.base_url", "")
        secret = self.get_config("api.secret", "")

        if not api_base_url:
            return {"name": self.name, "content": "错误：未配置 API 地址"}
        if not secret:
            return {"name": self.name, "content": "错误：未配置 API 密钥"}

        result = await get_weekly_stats(api_base_url, secret, device_id, week_offset)
        if result is None:
            return {"name": self.name, "content": f"获取 {device_id} 的周统计失败"}
        return {"name": self.name, "content": format_weekly_stats(result, device_id, week_offset)}


class GetAiSummaryTool(BaseTool):
    """获取设备AI总结工具"""

    name = "get_ai_summary"
    description = "获取指定设备最近生成的 AI 使用总结，包含设备使用行为的智能分析"
    parameters = [
        ("device_id", ToolParamType.STRING, "设备唯一标识符", True, None),
    ]
    available_for_llm = True

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        device_id = function_args.get("device_id", "")
        if not device_id:
            return {"name": self.name, "content": "错误：缺少设备ID参数"}

        api_base_url = self.get_config("api.base_url", "")
        secret = self.get_config("api.secret", "")

        if not api_base_url:
            return {"name": self.name, "content": "错误：未配置 API 地址"}
        if not secret:
            return {"name": self.name, "content": "错误：未配置 API 密钥"}

        result = await get_ai_summary(api_base_url, secret, device_id)
        if result is None:
            return {"name": self.name, "content": f"获取 {device_id} 的 AI 总结失败"}
        return {"name": self.name, "content": format_ai_summary(result, device_id)}


@register_plugin
class RunTimeTrackerPluginPlugin(BasePlugin):
    """RunTime Tracker 插件 - 查询设备使用时间"""

    plugin_name: str = "Run_Time_Tracker_plugin"
    enable_plugin: bool = True
    dependencies: List[str] = []
    python_dependencies: List[str] = ["aiohttp"]
    config_file_name: str = "config.toml"

    config_section_descriptions = {
        "plugin": "插件基本配置",
        "api": "API 连接配置",
        "security": "权限配置",
    }

    config_schema: dict = {
        "plugin": {
            "enabled": ConfigField(type=bool, default=True, description="是否启用插件"),
            "config_version": ConfigField(type=str, default="1.1.0", description="配置文件版本", hidden=True),
        },
        "api": {
            "base_url": ConfigField(
                type=str,
                default="",
                description="API 基础地址",
                placeholder="https://api.example.com/",
                required=True,
                order=1
            ),
            "secret": ConfigField(
                type=str,
                default="",
                description="API 请求密钥",
                input_type="password",
                placeholder="请输入 API 密钥",
                required=True,
                order=2
            ),
            "default_device": ConfigField(
                type=str,
                default="",
                description="默认设备名称",
                placeholder="如：手机",
                hint="设置了此项可简化命令，例如 /runtime stats 2025-01-01",
                order=3
            ),
        },
        "security": {
            "admin_only": ConfigField(
                type=bool,
                default=False,
                description="是否仅允许管理员使用指令",
                hint="开启后只有 admin_users 列表中的用户可以使用指令",
                order=1
            ),
            "admin_users": ConfigField(
                type=str,
                default="",
                description="管理员用户ID列表",
                placeholder="10001, 10002",
                hint="格式：用户ID，多个用逗号分隔",
                depends_on="security.admin_only",
                depends_value=True,
                order=2
            ),
        },
    }

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        return [
            (RunTimeTrackerPluginCommand.get_command_info(), RunTimeTrackerPluginCommand),
            (GetDeviceListTool.get_tool_info(), GetDeviceListTool),
            (GetDeviceRecentTool.get_tool_info(), GetDeviceRecentTool),
            (GetDeviceStatsTool.get_tool_info(), GetDeviceStatsTool),
            (GetWeeklyStatsTool.get_tool_info(), GetWeeklyStatsTool),
            (GetAiSummaryTool.get_tool_info(), GetAiSummaryTool),
        ]