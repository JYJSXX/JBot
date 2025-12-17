from alicebot.adapter.cqhttp.event import GroupMessageEvent

from nyaplugin import NYAPluginState
from nyaplugin.command_handler import (
    CQHTTPGroupMessageCommandHandlerPlugin,
    CQHTTPGroupMessageCommandHandlerPluginConfig,
    FunctionWithFixedParams,
    InternalCommand,
    LeafCommand,
    ReturnValue,
    RootCommand,
)


class ControllerPluginConfig(CQHTTPGroupMessageCommandHandlerPluginConfig):
    __config_name__ = "controller"


class ControllerPlugin(
    CQHTTPGroupMessageCommandHandlerPlugin[
        GroupMessageEvent, NYAPluginState, ControllerPluginConfig
    ]
):
    async def ctrl_state_save(self) -> ReturnValue:
        for plugin in self.registered_nyaplugin_list:
            await plugin.save_state(self.bot)
        await self.event.reply("已保存所有插件状态")
        return ReturnValue(0)

    async def ctrl_state_load(self) -> ReturnValue:
        for plugin in self.registered_nyaplugin_list:
            await plugin.load_state(self.bot)
        await self.event.reply("已加载所有插件状态")
        return ReturnValue(0)

    async def ctrl_plugin_list(self) -> ReturnValue:
        await self.event.reply(
            "已加载的插件：\n"
            + "\n".join(
                "* " + registered_plugin.__name__
                for registered_plugin in self.registered_nyaplugin_list
            )
        )
        return ReturnValue(0)

    async def ctrl_plugin_show_config(self, plugin_name: str) -> ReturnValue:
        plugin = next(
            (
                registered_plugin
                for registered_plugin in self.registered_nyaplugin_list
                if registered_plugin.__name__ == plugin_name
            ),
            None,
        )

        if not plugin:
            await self.event.reply(f"未找到插件 {plugin_name}")
            return ReturnValue(1, log=f"Plugin not found: {plugin_name}")

        plugin_instance = plugin()
        plugin_instance.event = self.event
        await self.event.reply(plugin_instance.config.model_dump_json())
        return ReturnValue(0)

    command = RootCommand(
        name="ctrl",
        desc="JBot 控制命令",
        limited_roles={"admin"},
        subcommand_list=[
            InternalCommand(
                name="state",
                desc="插件状态控制命令",
                subcommand_list=[
                    LeafCommand(
                        name="save",
                        desc="保存所有插件的状态",
                        limited_roles={"admin"},
                        function=FunctionWithFixedParams(
                            func=ctrl_state_save,
                            fixed_param_desc_list=[],
                        ),
                    ),
                    LeafCommand(
                        name="load",
                        desc="加载所有插件的状态",
                        limited_roles={"admin"},
                        function=FunctionWithFixedParams(
                            func=ctrl_state_load,
                            fixed_param_desc_list=[],
                        ),
                    ),
                ],
                limited_roles={"admin"},
            ),
            InternalCommand(
                name="plugin",
                desc="插件控制命令",
                limited_roles={"admin"},
                subcommand_list=[
                    LeafCommand(
                        name="list",
                        desc="列出所有插件",
                        limited_roles={"admin"},
                        function=FunctionWithFixedParams(
                            func=ctrl_plugin_list, fixed_param_desc_list=[]
                        ),
                    ),
                    LeafCommand(
                        name="show-config",
                        desc="查看插件配置",
                        limited_roles={"admin"},
                        function=FunctionWithFixedParams(
                            func=ctrl_plugin_show_config,
                            fixed_param_desc_list=[("plugin_name", str, "插件名")],
                        ),
                    ),
                ],
            ),
        ],
    )
