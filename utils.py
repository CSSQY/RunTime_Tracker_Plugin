"""
Run Time Tracker Plugin 工具函数模块

对接 RunTime Tracker API 的 HTTP 请求函数。
"""

import asyncio
import datetime
from typing import Optional, Dict, Any, List


async def safe_http_get(url: str, timeout: int = 10, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """
    安全的 HTTP GET 请求

    Args:
        url: 请求 URL
        timeout: 超时时间（秒）
        headers: 请求头

    Returns:
        JSON 响应字典，或失败时返回 None
    """
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout), headers=headers or {}) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except ImportError:
        raise ImportError("请先安装 aiohttp：pip install aiohttp")
    except Exception:
        return None


async def safe_http_post(url: str, data: Optional[Dict[str, Any]] = None, timeout: int = 10, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """
    安全的 HTTP POST 请求

    Args:
        url: 请求 URL
        data: POST 数据
        timeout: 超时时间（秒）
        headers: 请求头

    Returns:
        JSON 响应字典，或失败时返回 None
    """
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=timeout), headers=headers or {}) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except ImportError:
        raise ImportError("请先安装 aiohttp：pip install aiohttp")
    except Exception:
        return None


async def get_devices(api_base_url: str, secret: str) -> Optional[List[Dict[str, Any]]]:
    """
    获取所有设备列表

    Args:
        api_base_url: API 基础地址
        secret: API 密钥

    Returns:
        设备列表，或失败时返回 None
    """
    url = f"{api_base_url.rstrip('/')}/api/devices"
    headers = {"secret": secret}
    return await safe_http_get(url, headers=headers)


async def get_device_recent(api_base_url: str, secret: str, device_id: str) -> Optional[Dict[str, Any]]:
    """
    获取设备最近应用切换记录

    Args:
        api_base_url: API 基础地址
        secret: API 密钥
        device_id: 设备标识符

    Returns:
        包含 recent 和 count 字段的字典，或失败时返回 None
    """
    url = f"{api_base_url.rstrip('/')}/api/recent/{device_id}"
    headers = {"secret": secret}
    return await safe_http_get(url, headers=headers)


