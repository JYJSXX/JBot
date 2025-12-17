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
        client = fp.Client(api_key=api_key)
        msg = fp.ProtocolMessage(role="user", content=message)
        async for chunk in client.send_message(model="GPT-5.2", message=msg):
            if chunk.is_done:
                break
            if chunk.is_error:
                raise Exception(chunk.text)
        return ReturnValue(0, reply=chunk.text)
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