# GUGU黑名单插件

## 插件简介

GUGU黑名单插件是一个高优先级的消息拦截插件，提供用户黑名单和群聊黑名单功能。该插件会在其他插件之前拦截消息，确保黑名单中的用户和群聊无法与机器人进行任何交互。并且在消息发送前会拦截 AstrBot 的内部错误信息，向用户返回统一提示，避免暴露错误细节。

## 主要功能

### 🛡️ 高优先级拦截
- **优先级**: 1000 (最高优先级)
- **拦截范围**: 所有消息类型
- **拦截时机**: 在其他插件处理之前

### 👤 用户黑名单
- 拦截指定用户的所有消息
- 包括私聊和群聊中的消息
- 即使用户在非黑名单群聊中@机器人也会被拦截

### 👥 群聊黑名单
- 拦截指定群聊的所有消息
- 群聊内所有用户的消息都会被拦截
- 包括群聊中的@消息

### 📊 数据持久化
- 黑名单数据自动保存到JSON文件
- 支持插件重启后数据恢复
- 数据文件位置: `data/plugin_data/gugus/blacklist/`

### 🚫 错误信息拦截
- 在发送消息前的阶段拦截 AstrBot 错误输出（如 LLM 请求失败、插件调用异常等）
- 用户仅会看到统一提示（可配置）：默认 `⚠️ 系统繁忙，已拦截内部错误信息，请稍后重试。`
- 详细错误仍记录在服务端日志中，便于排查

## 命令系统

### 基本命令格式
```
/blacklist <子命令> [参数]
```

### 可用命令

#### 1. 添加到黑名单
```
/blacklist add <类型> <ID>
```
- **类型**: `user` (用户) 或 `group` (群聊)
- **示例**:
  - `/blacklist add user 123456789` - 将用户123456789加入黑名单
  - `/blacklist add group 987654321` - 将群聊987654321加入黑名单

#### 2. 从黑名单移除
```
/blacklist remove <类型> <ID>
```
- **示例**:
  - `/blacklist remove user 123456789` - 将用户123456789从黑名单移除
  - `/blacklist remove group 987654321` - 将群聊987654321从黑名单移除

#### 3. 查看黑名单
```
/blacklist list [类型]
```
- **类型**: `user` (用户) 或 `group` (群聊) 或 `all` (全部)
- **示例**:
  - `/blacklist list user` - 查看用户黑名单
  - `/blacklist list group` - 查看群聊黑名单
  - `/blacklist list all` - 查看所有黑名单

#### 4. 清空黑名单
```
/blacklist clear [类型]
```
- **类型**: `user` (用户) 或 `group` (群聊) 或 `all` (全部)
- **示例**:
  - `/blacklist clear user` - 清空用户黑名单
  - `/blacklist clear group` - 清空群聊黑名单
  - `/blacklist clear all` - 清空所有黑名单

#### 5. 显示帮助
```
/blacklist help
```

## 配置系统

### 配置文件
插件使用 `_conf_schema.json` 进行配置，支持以下参数：

#### 基本配置
- `plugin_name`: 插件名称
- `plugin_version`: 插件版本
- `plugin_description`: 插件描述
- `plugin_author`: 插件作者
- `plugin_priority`: 插件优先级 (1-9999)
- `plugin_enabled`: 是否启用插件

#### 功能配置
- `data_directory`: 数据文件存储目录
- `log_level`: 日志级别 (DEBUG, INFO, WARNING, ERROR)
- `auto_save`: 是否自动保存黑名单数据
- `backup_enabled`: 是否启用数据备份
- `backup_interval`: 备份间隔时间（秒）

#### 权限配置
- `admin_only`: 是否只允许管理员使用黑名单命令
- `max_blacklist_size`: 黑名单最大容量 (100-10000)

#### 拦截配置
- `intercept_private_chat`: 是否拦截私聊消息
- `intercept_group_chat`: 是否拦截群聊消息
- `show_interception_log`: 是否显示拦截日志
- `error_intercept_enabled`: 是否启用 AstrBot 错误信息拦截（默认 true）
- `error_intercept_message`: 拦截后返回给用户的提示文案（默认如上）

