# RunTime Tracker Plugin

> 本项目由 AI 辅助开发
> 版本: 1.2.0-pre

> **⚠️ 重要提示**：v1.2.0 起插件已迁移至 MaiBot 新版 Plugin SDK v2，**不再兼容** MaiBot < 1.0.0 及旧版插件系统。如仍使用旧版 MaiBot，请继续使用 [v1.1.0](https://github.com/CSSQY/RunTime_Tracker_Plugin/releases/tag/v1.1.0)。

## 项目介绍
本项目是一个对接 [1812z](https://github.com/1812z/) 的 [RunTime Tracker](https://github.com/1812z/RunTime_Tracker) 后端的 [MaiBot](https://github.com/Mai-with-u/MaiBot) 插件，用于查询设备使用时间统计。

使用本插件前，请先自行部署上述后端服务。

## 功能特性

- **Command 组件**：用户通过命令主动查询
- **Tool 组件**：LLM 在生成回复时可根据上下文自主调用
- 支持多种查询：设备列表、最近记录、单日统计、周统计、AI 总结
- 智能参数识别：日期格式参数自动识别为日期，否则识别为设备名
- 管理员权限控制：可配置仅允许指定用户使用命令

## 安装

1. 将插件目录复制到 MaiBot 的 `plugins/` 目录下：

```
MaiBot/
└── plugins/
    └── RunTime_Tracker_Plugin/
        ├── _manifest.json
        ├── plugin.py
        ├── utils.py
        └── config.toml
```

2. 重启 MaiBot

## 配置

编辑 `config.toml` 配置文件：

```toml
[plugin]
enabled = true
config_version = "1.2.0"

[api]
base_url = "https://your-runtime-tracker-api.com"   # API 地址（不要以 /api/ 结尾）
secret = "your-api-secret"                           # API 密钥
default_device = ""                                   # 默认设备名称（可选）

[security]
admin_only = false                                   # 是否仅允许管理员使用指令
admin_users = "10001,10002"                          # 管理员用户ID列表
```

### 配置项说明

| 配置项 | 说明 | 必填 |
|--------|------|------|
| `api.base_url` | RunTime Tracker API 地址，不含 `/api/` 后缀 | 是 |
| `api.secret` | API 请求密钥 | 是 |
| `api.default_device` | 默认设备名称，设置了可简化命令 | 否 |
| `security.admin_only` | 是否仅允许管理员使用指令 | 否 |
| `security.admin_users` | 管理员用户ID列表，多个用逗号分隔 | 否 |

## 使用方法

### Command 命令

| 命令 | 说明 |
|------|------|
| `/runtime` | 显示帮助信息 |
| `/runtime devices` | 查看所有设备列表 |
| `/runtime recent <设备名>` | 查看设备最近记录 |
| `/runtime stats [设备名] [日期]` | 查看设备单日统计 |
| `/runtime weekly [设备名] [周偏移]` | 查看设备周统计 |

**示例：**
```
/runtime devices                              # 查看所有设备
/runtime recent 手机                          # 查看手机最近记录
/runtime stats 手机 2025-01-01                # 查看手机指定日期统计
/runtime stats 2025-01-01                     # 使用默认设备查看指定日期统计
/runtime stats 手机                           # 查看手机今日统计
/runtime weekly 手机                          # 查看手机本周统计
/runtime weekly 手机 -1                       # 查看手机上週统计
```

**提示**：参数会自动识别为日期（YYYY-MM-DD格式）或设备名。如果只输入日期且配置了默认设备，将自动使用默认设备。

### Tool 工具（LLM 自动调用）

LLM 在以下场景会自动调用相应工具：

| 工具名称 | 说明 | 参数 |
|----------|------|------|
| `get_device_list` | 获取所有设备列表 | 无 |
| `get_device_recent` | 获取设备最近记录 | `device_id` |
| `get_device_stats` | 获取设备单日统计 | `device_id`, `date`(可选) |
| `get_weekly_stats` | 获取设备周统计 | `device_id`, `week_offset`(可选) |
| `get_ai_summary` | 获取 AI 使用总结 | `device_id` |

## 变更记录

### v1.2.0-pre

> **破坏性变更**：不再兼容 MaiBot < 1.0.0。

- **SDK 迁移**：从旧版 `src.plugin_system` 迁移至 `maibot_sdk` v2
- **Manifest 升级**：`_manifest.json` 升级为 Manifest v2 格式，新增 `urls`、`sdk`、`i18n`、`capabilities` 字段
- **组件声明**：`BaseCommand` / `BaseTool` 独立类改为 `@Command` / `@Tool` 装饰器
- **配置读取**：从 `self.get_config()` 改为 SDK Capability 机制 (`config.get_plugin` + `send.text`)
- **生命周期**：新增 `on_load()`、`on_unload()`、`on_config_update()` 必须实现的钩子方法
- **鉴权适配**：管理员用户 ID 提取适配新版 SDK 消息结构
- **配置路径**：`base_url` 不再包含 `/api/` 后缀（插件自动拼接）

### 升级指南

从 v1.1.0 升级到 v1.2.0-pre：

1. 确保 MaiBot >= 1.0.0，且已安装 `maibot-plugin-sdk` >= 2.0.0
2. 删除旧的 `config.toml`，使用新版模板重新配置
3. `api.base_url` 值中移除 `/api/` 后缀（如 `https://api.example.com/api/` → `https://api.example.com`）
4. 重启 MaiBot

### v1.1.0 (2026-04-16)
- **Bug 修复**：修复单日统计查询返回 0 的问题（API 字段名实际为 `totalUsage` 和 `appStats`）；修复周统计小数点过长问题（添加 `round()` 四舍五入）；修复参数为空时指令报错（args 可能为 None，添加空值处理）；修复日期参数 URL 编码问题（添加 `urllib.parse.quote()` 处理中文设备名）
- **新功能**：智能参数识别（`/runtime stats` 支持只输入日期自动使用默认设备）；管理员权限控制（新增 `security.admin_only` 和 `security.admin_users` 配置项）；WebUI 配置集成（所有配置项添加 `placeholder`、`hint`、`depends_on` 等属性）
- **文档更新**：添加版本号标识；新增智能参数识别功能说明；更新使用示例；更新 `_manifest.json` 作者信息和仓库地址

## 依赖

- Python 3.10+
- [MaiBot](https://github.com/Mai-with-u/MaiBot) >= 1.0.0
- [maibot-plugin-sdk](https://pypi.org/project/maibot-plugin-sdk/) >= 2.0.0
- `aiohttp`

## API 文档

插件对接的 API 文档请参考：[RunTime Tracker API](https://github.com/1812z/RunTime_Tracker/wiki/API)

## 许可证

MIT