# RunTime Tracker Plugin

> 本项目由 AI 开发

一个对接 [RunTime Tracker](https://github.com/1812z/RunTime_Tracker) 后端 API 的 MaiBot 插件，用于查询设备使用时间统计。

## 功能特性

- **Command 组件**：用户通过命令主动查询
- **Tool 组件**：LLM 在生成回复时可根据上下文自主调用
- 支持多种查询：设备列表、最近记录、单日统计、周统计、AI 总结

## 安装

1. 将插件目录复制到 MaiBot 的 `plugins/` 目录下：

```
MaiBot/
└── plugins/
    └── Run_Time_Tracker_plugin/
        ├── _manifest.json
        ├── plugin.py
        └── utils.py
```

2. 重启 MaiBot

## 配置

插件首次运行后会自动生成 `config.toml` 配置文件，需要填写以下必填项：

```toml
[api]
base_url = "https://your-runtime-tracker-api.com/"  # API 地址
secret = "your-api-secret"                          # API 密钥
default_device = ""                                 # 默认设备名称（可选）
```

### 配置项说明

| 配置项 | 说明 | 必填 |
|--------|------|------|
| `api.base_url` | RunTime Tracker API 地址 | 是 |
| `api.secret` | API 请求密钥 | 是 |
| `api.default_device` | 默认设备名称，不填则每次需手动指定 | 否 |

## 使用方法

### Command 命令

| 命令 | 说明 |
|------|------|
| `/runtime` | 显示帮助信息 |
| `/runtime devices` | 查看所有设备列表 |
| `/runtime recent <设备名>` | 查看设备最近记录 |
| `/runtime stats <设备名> [日期]` | 查看设备单日统计 |
| `/runtime weekly <设备名> [周偏移]` | 查看设备周统计 |

**示例：**
```
/runtime devices                                    # 查看所有设备
/runtime recent 手机                               # 查看手机最近记录
/runtime stats 手机 2025-01-01                    # 查看手机 2025-01-01 的统计
/runtime weekly 手机                              # 查看手机本周统计
/runtime weekly 手机 -1                           # 查看手机上週统计
```

### Tool 工具（LLM 自动调用）

LLM 在以下场景会自动调用相应工具：

| 工具名称 | 说明 | 参数 |
|----------|------|------|
| `get_device_list` | 获取所有设备列表 | 无 |
| `get_device_recent` | 获取设备最近记录 | `device_id` |
| `get_device_stats` | 获取设备单日统计 | `device_id`, `date`(可选) |
| `get_weekly_stats` | 获取设备周统计 | `device_id`, `week_offset`(可选) |
| `get_ai_summary` | 获取 AI 使用总结 | `device_id` |

## 依赖

- Python 3.10+
- [MaiBot](https://github.com/Mai-with-u/MaiBot) >= 0.8.0
- `aiohttp` (插件已声明依赖，会自动安装)

## API 文档

插件对接的 API 文档请参考：[RunTime Tracker API](https://github.com/1812z/RunTime_Tracker/wiki/API)

## 许可证

MIT
