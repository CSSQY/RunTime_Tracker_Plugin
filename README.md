# RunTime Tracker MaiBot 插件

## 项目简介

RunTime Tracker MaiBot 插件是一个专为 MaiBot 设计的工具插件，用于查询用户的设备使用情况。当需要了解用户去向或设备使用状态时，MaiBot 可以通过此工具查看设备的当前状态、使用记录和统计数据。

本插件基于以下项目开发：
- [RunTime_Tracker](https://github.com/1812z/RunTime_Tracker) - 核心设备使用追踪系统
- [MaiBot](https://github.com/Mai-with-u/MaiBot) - 多平台智能体框架
- 本项目由AI生成

## 功能特点

- **设备状态查询**：获取所有设备的当前状态，包括运行中的应用、电池电量等
- **最近使用记录**：查询设备最近 30 条应用切换记录
- **使用统计**：获取设备单日使用时长统计
- **周统计分析**：获取设备一周内的使用情况分析
- **AI 总结**：获取设备使用情况的 AI 分析总结

## 设备信息

设备信息可在配置文件中自定义，默认配置为：
- 电脑
- 手机

## 安装方法

1. 将 `runtime_tracker_plugin` 目录复制到 MaiBot 的 `plugins` 目录中
2. 确保安装了必要的 Python 依赖：
   ```bash
   pip install aiohttp
   ```
3. 启动 MaiBot，插件会自动加载

## 使用说明

MaiBot 会在以下场景自动调用此工具：
- 当有人询问用户的去向时
- 当需要确认用户是否在线时
- 当需要了解用户的设备使用情况时

### 工具参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| query_type | string | 是 | 查询类型：devices(设备列表), recent(最近记录), stats(统计数据), weekly(周统计), ai_summary(AI总结) |
| device_id | string | 否 | 设备ID，可在配置文件中自定义，默认设备有：电脑、手机，不填则查询所有设备 |
| date | string | 否 | 日期，格式YYYY-MM-DD，查询stats时使用 |
| week_offset | integer | 否 | 周偏移，0=本周，-1=上周，查询weekly时使用 |
| app_name | string | 否 | 应用名称，查询weekly时可指定 |

### 示例调用

1. 查询所有设备状态：
   ```
   runtime_tracker_tool(query_type="devices")
   ```

2. 查询电脑的最近记录：
   ```
   runtime_tracker_tool(query_type="recent", device_id="电脑")
   ```

3. 查询手机的单日统计：
   ```
   runtime_tracker_tool(query_type="stats", device_id="手机", date="2026-03-11")
   ```

4. 查询设备周统计：
   ```
   runtime_tracker_tool(query_type="weekly", device_id="电脑", week_offset=0)
   ```

5. 查询设备 AI 总结：
   ```
   runtime_tracker_tool(query_type="ai_summary", device_id="手机")
   ```

## 插件结构

```
runtime_tracker_plugin/
├── _manifest.json    # 插件元数据
├── plugin.py         # 插件核心代码
└── config.toml       # 配置文件
```

## 配置选项

编辑 `config.toml` 文件可以修改以下配置：

```toml
# RunTime Tracker 插件配置

[api]
# API基础URL
base_url = "https://localhost.com"
# API访问令牌
token = "your_api_token_here"

[user]
# 默认用户名
default_username = "用户"

[devices]
# 设备数量
device_count = 2
# 设备名字列表
device_names = ["电脑", "手机"]
```

## 技术实现

- **异步请求**：使用 `aiohttp` 库进行异步 API 请求，提高性能
- **配置管理**：支持从配置文件读取设置，方便定制
- **格式化输出**：提供友好的格式化结果，便于阅读
- **错误处理**：完善的错误处理机制，确保工具稳定运行
- **符合规范**：完全符合 MaiBot 插件开发规范

## API 接口

插件使用以下 API 接口：

- `GET /api/devices` - 获取所有设备列表
- `GET /api/recent/:deviceId` - 查询设备最近记录
- `GET /api/stats/:deviceId` - 单日使用统计
- `GET /api/weekly/:deviceId` - 周维度统计
- `GET /api/ai/summary/:deviceId` - 获取设备最近 AI 总结

## 注意事项

- 确保网络连接正常，能够访问 API 服务器
- 插件依赖 `aiohttp` 库，请确保已安装
- 如需修改 API 地址，请编辑 `config.toml` 文件

## 许可证

MIT License

## 作者


CSSQY