### 配置示例
```json
{
  "admin_only": {
    "type": "bool",
    "default": true,
    "description": "是否只允许管理员使用黑名单命令"
  },
  "max_blacklist_size": {
    "type": "int",
    "default": 1000,
    "min": 100,
    "max": 10000,
    "description": "黑名单最大容量"
  },
  "intercept_private_chat": {
    "type": "bool",
    "default": true,
    "description": "是否拦截私聊消息"
  },
  "intercept_group_chat": {
    "type": "bool",
    "default": true,
    "description": "是否拦截群聊消息"
  },
  "show_interception_log": {
    "type": "bool",
    "default": true,
    "description": "是否显示拦截日志"
  }
}
```

## 数据文件结构

### 用户黑名单文件: `data/plugin_data/gugus/blacklist/user_blacklist.json`
```json
{
  "users": [
    "123456789",
    "987654321"
  ],
  "updated_at": "2024-01-01T12:00:00"
}
```

### 群聊黑名单文件: `data/plugin_data/gugus/blacklist/group_blacklist.json`
```json
{
  "groups": [
    "111111111",
    "222222222"
  ],
  "updated_at": "2024-01-01T12:00:00"
}
```

## 工作原理

### 消息拦截流程
1. **接收消息** - 插件以最高优先级接收所有消息
2. **检查黑名单** - 检查发送者ID和群聊ID是否在黑名单中
3. **拦截决策**:
   - 如果在黑名单中 → 调用 `event.stop_event()` 停止事件传播
   - 如果不在黑名单中 → 跳过处理，让其他插件继续处理

### 拦截规则
- **用户黑名单**: 发送者ID在用户黑名单中 → 拦截
- **群聊黑名单**: 群聊ID在群聊黑名单中 → 拦截
- **优先级**: 用户黑名单 > 群聊黑名单

## 日志信息

插件会输出详细的日志信息，包括：
- 插件初始化状态
- 黑名单加载/保存状态
- 消息拦截记录
- 命令执行结果

### 日志示例
```
[INFO] [GUGU黑名单插件] 🚀 插件已初始化，用户黑名单: 2 个，群聊黑名单: 1 个
[INFO] [GUGU黑名单插件] 📥 已加载用户黑名单: 2 个用户
[INFO] [GUGU黑名单插件] 🚫 拦截黑名单用户消息: 123456789
[INFO] [GUGU黑名单插件] 🛑 已拦截黑名单消息，停止事件传播
```

## 安装和配置

### 1. 安装插件
将插件文件夹复制到AstrBot的插件目录中

### 2. 重启AstrBot
重启AstrBot以加载新插件

### 3. 验证安装
发送 `/blacklist help` 查看帮助信息

### 4. 添加黑名单
使用命令添加需要拦截的用户或群聊

## 注意事项

### ⚠️ 重要提醒
1. **高优先级**: 该插件优先级为1000，会在所有其他插件之前执行
2. **不可逆操作**: 清空黑名单操作不可撤销，请谨慎使用
3. **数据备份**: 建议定期备份黑名单数据文件
4. **权限控制**: 建议只给管理员开放黑名单管理权限
5. **错误拦截**: 统一提示只影响用户可见内容，不影响服务端日志与排查

### 🔧 故障排除
1. **插件未加载**: 检查插件文件夹名称和文件结构
2. **命令无响应**: 确认插件已正确加载并启用
3. **数据丢失**: 检查数据文件权限和磁盘空间
4. **拦截失效**: 确认插件优先级设置正确

## 更新日志

### v1.1.0 (2025-09-06)
- 新增：在发送前拦截 AstrBot 错误输出并返回统一提示（文案可配置）
- 变更：固定黑名单数据目录为 `data/plugin_data/gugus/blacklist/`

### v1.0.0 (2024-01-01)
- 初始版本发布
- 实现用户和群聊黑名单功能
- 支持高优先级消息拦截
- 提供完整的命令管理系统
- 实现数据持久化存储

## 技术支持

如有问题或建议，请联系插件作者。
