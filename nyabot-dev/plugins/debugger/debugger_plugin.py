import json

from alicebot.adapter.cqhttp.event import GroupMessageEvent
from alicebot.adapter.cqhttp.message import CQHTTPMessageSegment

from nyaplugin.command_handler import (
    CQHTTPGroupMessageCommandHandlerPlugin,
    CQHTTPGroupMessageCommandHandlerPluginConfig,
    FunctionWithFixedParams,
    FunctionWithVariableParams,
    LeafCommand,
    ReturnValue,
    RootCommand,
)
from nyaplugin.nyaplugin_base import NYAPluginState


class DebuggerPluginConfig(CQHTTPGroupMessageCommandHandlerPluginConfig):
    __config_name__ = "debugger"


class DebuggerPlugin(
    CQHTTPGroupMessageCommandHandlerPlugin[
        GroupMessageEvent, NYAPluginState, DebuggerPluginConfig
    ]
):
    """
    'debug': NYABot 调试用命令
    子命令列表：
    * eval: 计算一个 Python 表达式
    * exec: 执行一段 Python 代码
    * echo: 回显一段文本
    * echo-next: 回显下一条消息
    * echo-json: 将一段文本以 JSON 格式回显
    """

    async def debug_eval(self, *code: str) -> ReturnValue:
        """
        计算一个 Python 表达式
        """
        try:
            result = eval(" ".join(code))
        except Exception as e:
            await self.event.reply(f"Error when eval {code!r}: {e}")
            return ReturnValue(1, log=f"Error when eval {code!r}: {e}")

        await self.event.reply(f"{result}")
        return ReturnValue(0)

    async def debug_exec(self, *code: str) -> ReturnValue:
        """
        执行一段 Python 代码
        """
        try:
            exec(" ".join(code))
        except Exception as e:
            await self.event.reply(f"Error when exec {code!r}: {e}")
            return ReturnValue(1, log=f"Error when exec {code!r}: {e}")

        await self.event.reply(f"Executed {code!r}")
        return ReturnValue(0)

    async def debug_echo(self, text: str) -> ReturnValue:
        """
        回显一段文本
        """
        await self.event.reply(text)
        return ReturnValue(0)

    async def debug_echo_next(self) -> ReturnValue:
        """
        回显下一条消息
        """
        await self.event.reply("请发送要回显的内容")
        next = await self.event.get()
        await self.event.reply(next.message)
        return ReturnValue(0)

    async def debug_echo_json(self, data: str) -> ReturnValue:
        """
        将一段文本以 JSON 格式回显
        """
        try:
            json.loads(data)
        except json.JSONDecodeError as e:
            await self.event.reply(f"JSON decode error: {e}")
            return ReturnValue(1, log=f"JSON decode error: {e}")

        await self.event.reply(CQHTTPMessageSegment.json_message(data))
        return ReturnValue(0)
    
    async def ps_aux(self) -> ReturnValue:
        """
        列出当前进程
        """
        import subprocess
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        await self.event.reply(f"当前进程列表：\n{result.stdout}")
        return ReturnValue(0)

    command = RootCommand(
        name="debug",
        desc="JBot 调试用命令（测试群限定）",
        limited_roles={"admin"},
        subcommand_list=[
            LeafCommand(
                name="eval",
                desc="计算一个 Python 表达式",
                limited_roles={"admin"},
                function=FunctionWithVariableParams(
                    func=debug_eval,
                    fixed_param_desc_list=[],
                    variable_param_desc=("code", str, "要计算的 Python 表达式"),
                ),
            ),
            LeafCommand(
                name="exec",
                desc="执行一段 Python 代码",
                limited_roles={"admin"},
                function=FunctionWithVariableParams(
                    func=debug_exec,
                    fixed_param_desc_list=[],
                    variable_param_desc=("code", str, "要执行的 Python 代码"),
                ),
            ),
            LeafCommand(
                name="echo",
                desc="回显一段文本",
                limited_roles={"admin"},
                function=FunctionWithFixedParams(
                    func=debug_echo,
                    fixed_param_desc_list=[("text", str, "要回显的文本")],
                ),
            ),
            LeafCommand(
                name="echo-next",
                desc="回显下一条消息",
                limited_roles={"admin"},
                function=FunctionWithFixedParams(
                    func=debug_echo_next,
                    fixed_param_desc_list=[],
                ),
            ),
            LeafCommand(
                name="echo-json",
                desc="将一段文本以 JSON 格式回显",
                limited_roles={"admin"},
                function=FunctionWithFixedParams(
                    func=debug_echo_json,
                    fixed_param_desc_list=[("data", str, "要回显的 JSON 数据")],
                ),
            ),
            LeafCommand(
                name="ps-aux",
                desc="列出当前进程",
                limited_roles={"admin"},
                function=FunctionWithFixedParams(
                    func=ps_aux,
                    fixed_param_desc_list=[],
                ),
            ),
        ],
    )
