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
    __config_name__ = "shit"
    report_gid : int | None = 1022660464
    state_filename : str | None = "shit.json"


class ShitPluginState(NYAPluginState):
    def __init__(self) -> None:
        self.context: dict[int, list[fp.ProtocolMessage]] = {}
    async def from_dict(self, obj)-> None:
        if obj is None:
            return
        self.context = {gid: [fp.ProtocolMessage(**msg) for msg in msgs] for gid, msgs in obj.get("context", {}).items()}
    async def to_dict(self) -> dict:
        return {
            "context": {gid: [x.model_dump() for x in msgs] for gid, msgs in self.context.items()}
        }
    
class ShitPlugin(
    CQHTTPGroupMessageCommandHandlerPlugin[
        GroupMessageEvent, ShitPluginState, ShitPluginConfig
    ]
):
    def __init__(self) -> None:
        super().__init__()

    def __init_state__(self) -> ShitPluginState:
        return ShitPluginState()
    async def ask_poe(self, *message_: str) -> ReturnValue:
        message = " ".join(message_)
        if message == "save" :
            if self.event.user_id == 2055663122:
                await self.save_state(self.bot)
                return ReturnValue(0, reply="已保存状态")
            else:
                return ReturnValue(1, reply="你没有权限")
        elif message == "show":
            if self.event.user_id == 2055663122:
                return ReturnValue(0, reply=f"当前上下文长度为：{len(self.state.context)}")
            else:
                return ReturnValue(1, reply="你没有权限")
        if message == "test":
            await self.event.reply([CQHTTPMessageSegment.image("https://qcloud.dpfile.com/pc/QQb34LJ3KAdhhFxsCZvfHgi1vSsaFGmzTUc3kMm6xfsE86uPgTG04ebXFIQgSFFJ.jpg")])
            return ReturnValue(1, reply="111test")
        message = "请你用尽量简短的纯文本来回复：" + message
        msg = fp.ProtocolMessage(role="user", content=message)
        self.logger.debug("message", message=message)



        gid = self.event.group_id
        if gid not in self.state.context:
            self.state.context[gid] = []
        self.state.context[gid].append(msg)
        chunks = ""
        async for chunk in fp.get_bot_response(messages=self.state.context[gid], bot_name="GPT-5.2", api_key=api_key):
            chunks += chunk.text
        self.state.context[gid].append(fp.ProtocolMessage(role="bot", content=chunks))
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