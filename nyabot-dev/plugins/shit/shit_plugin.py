import json

from alicebot.adapter.cqhttp.event import GroupMessageEvent
from alicebot.exceptions import GetEventTimeout
from alicebot.adapter.cqhttp.message import CQHTTPMessageSegment
from pydantic import BaseModel

import re
from nyaplugin.command_handler import (
    CQHTTPGroupMessageCommandHandlerPlugin,
    CQHTTPGroupMessageCommandHandlerPluginConfig,
    FunctionWithFixedParams,
    FunctionWithVariableParams,
    FunctionWithOptionalParam,
    LeafCommand,
    ReturnValue,
    InternalCommand,
    RootCommand,
)
from nyaplugin.nyaplugin_base import NYAPluginState
import fastapi_poe as fp
api_key ="5KWYa_nUmeTRLvlgX-reQrgJNI8YRsgd1CFkt0Pbhxc"


class ShitPluginConfig(CQHTTPGroupMessageCommandHandlerPluginConfig):
    __config_name__ = "schedule"


class ShitPluginState(NYAPluginState):
    def __init__(self) -> None:
        self.context = []
    async def from_dict(self, obj)-> None:
        if obj is None:
            return
        self.context = obj.get("context", [])
    async def to_dict(self) -> dict:
        return {
            "context": self.context
        }
    
class ShitPlugin(
    CQHTTPGroupMessageCommandHandlerPlugin[
        GroupMessageEvent, ShitPluginState, ShitPluginConfig
    ]
):
    def __init__(self) -> None:
        super().__init__()
        self.state = self.__init_state__()
    def __init_state__(self) -> ShitPluginState:
        return ShitPluginState()
    async def ask_poe(self, *message_: str) -> ReturnValue:
        message = " ".join(message_)
        message = "请你用尽量简短的纯文本来回复：" + message
        msg = fp.ProtocolMessage(role="user", content=message)
        self.state.context.append(msg)
        chunks = ""
        async for chunk in fp.get_bot_response(messages=self.state.context, bot_name="GPT-5.2", api_key=api_key):
            chunks += chunk.text
        self.state.context.append(fp.ProtocolMessage(role="bot", content=chunks))
        return ReturnValue(0, reply=chunks)
    command = LeafCommand(
        name="ask",
        desc="ask",
        limited_roles=None,

        function=FunctionWithVariableParams(
            func=ask_poe,
            variable_param_desc=("message", str, "要询问的问题"),
            fixed_param_desc_list=[],
        )

    )