async def get_device_stats(api_base_url: str, secret: str, device_id: str, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    获取设备单日使用统计

    Args:
        api_base_url: API 基础地址
        secret: API 密钥
        device_id: 设备标识符
        date: 日期（YYYY-MM-DD），默认为当天

    Returns:
        统计字典，或失败时返回 None
    """
    url = f"{api_base_url.rstrip('/')}/api/stats/{device_id}"
    if date:
        url += f"?date={date}"
    headers = {"secret": secret}
    return await safe_http_get(url, headers=headers)


async def get_weekly_stats(api_base_url: str, secret: str, device_id: str, week_offset: int = 0, app_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    获取设备周维度统计

    Args:
        api_base_url: API 基础地址
        secret: API 密钥
        device_id: 设备标识符
        week_offset: 周偏移（0=本周，-1=上周，-2=上上周）
        app_name: 应用名称（可选）

    Returns:
        统计字典，或失败时返回 None
    """
    url = f"{api_base_url.rstrip('/')}/api/weekly/{device_id}?weekOffset={week_offset}"
    if app_name:
        url += f"&appName={app_name}"
    headers = {"secret": secret}
    return await safe_http_get(url, headers=headers)


async def get_ai_summary(api_base_url: str, secret: str, device_id: str) -> Optional[Dict[str, Any]]:
    """
    获取设备 AI 使用总结

    Args:
        api_base_url: API 基础地址
        secret: API 密钥
        device_id: 设备标识符

    Returns:
        AI 总结字典，或失败时返回 None
    """
    url = f"{api_base_url.rstrip('/')}/api/ai/summary/{device_id}"
    headers = {"secret": secret}
    return await safe_http_get(url, headers=headers)


async def get_ai_summaries(api_base_url: str, secret: str) -> Optional[Dict[str, Any]]:
    """
    获取所有设备的 AI 总结

    Args:
        api_base_url: API 基础地址
        secret: API 密钥

    Returns:
        AI 总结字典，或失败时返回 None
    """
    url = f"{api_base_url.rstrip('/')}/api/ai/summaries"
    headers = {"secret": secret}
    return await safe_http_get(url, headers=headers)


def format_devices_list(devices: List[Dict[str, Any]]) -> str:
    """格式化设备列表为易读字符串"""
    if not devices:
        return "暂无设备信息"

    lines = []
    for i, device in enumerate(devices, 1):
        running_status = "运行中" if device.get("running") else "未运行"
        battery = device.get("batteryLevel", "未知")
        is_charging = "🔌 充电中" if device.get("isCharging") else ""
        current_app = device.get("currentApp", "未知")

        lines.append(f"{i}. {device.get('device', '未知设备')}")
        lines.append(f"   当前应用: {current_app} ({running_status})")
        lines.append(f"   电池: {battery}% {is_charging}")

    return "\n".join(lines)


def format_recent_records(data: Dict[str, Any], device_id: str) -> str:
    """格式化最近记录为易读字符串"""
    if not data.get("success"):
        return f"获取 {device_id} 的最近记录失败"

    records = data.get("data", [])
    count = data.get("count", 0)

    if not records:
        return f"{device_id} 暂无最近记录"

    lines = [f"📱 {device_id} 最近 {count} 条应用切换记录：\n"]
    for i, record in enumerate(records[:10], 1):
        app_name = record.get("appName", "未知")
        timestamp = record.get("timestamp", "")
        running = "运行中" if record.get("running") else "已关闭"

        if timestamp:
            try:
                dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%m-%d %H:%M")
            except Exception:
                time_str = timestamp[:16]
        else:
            time_str = "未知"

        lines.append(f"{i}. {app_name} - {time_str} ({running})")

    if count > 10:
        lines.append(f"\n... 还有 {count - 10} 条记录")

    return "\n".join(lines)


def format_stats(data: Dict[str, Any], device_id: str, date: str) -> str:
    """格式化单日统计为易读字符串"""
    if not data:
        return f"获取 {device_id} 在 {date} 的统计失败"

    total_minutes = data.get("total", 0)
    hours = total_minutes // 60
    minutes = total_minutes % 60

    lines = [f"📊 {device_id} 在 {date} 的使用统计："]
    lines.append(f"总使用时长: {hours}小时{minutes}分钟\n")

    apps = data.get("apps", {})
    if apps:
        lines.append("📱 各应用使用时长：")
        sorted_apps = sorted(apps.items(), key=lambda x: x[1], reverse=True)
        for app_name, minutes in sorted_apps[:5]:
            h = minutes // 60
            m = minutes % 60
            lines.append(f"  • {app_name}: {h}小时{m}分钟" if h > 0 else f"  • {app_name}: {m}分钟")

    return "\n".join(lines)


def format_weekly_stats(data: Dict[str, Any], device_id: str, week_offset: int) -> str:
    """格式化周统计为易读字符串"""
    if not data:
        return f"获取 {device_id} 的周统计失败"

    week_range = data.get("weekRange", {})
    start = week_range.get("start", "")
    end = week_range.get("end", "")

    week_label = "本周" if week_offset == 0 else f"上周" if week_offset == -1 else f"{abs(week_offset)}周前"

    lines = [f"📅 {device_id} {week_label}（{start} 至 {end}）的统计：\n"]

    daily_totals = data.get("dailyTotals", {})
    if daily_totals:
        lines.append("每日总使用时长：")
        sorted_days = sorted(daily_totals.items())
        for day, minutes in sorted_days:
            h = minutes // 60
            m = minutes % 60
            day_short = day[5:] if len(day) > 5 else day
            lines.append(f"  • {day_short}: {h}小时{m}分钟" if h > 0 else f"  • {day_short}: {m}分钟")

    return "\n".join(lines)


def format_ai_summary(data: Dict[str, Any], device_id: str) -> str:
    """格式化 AI 总结为易读字符串"""
    if not data or not data.get("success"):
        return f"获取 {device_id} 的 AI 总结失败"

    summary = data.get("summary", "暂无总结")
    timestamp = data.get("timestamp", "")
    date_range = data.get("dateRange", {})

    if timestamp:
        try:
            dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            time_str = timestamp
    else:
        time_str = "未知"

    range_start = date_range.get("start", "")
    range_end = date_range.get("end", "")

    lines = [f"🤖 {device_id} 的 AI 使用总结"]
    lines.append(f"📅 统计周期: {range_start} 至 {range_end}")
    lines.append(f"🕐 生成时间: {time_str}\n")
    lines.append(f"📝 总结内容：\n{summary}")

    return "\n".join(lines)