import random

from astrbot.api import logger
from astrbot.api.star import Context
from astrbot.core.message.components import At, BaseMessageComponent, Image, Plain
from astrbot.core.platform import AstrMessageEvent
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

from .config import PluginConfig
from .model import SupervisorModel
from .supervisor import SupervisorManager


class SupervisorService:
    """Select and execute weighted reactions for supervised messages."""

    def __init__(
        self,
        context: Context,
        config: PluginConfig,
        supervisor_manager: SupervisorManager,
    ):
        self.context = context
        self.config = config
        self.supervisor_mgr = supervisor_manager
        self.handlers = {
            SupervisorModel.IMAGE: self.respond_image,
            SupervisorModel.LLM: self.respond_llm,
            SupervisorModel.POKE: self.respond_poke,
        }
        self._models, self._weights = self._build_response_pool()

    def _build_response_pool(
        self,
    ) -> tuple[tuple[SupervisorModel, ...], tuple[int, ...]]:
        pool = []
        for model in self.handlers:
            weight = self.config.weight_of(model)
            if weight > 0:
                pool.append((model, weight))
        if not pool:
            logger.warning(
                "All supervisor response weights are zero; responses disabled"
            )
            return (), ()
        models, weights = zip(*pool)
        return models, weights

    async def supervise(self, event: AstrMessageEvent) -> list[BaseMessageComponent]:
        """Select and execute one weighted reaction for a supervised message"""
        if not self.supervisor_mgr.is_supervising(event.get_sender_id()):
            return []
        if not self._models:
            return []

        model = random.choices(self._models, self._weights, k=1)[0]
        logger.debug(f"Selected supervisor response model: {model}")
        try:
            return await self.handlers[model](event)
        except Exception as exc:
            logger.error(f"Supervisor response model {model} failed: {exc}")
            return []

    async def respond_image(
        self, event: AstrMessageEvent
    ) -> list[BaseMessageComponent]:
        available_images = [
            image_path for image_path in self.config.image_files if image_path.is_file()
        ]
        if not available_images:
            if self.config.image_files:
                logger.warning("No configured supervisor image exists")
            return []
        return [
            At(qq=event.get_sender_id()),
            Image(str(random.choice(available_images))),
        ]

    async def respond_llm(self, event: AstrMessageEvent) -> list[BaseMessageComponent]:
        provider = self.context.get_using_provider()
        if not provider:
            return []
        response = await provider.text_chat(
            prompt=f"他来水群了：{event.get_message_str()}",
            contexts=[{"role": "system", "content": self.config.llm.prompt}],
        )
        return [Plain(" " + response.completion_text)]

    async def respond_poke(self, event: AstrMessageEvent) -> list[BaseMessageComponent]:
        if isinstance(event, AiocqhttpMessageEvent):
            for _ in range(self.config.poke.times):
                await event.bot.send_poke(
                    user_id=int(event.get_sender_id()),
                    group_id=int(event.get_group_id()),
                )
        return []
