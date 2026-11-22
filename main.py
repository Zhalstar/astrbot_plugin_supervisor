from astrbot.api.event import filter
from astrbot.api.star import Context, Star
from astrbot.core import AstrBotConfig
from astrbot.core.platform import AstrMessageEvent
from astrbot.core.star.filter.event_message_type import EventMessageType

from .core.config import PluginConfig
from .core.service import SupervisorService
from .core.supervisor import SupervisorManager
from .core.utils import get_ats, get_nickname


class SupervisorPlugin(Star):
    """Expose supervisor service behavior through AstrBot commands and events."""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.cfg = PluginConfig(config)
        self.supervisor_mgr = SupervisorManager(self.cfg)
        self.service = SupervisorService(context, self.cfg, self.supervisor_mgr)

    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def on_supervisor(self, event: AstrMessageEvent):
        """监听群消息，执行监督逻辑"""
        if chain := await self.service.supervise(event):
            yield event.chain_result(chain)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("监督")
    async def add_supervisor(self, event: AstrMessageEvent):
        """监督 @用户 [分钟]，添加监督对象并设置时长"""
        at_ids = get_ats(event, noself=True)
        if not at_ids:
            yield event.plain_result("请 @ 要监督的对象")
            return

        parts = event.message_str.split()
        minute = int(parts[-1]) if parts and parts[-1].isdigit() else None
        effective_minute = self.supervisor_mgr.add_supervisors(at_ids, minute)
        nicknames = [await get_nickname(event, user_id) for user_id in at_ids]
        yield event.plain_result(
            f"已监督：{'、'.join(nicknames)}({effective_minute}分钟)"
        )

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("解除监督")
    async def remove_supervisor(self, event: AstrMessageEvent):
        """解除监督 @用户"""
        at_ids = get_ats(event, noself=True)
        if not at_ids:
            yield event.plain_result("请 @ 要解除监督的对象")
            return

        self.supervisor_mgr.remove_supervisors(at_ids)
        nicknames = [await get_nickname(event, user_id) for user_id in at_ids]
        yield event.plain_result(f"已解除监督：{'、'.join(nicknames)}")

    @filter.command("监督列表")
    async def list_supervisors(self, event: AstrMessageEvent):
        """查看监督对象及剩余时长。"""
        supervisors = self.supervisor_mgr.list_supervisors()
        if not supervisors:
            yield event.plain_result("当前没有正在监督的对象")
            return

        lines = []
        for user_id, remain in supervisors.items():
            nickname = await get_nickname(event, user_id)
            duration = "长期" if remain is None else f"剩余{remain}分钟"
            lines.append(f"{nickname}（{duration}）")
        yield event.plain_result("监督中：\n" + "\n".join(lines))
