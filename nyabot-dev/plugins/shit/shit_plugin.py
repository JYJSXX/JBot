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

    
    
class ShitPlugin(
    CQHTTPGroupMessageCommandHandlerPlugin[
        GroupMessageEvent, None, ShitPluginConfig
    ]
):
    async def ask_poe(self, message: str) -> ReturnValue:
        message = "想象你是一个高智商高情商的毒舌人设，请你用尽量简短的纯文本来回复：" + message
        msg = fp.ProtocolMessage(role="user", content=message)
        chunks = ""
        async for chunk in fp.get_bot_response(messages=[msg], bot_name="GPT-5.2", api_key=api_key):
            chunks += chunk.text
        return ReturnValue(0, reply=chunks)
    command = LeafCommand(
        name="ask",
        desc="ask",
        limited_roles=None,

        function=FunctionWithFixedParams(
            func=ask_poe,
            fixed_param_desc_list=[
                ("message", str, "问题")
            ]
        )

    )