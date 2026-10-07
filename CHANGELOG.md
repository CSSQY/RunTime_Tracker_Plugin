# Changelog

本文件记录 `CSSQY.RunTime_Tracker_Plugin` 的版本变更。每版分为**主要功能**（用户可感知的新能力）与**细节**（修复、行为调整、插件 SDK / API 适配）两部分，一条一行。

## [1.2.1]

### 主要功能

- 配置模型化：新增 `config_model`（基于 SDK `PluginConfigBase`），配置改由 `self.config` 强类型读取，并在 WebUI 插件配置页生成中文表单（标签 / 说明 / 占位符，API 密钥以密码框显示）。

### 细节

- SDK 适配：移除 `config.get_plugin` 能力调用（配置改由 Runner 本地注入），`_manifest.json` 的 `capabilities` 收敛为 `send.text`。
- 兼容范围：`_manifest.json` 的 `host_application` 调整为 `1.3.0 ~ 1.3.99`、`sdk` 调整为 `2.9.0 ~ 2.99.99`；`config.toml` 与 README 的 `config_version` 同步为 `1.2.1`。
- 文档：新增独立 CHANGELOG.md（自 1.2.0 起），README 变更记录改为指向本文件。

## [1.2.0]

> **破坏性变更**：不再兼容 MaiBot < 1.0.0。

### 主要功能

- SDK 迁移：从旧版 `src.plugin_system` 迁移至 `maibot_sdk` v2。
- Manifest 升级：`_manifest.json` 升级为 Manifest v2 格式，新增 `urls`、`sdk`、`i18n`、`capabilities` 字段。
- 组件声明：`BaseCommand` / `BaseTool` 独立类改为 `@Command` / `@Tool` 装饰器。
- 生命周期：新增 `on_load()`、`on_unload()`、`on_config_update()` 必须实现的钩子方法。

### 细节

- 配置读取：从 `self.get_config()` 改为 SDK Capability 机制（`config.get_plugin` + `send.text`）。
- 鉴权适配：管理员用户 ID 提取适配新版 SDK 消息结构。
- 配置路径：`api.base_url` 不再包含 `/api/` 后缀（插件自动拼接）。

### 升级指南

从 v1.1.0 升级到 v1.2.0：

1. 确保 MaiBot >= 1.0.0，且已安装 `maibot-plugin-sdk` >= 2.0.0
2. 删除旧的 `config.toml`，使用新版模板重新配置
3. `api.base_url` 值中移除 `/api/` 后缀（如 `https://api.example.com/api/` → `https://api.example.com`）
4. 重启 MaiBot
