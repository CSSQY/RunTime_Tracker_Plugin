from typing import List, Tuple, Type, Dict, Any
from src.plugin_system import BasePlugin, register_plugin, BaseTool, ComponentInfo
import aiohttp
import json

# ===== Tool组件 =====

class RuntimeTrackerTool(BaseTool):
    """RunTime Tracker工具 - 查询用户设备使用情况"""
    
    name = "runtime_tracker_tool"
    available_for_llm = True  # 允许LLM调用此工具
    
    @property
    def description(self):
        """从配置文件获取工具描述"""
        default_username = self.get_config("user.default_username", "用户")
        device_count = self.get_config("devices.device_count", 0)
        device_names = self.get_config("devices.device_names", [])
        device_list = "、".join(device_names) if device_names else "无"
        return f"当需要找{default_username}，或者{default_username}主动查询设备使用情况时，查询其设备使用情况，{default_username}有{device_count}个设备：{device_list}"
    
    @property
    def parameters(self):
        """从配置文件获取参数描述"""
        device_names = self.get_config("devices.device_names", [])
        device_list = "、".join(device_names) if device_names else "无"
        return [
            ("query_type", "string", "查询类型: devices(设备列表), recent(最近记录), stats(统计数据), weekly(周统计), ai_summary(AI总结)", True),
            ("device_id", "string", f"设备ID，可选设备有：{device_list}，不填则查询所有设备", False),
            ("date", "string", "日期，格式YYYY-MM-DD，查询stats时使用", False),
            ("week_offset", "integer", "周偏移，0=本周，-1=上周，查询weekly时使用", False),
            ("app_name", "string", "应用名称，查询weekly时可指定", False)
        ]
    
    @property
    def API_BASE_URL(self):
        """从配置文件获取API基础URL"""
        return self.get_config("api.base_url", "https://sleepyapi.cssqy.top")
    
    @property
    def API_TOKEN(self):
        """从配置文件获取API令牌"""
        return self.get_config("api.token", "")
    
    async def execute(self, function_args: dict) -> Dict[str, Any]:
        """执行工具逻辑"""
        try:
            query_type = function_args.get("query_type")
            device_id = function_args.get("device_id")
            date = function_args.get("date")
            week_offset = function_args.get("week_offset", 0)
            app_name = function_args.get("app_name")
            
            # 构建API请求URL
            url = await self._build_url(query_type, device_id, date, week_offset, app_name)
            
            # 发送请求
            data = await self._fetch_data(url)
            
            # 格式化结果
            result = await self._format_result(query_type, data)
            
            # 获取默认用户名
            default_username = self.get_config("user.default_username", "CSSQY")
            result = f"用户: {default_username}\n" + result
            
            return {
                "name": self.name,
                "content": result,
                "thought": f"已查询{default_username}的{query_type}信息，结果将用于智能对话参考"
            }
            
        except Exception as e:
            # 获取默认用户名
            default_username = self.get_config("user.default_username", "CSSQY")
            error_message = f"查询失败: {str(e)}"
            return {
                "name": self.name,
                "content": error_message,
                "thought": f"查询{default_username}设备信息失败，将在对话中告知用户"
            }
    
    async def _build_url(self, query_type: str, device_id: str = None, date: str = None, week_offset: int = 0, app_name: str = None) -> str:
        """构建API请求URL"""
        base_url = self.API_BASE_URL
        if query_type == "devices":
            return f"{base_url}/api/devices"
        elif query_type == "recent" and device_id:
            return f"{base_url}/api/recent/{device_id}"
        elif query_type == "stats" and device_id:
            url = f"{base_url}/api/stats/{device_id}"
            if date:
                url += f"?date={date}"
            return url
        elif query_type == "weekly" and device_id:
            url = f"{base_url}/api/weekly/{device_id}?weekOffset={week_offset}"
            if app_name:
                url += f"&appName={app_name}"
            return url
        elif query_type == "ai_summary" and device_id:
            return f"{base_url}/api/ai/summary/{device_id}"
        else:
            raise ValueError("无效的查询类型或参数")
    
    async def _fetch_data(self, url: str) -> dict:
        """获取API数据"""
        headers = {}
        if self.API_TOKEN:
            headers["Authorization"] = f"Bearer {self.API_TOKEN}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"API请求失败: {response.status}")
                return await response.json()
    
    async def _format_result(self, query_type: str, data: dict) -> str:
        """格式化结果"""
        if query_type == "devices":
            return self._format_devices(data)
        elif query_type == "recent":
            return self._format_recent(data)
        elif query_type == "stats":
            return self._format_stats(data)
        elif query_type == "weekly":
            return self._format_weekly(data)
        elif query_type == "ai_summary":
            return self._format_ai_summary(data)
        else:
            return str(data)
    
    def _format_devices(self, devices: list) -> str:
        """格式化设备列表"""
        if not devices:
            return "暂无设备数据"
        
        result = "📱 设备列表\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for device in devices:
            device_name = device.get("device", "未知设备")
            current_app = device.get("currentApp", "无")
            running = device.get("running", False)
            battery_level = device.get("batteryLevel", "未知")
            is_charging = device.get("isCharging", False)
            
            status = "运行中" if running else "未运行"
            charging_status = "充电中" if is_charging else "未充电"
            
            result += f"🔹 {device_name}\n"
            result += f"   当前应用: {current_app}\n"
            result += f"   状态: {status}\n"
            result += f"   电池: {battery_level}% ({charging_status})\n"
            result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        return result
    
    def _format_recent(self, data: dict) -> str:
        """格式化最近记录"""
        if not data.get("success"):
            return "查询失败"
        
        records = data.get("data", [])
        count = data.get("count", 0)
        
        result = f"📊 最近应用切换记录 (共{count}条)\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for record in records:
            app_name = record.get("appName", "未知应用")
            timestamp = record.get("timestamp", "未知时间")
            running = record.get("running", False)
            
            status = "运行中" if running else "已停止"
            
            result += f"🔹 {app_name}\n"
            result += f"   时间: {timestamp}\n"
            result += f"   状态: {status}\n"
            result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        return result
    
    def _format_stats(self, data: dict) -> str:
        """格式化统计数据"""
        total = data.get("total", 0)
        apps = data.get("apps", {})
        
        result = f"📈 设备使用统计\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        result += f"总使用时长: {total}分钟\n\n"
        result += "应用使用时长:\n"
        
        for app, duration in apps.items():
            result += f"🔹 {app}: {duration}分钟\n"
        
        return result
    
    def _format_weekly(self, data: dict) -> str:
        """格式化周统计数据"""
        week_offset = data.get("weekOffset", 0)
        week_range = data.get("weekRange", {})
        daily_totals = data.get("dailyTotals", {})
        app_daily_stats = data.get("appDailyStats", {})
        
        result = f"📅 周统计数据 (偏移: {week_offset})\n"
        result += f"日期范围: {week_range.get('start', '')} 至 {week_range.get('end', '')}\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        result += "每日总使用时长:\n"
        
        for date, duration in daily_totals.items():
            result += f"🔹 {date}: {duration}分钟\n"
        
        result += "\n各应用每日使用时长:\n"
        for app, daily_stats in app_daily_stats.items():
            result += f"\n{app}:\n"
            for date, duration in daily_stats.items():
                result += f"   🔹 {date}: {duration}分钟\n"
        
        return result
    
    def _format_ai_summary(self, data: dict) -> str:
        """格式化AI总结"""
        success = data.get("success", False)
        if not success:
            return "AI总结获取失败"
        
        device_id = data.get("deviceId", "未知设备")
        summary = data.get("summary", "无总结内容")
        timestamp = data.get("timestamp", "未知时间")
        date_range = data.get("dateRange", {})
        
        result = f"🤖 设备AI总结\n"
        result += f"设备: {device_id}\n"
        result += f"生成时间: {timestamp}\n"
        result += f"覆盖范围: {date_range.get('start', '')} 至 {date_range.get('end', '')}\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        result += summary
        
        return result

