# -*- coding: utf-8 -*-

"""
GUGU黑名单插件
提供用户黑名单和群聊黑名单功能，高优先级拦截黑名单消息
"""

import json
import os
import logging
import re
from typing import List, Optional, Set
from datetime import datetime

from astrbot.api.event import filter, AstrMessageEvent, MessageChain
import astrbot.core.message.components as Comp
from astrbot.core.star import Star

# 插件名称
PLUGIN_NAME = "GUGU黑名单插件"

# 获取日志记录器
logger = logging.getLogger(__name__)


class GUGUBlacklistPlugin(Star):
    """GUGU黑名单插件主类"""
    
    def __init__(self, context=None, config=None):
        super().__init__(context=context, config=config)
        
        # 获取配置
        self.config = config or {}
        
        # 数据文件路径（固定新路径，不再自动迁移）
        self.data_dir = "data/plugin_data/gugus/blacklist"
        self.user_blacklist_file = os.path.join(self.data_dir, "user_blacklist.json")
        self.group_blacklist_file = os.path.join(self.data_dir, "group_blacklist.json")
        
        # 黑名单数据
        self.user_blacklist: Set[str] = set()
        self.group_blacklist: Set[str] = set()
        
        # 配置参数
        self.admin_only = self.config.get("admin_only", True)
        self.max_blacklist_size = self.config.get("max_blacklist_size", 1000)
        self.intercept_private_chat = self.config.get("intercept_private_chat", True)
        self.intercept_group_chat = self.config.get("intercept_group_chat", True)
        self.show_interception_log = self.config.get("show_interception_log", True)
        self.error_intercept_enabled = self.config.get("error_intercept_enabled", True)
        self.error_intercept_message = self.config.get(
            "error_intercept_message",
            "⚠️ 系统繁忙，已拦截内部错误信息，请稍后重试。",
        )
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)

        # 加载黑名单数据
        self._load_blacklists()
        
        logger.info(f"[{PLUGIN_NAME}] 🚀 插件已初始化，用户黑名单: {len(self.user_blacklist)} 个，群聊黑名单: {len(self.group_blacklist)} 个")

    def _load_blacklists(self):
        """加载黑名单数据"""
        try:
            # 加载用户黑名单
            if os.path.exists(self.user_blacklist_file):
                with open(self.user_blacklist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.user_blacklist = set(data.get('users', []))
                logger.info(f"[{PLUGIN_NAME}] 📥 已加载用户黑名单: {len(self.user_blacklist)} 个用户")
            else:
                # 创建默认用户黑名单文件
                self._save_user_blacklist()
                logger.info(f"[{PLUGIN_NAME}] 📝 已创建默认用户黑名单文件")
            
            # 加载群聊黑名单
            if os.path.exists(self.group_blacklist_file):
                with open(self.group_blacklist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.group_blacklist = set(data.get('groups', []))
                logger.info(f"[{PLUGIN_NAME}] 📥 已加载群聊黑名单: {len(self.group_blacklist)} 个群聊")
            else:
                # 创建默认群聊黑名单文件
                self._save_group_blacklist()
                logger.info(f"[{PLUGIN_NAME}] 📝 已创建默认群聊黑名单文件")
                
        except Exception as e:
            logger.error(f"[{PLUGIN_NAME}] 💥 加载黑名单数据失败: {e}")
            # 初始化空黑名单
            self.user_blacklist = set()
            self.group_blacklist = set()

    def _save_user_blacklist(self):
        """保存用户黑名单"""
        try:
            data = {
                'users': list(self.user_blacklist),
                'updated_at': datetime.now().isoformat()
            }
            with open(self.user_blacklist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"[{PLUGIN_NAME}] 💾 用户黑名单已保存: {len(self.user_blacklist)} 个用户")
        except Exception as e:
            logger.error(f"[{PLUGIN_NAME}] 💥 保存用户黑名单失败: {e}")

    def _save_group_blacklist(self):
        """保存群聊黑名单"""
        try:
            data = {
                'groups': list(self.group_blacklist),
                'updated_at': datetime.now().isoformat()
            }
            with open(self.group_blacklist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"[{PLUGIN_NAME}] 💾 群聊黑名单已保存: {len(self.group_blacklist)} 个群聊")
        except Exception as e:
            logger.error(f"[{PLUGIN_NAME}] 💥 保存群聊黑名单失败: {e}")

    def _get_sender_id(self, event: AstrMessageEvent) -> str:
        """获取发送者ID"""
        try:
            return event.get_sender_id()
        except:
            return ""

    def _get_group_id(self, event: AstrMessageEvent) -> Optional[str]:
        """获取群聊ID"""
        try:
            return event.get_group_id()
        except:
            return None

    def _is_private_chat(self, event: AstrMessageEvent) -> bool:
        """判断是否为私聊"""
        try:
            return event.is_private_chat()
        except:
            return False

    def _is_blacklisted(self, event: AstrMessageEvent) -> bool:
        """检查是否在黑名单中"""
        try:
            sender_id = self._get_sender_id(event)
            group_id = self._get_group_id(event)
            is_private = self._is_private_chat(event)
            
            # 检查是否应该拦截此类型消息
            if is_private and not self.intercept_private_chat:
                return False
            
            if not is_private and not self.intercept_group_chat:
                return False
            
            # 检查发送者是否在用户黑名单中
            if sender_id in self.user_blacklist:
                if self.show_interception_log:
                    logger.info(f"[{PLUGIN_NAME}] 🚫 拦截黑名单用户消息: {sender_id}")
                return True
            
            # 如果是群聊，检查群聊是否在黑名单中
            if not is_private and group_id:
                if group_id in self.group_blacklist:
                    if self.show_interception_log:
                        logger.info(f"[{PLUGIN_NAME}] 🚫 拦截黑名单群聊消息: {group_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"[{PLUGIN_NAME}] 💥 检查黑名单状态失败: {e}")
            return False

    @filter.event_message_type(filter.EventMessageType.ALL, priority=1000)
    async def intercept_all_messages(self, event: AstrMessageEvent):
        """拦截所有消息，检查黑名单状态"""
        try:
            # 检查是否在黑名单中
            if self._is_blacklisted(event):
                # 拦截消息，不进行任何处理
                event.stop_event()
                logger.info(f"[{PLUGIN_NAME}] 🛑 已拦截黑名单消息，停止事件传播")
                return
            
            # 不在黑名单中，跳过此插件
            logger.debug(f"[{PLUGIN_NAME}] ✅ 消息不在黑名单中，跳过处理")
            
        except Exception as e:
            logger.exception(f"[{PLUGIN_NAME}] 💥 消息拦截处理异常: {e}")

    @filter.on_decorating_result(priority=1000)
    async def intercept_astrbot_error_messages(self, event: AstrMessageEvent):
        """拦截 AstrBot 内部错误信息，向用户发送统一提示"""
        try:
            if not self.error_intercept_enabled:
                return
            result = event.get_result()
            if result is None or not getattr(result, "chain", None):
                return

            # 聚合纯文本内容
            combined_text = ""
            for comp in result.chain:
                if isinstance(comp, Comp.Plain):
                    combined_text += comp.text + "\n"

            if not combined_text:
                return

            patterns = [
                r"AstrBot 请求失败",
                r"在调用插件 .+? 时出现异常",
                r"错误类型[:：].*?错误信息[:：]",
                r"Traceback \\(most recent call last\\)",
                r"请求失败[:：]",
            ]

            if any(re.search(p, combined_text, re.S | re.I) for p in patterns):
                tip_text = self.error_intercept_message or "⚠️ 系统繁忙，已拦截内部错误信息，请稍后重试。"
                result.chain = [Comp.Plain(tip_text)]
                if self.show_interception_log:
                    logger.info(f"[{PLUGIN_NAME}] 🔒 已拦截 AstrBot 错误输出，并替换为用户提示。")

        except Exception as e:
            logger.error(f"[{PLUGIN_NAME}] 💥 错误拦截处理异常: {e}")

    @filter.command("blacklist", priority=1000)
    async def blacklist_commands(self, event: AstrMessageEvent):
        """黑名单管理命令"""
        try:
            # 检查管理员权限
            if self.admin_only and not event.is_admin():
                await event.send(MessageChain([Comp.Plain("❌ 只有管理员才能使用黑名单命令")]))
                return
            
            command = event.message_str.strip()
            args = command.split()
            
            if len(args) < 2:
                await self._show_help(event)
                return
            
            subcommand = args[1].lower()
            
            if subcommand == "add":
                await self._add_to_blacklist(event, args[2:])
            elif subcommand == "remove":
                await self._remove_from_blacklist(event, args[2:])
            elif subcommand == "list":
                await self._list_blacklist(event, args[2:])
            elif subcommand == "clear":
                await self._clear_blacklist(event, args[2:])
            elif subcommand == "help":
                await self._show_help(event)
            else:
                await self._show_help(event)
                
        except Exception as e:
            logger.exception(f"[{PLUGIN_NAME}] 💥 黑名单命令处理异常: {e}")
            await event.send(MessageChain([Comp.Plain(f"❌ 命令执行失败: {e}")]))

    async def _show_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        help_text = f"""
🛡️ {PLUGIN_NAME} 帮助信息

📋 命令格式: /blacklist <子命令> [参数]

🔧 子命令:
  add <类型> <ID>     - 添加到黑名单
   类型: user(用户) 或 group(群聊)
   示例: /blacklist add user 123456789
        /blacklist add group 987654321

  remove <类型> <ID>  - 从黑名单移除
   示例: /blacklist remove user 123456789

  list [类型]         - 查看黑名单
   类型: user(用户) 或 group(群聊) 或 all(全部)
   示例: /blacklist list all

  clear [类型]        - 清空黑名单
   类型: user(用户) 或 group(群聊) 或 all(全部)
   示例: /blacklist clear all

  help                - 显示此帮助信息

📊 当前状态:
   用户黑名单: {len(self.user_blacklist)}/{self.max_blacklist_size} 个
   群聊黑名单: {len(self.group_blacklist)}/{self.max_blacklist_size} 个
   管理员权限: {'是' if self.admin_only else '否'}
   拦截私聊: {'是' if self.intercept_private_chat else '否'}
   拦截群聊: {'是' if self.intercept_group_chat else '否'}
   显示拦截日志: {'是' if self.show_interception_log else '否'}
"""
        await event.send(MessageChain([Comp.Plain(help_text.strip())]))

    async def _add_to_blacklist(self, event: AstrMessageEvent, args: List[str]):
        """添加到黑名单"""
        if len(args) < 2:
            await event.send(MessageChain([Comp.Plain("❌ 参数不足，格式: /blacklist add <类型> <ID>")]))
            return
        
        blacklist_type = args[0].lower()
        target_id = args[1]
        
        if blacklist_type == "user":
            if target_id in self.user_blacklist:
                await event.send(MessageChain([Comp.Plain(f"⚠️ 用户 {target_id} 已在黑名单中")]))
            else:
                # 检查容量限制
                if len(self.user_blacklist) >= self.max_blacklist_size:
                    await event.send(MessageChain([Comp.Plain(f"❌ 用户黑名单已达到最大容量 {self.max_blacklist_size}")]))
                    return
                
                self.user_blacklist.add(target_id)
                self._save_user_blacklist()
                await event.send(MessageChain([Comp.Plain(f"✅ 已将用户 {target_id} 添加到黑名单")]))
                
        elif blacklist_type == "group":
            if target_id in self.group_blacklist:
                await event.send(MessageChain([Comp.Plain(f"⚠️ 群聊 {target_id} 已在黑名单中")]))
            else:
                # 检查容量限制
                if len(self.group_blacklist) >= self.max_blacklist_size:
                    await event.send(MessageChain([Comp.Plain(f"❌ 群聊黑名单已达到最大容量 {self.max_blacklist_size}")]))
                    return
                
                self.group_blacklist.add(target_id)
                self._save_group_blacklist()
                await event.send(MessageChain([Comp.Plain(f"✅ 已将群聊 {target_id} 添加到黑名单")]))
                
        else:
            await event.send(MessageChain([Comp.Plain("❌ 无效的类型，请使用 user 或 group")]))

    async def _remove_from_blacklist(self, event: AstrMessageEvent, args: List[str]):
        """从黑名单移除"""
        if len(args) < 2:
            await event.send(MessageChain([Comp.Plain("❌ 参数不足，格式: /blacklist remove <类型> <ID>")]))
            return
        
        blacklist_type = args[0].lower()
        target_id = args[1]
        
        if blacklist_type == "user":
            if target_id in self.user_blacklist:
                self.user_blacklist.remove(target_id)
                self._save_user_blacklist()
                await event.send(MessageChain([Comp.Plain(f"✅ 已将用户 {target_id} 从黑名单移除")]))
            else:
                await event.send(MessageChain([Comp.Plain(f"⚠️ 用户 {target_id} 不在黑名单中")]))
                
        elif blacklist_type == "group":
            if target_id in self.group_blacklist:
                self.group_blacklist.remove(target_id)
                self._save_group_blacklist()
                await event.send(MessageChain([Comp.Plain(f"✅ 已将群聊 {target_id} 从黑名单移除")]))
            else:
                await event.send(MessageChain([Comp.Plain(f"⚠️ 群聊 {target_id} 不在黑名单中")]))
                
        else:
            await event.send(MessageChain([Comp.Plain("❌ 无效的类型，请使用 user 或 group")]))

    async def _list_blacklist(self, event: AstrMessageEvent, args: List[str]):
        """查看黑名单"""
        if not args:
            blacklist_type = "all"
        else:
            blacklist_type = args[0].lower()
        
        if blacklist_type == "user":
            if self.user_blacklist:
                user_list = "\n".join(sorted(self.user_blacklist))
                await event.send(MessageChain([Comp.Plain(f"📋 用户黑名单 ({len(self.user_blacklist)} 个):\n{user_list}")]))
            else:
                await event.send(MessageChain([Comp.Plain("📋 用户黑名单为空")]))
                
        elif blacklist_type == "group":
            if self.group_blacklist:
                group_list = "\n".join(sorted(self.group_blacklist))
                await event.send(MessageChain([Comp.Plain(f"📋 群聊黑名单 ({len(self.group_blacklist)} 个):\n{group_list}")]))
            else:
                await event.send(MessageChain([Comp.Plain("📋 群聊黑名单为空")]))
                
        elif blacklist_type == "all":
            result = f"📊 黑名单统计:\n"
            result += f"👤 用户黑名单: {len(self.user_blacklist)} 个\n"
            result += f"👥 群聊黑名单: {len(self.group_blacklist)} 个\n"
            
            if self.user_blacklist:
                result += f"\n👤 用户列表:\n" + "\n".join(sorted(self.user_blacklist)) + "\n"
            
            if self.group_blacklist:
                result += f"\n👥 群聊列表:\n" + "\n".join(sorted(self.group_blacklist))
            
            await event.send(MessageChain([Comp.Plain(result)]))
            
        else:
            await event.send(MessageChain([Comp.Plain("❌ 无效的类型，请使用 user、group 或 all")]))

    async def _clear_blacklist(self, event: AstrMessageEvent, args: List[str]):
        """清空黑名单"""
        if not args:
            blacklist_type = "all"
        else:
            blacklist_type = args[0].lower()
        
        if blacklist_type == "user":
            count = len(self.user_blacklist)
            self.user_blacklist.clear()
            self._save_user_blacklist()
            await event.send(MessageChain([Comp.Plain(f"🗑️ 已清空用户黑名单，移除了 {count} 个用户")]))
            
        elif blacklist_type == "group":
            count = len(self.group_blacklist)
            self.group_blacklist.clear()
            self._save_group_blacklist()
            await event.send(MessageChain([Comp.Plain(f"🗑️ 已清空群聊黑名单，移除了 {count} 个群聊")]))
            
        elif blacklist_type == "all":
            user_count = len(self.user_blacklist)
            group_count = len(self.group_blacklist)
            self.user_blacklist.clear()
            self.group_blacklist.clear()
            self._save_user_blacklist()
            self._save_group_blacklist()
            await event.send(MessageChain([Comp.Plain(f"🗑️ 已清空所有黑名单，移除了 {user_count} 个用户和 {group_count} 个群聊")]))
            
        else:
            await event.send(MessageChain([Comp.Plain("❌ 无效的类型，请使用 user、group 或 all")]))

    async def on_enable(self):
        """插件启用时调用"""
        logger.info(f"[{PLUGIN_NAME}] 🎉 插件已启用")
        
    async def on_disable(self):
        """插件禁用时调用"""
        logger.info(f"[{PLUGIN_NAME}] 🛑 插件已禁用")