@register_plugin
class RuntimeTrackerPlugin(BasePlugin):
    """RunTime Tracker插件 - 为MaiBot提供设备使用情况查询功能"""

    # 插件基本信息
    plugin_name = "runtime_tracker_plugin"
    enable_plugin = True  # 启用插件
    dependencies = []  # 插件依赖列表
    python_dependencies = ["aiohttp"]  # Python依赖列表
    config_file_name = "config.toml"  # 配置文件名
    config_schema = {
        "api": {
            "base_url": {
                "type": "string",
                "default": "https://sleepyapi.cssqy.top",
                "description": "API基础URL"
            },
            "token": {
                "type": "string",
                "default": "",
                "description": "API访问令牌"
            }
        },
        "user": {
            "default_username": {
                "type": "string",
                "default": "CSSQY",
                "description": "默认用户名"
            },
            "username_keywords": {
                "type": "array",
                "default": ["CSSQY", "管理员"],
                "description": "用户名关键词列表"
            }
        },
        "devices": {
            "device_count": {
                "type": "integer",
                "default": 2,
                "description": "设备数量"
            },
            "device_names": {
                "type": "array",
                "default": ["CSSQY的电脑", "手机"],
                "description": "设备列表"
            }
        }
    }  # 配置文件模式

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        """返回插件包含的组件列表"""
        default_username = self.get_config("user.default_username", "CSSQY")
        return [
            (ComponentInfo("tool", "runtime_tracker_tool", f"查询{default_username}设备使用情况的工具"), RuntimeTrackerTool)
        ]