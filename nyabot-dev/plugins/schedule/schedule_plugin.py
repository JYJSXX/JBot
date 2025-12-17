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

class ScheduleException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class Time(BaseModel):
        
    items: list[tuple] = [()]

    def __init__(self, items: list[tuple[int, int]]):
        super().__init__(items=items)

    def add_item(self, day: int, time: tuple[int, int]) -> None:
        if not (1 <= day <= 7):
            raise ScheduleException(f"Invalid day: {day}")
        if not (1 <= time[0] <= 13 and 1 <= time[1] <= 13 and time[0] <= time[1]):
            raise ScheduleException(f"Invalid time: {time}")
        self.items.append((day, time))

    @classmethod
    def from_str(cls, input:str) -> "Time":
        pattern = r'([1-7])\(([1-9]|1[0-3])(?:,\s*([1-9]|1[0-3]))*\)'
        match = re.match(pattern, input)
        if not match:
            raise ScheduleException(f"Invalid time format: {input}")
        matches = re.findall(pattern=pattern, string=input)
        items = []
        for date, *period in matches:
            assert len(period) == 2 and all(1 <= int(num) <= 13 for num in period)
            items.append((date, (period[0], period[-1])))
        if not items:
            raise ScheduleException(f"Invalid time format: {input}")
        return cls(items=items)
    
    def __str__(self) -> str:
        day_dict = {
            1: "周一",
            2: "周二",
            3: "周三",
            4: "周四",
            5: "周五",
            6: "周六",
            7: "周日",
        }
        return ", ".join([f"{day_dict[item[0]]}({item[1][0]}-{item[1][1]})" for item in self.items])



class SchedulePluginConfig(CQHTTPGroupMessageCommandHandlerPluginConfig):
    __config_name__ = "schedule"
    report_gid : int | None = 1022660464
    state_filename : str | None = "schedule.json"
    class User(BaseModel):
        uid: int
        nickname: str
    class Course(BaseModel):
        name: str
        time: Time | None
        place: str
        valid_weeks: list[int] = [i for i in range(1, 21)]

        def __str__(self) -> str:
            return f"{self.name} @ {self.place} : {self.time if self.time else '神秘时间'}"
    class Schedule(BaseModel):
        uid: int
        name : str
        course_list: list["SchedulePluginConfig.Course"]
        def __str__(self) -> str:
            return f"{self.uid}: {self.name} @ {self.course_list}"

class SchedulePluginState(NYAPluginState):
    def __init__(self):
        self.courses: list[SchedulePluginConfig.Course] = []
        self.schedules: list[SchedulePluginConfig.Schedule] = []
        self.users: dict[int, SchedulePluginConfig.User] = {}
        self.user_schedules: dict[int, list[SchedulePluginConfig.Schedule]] = {}
        self.nickname_to_uid: dict[str, int] = {}

    async def from_dict(self, obj) -> None:
        if obj is None:
            return
        self.courses = [SchedulePluginConfig.Course(**course) for course in obj["courses"]]
        self.schedules = [SchedulePluginConfig.Schedule(**schedule) for schedule in obj["schedules"]]
        self.users = {user["uid"]: SchedulePluginConfig.User(**user) for user in obj["users"]}
        self.user_schedules = {int(gid): [SchedulePluginConfig.Schedule(**schedule) for schedule in schedules] for gid, schedules in obj["user_schedules"].items()}
        self.nickname_to_uid = {nickname: uid for uid, nickname in obj["nickname_to_uid"].items()}
    async def to_dict(self) -> dict:
        return {
            "courses": [course.model_dump() for course in self.courses],
            "schedules": [schedule.model_dump() for schedule in self.schedules],
            "users": [user.model_dump() for user in self.users.values()],
            "user_schedules": {gid: [schedule.model_dump() for schedule in schedules] for gid, schedules in self.user_schedules.items()},
            "nickname_to_uid": {nickname: uid for uid, nickname in self.nickname_to_uid.items()},
        }
    




class SchedulePlugin(
    CQHTTPGroupMessageCommandHandlerPlugin[
        GroupMessageEvent, SchedulePluginState, SchedulePluginConfig
    ]
):
    def __init__(self) -> None:
        super().__init__()
        self.state = self.__init_state__()
    def __init_state__(self) -> SchedulePluginState:
        return SchedulePluginState()


    def __add_schedule__(self, uid: int, name: str | None = None) -> ReturnValue:
        if any(s.name == name for s in self.state.schedules):
            return ReturnValue(1, reply=f"课程表 {name} 已存在" if name else "请手动创建课程表并命名")
        schedule = SchedulePluginConfig.Schedule(uid=uid, name = name or self.state.users[uid].nickname + "'s schedule", course_list=[])
        if uid not in self.state.user_schedules:
            self.state.user_schedules.update({uid: schedule})
        else:
            self.state.user_schedules[uid].append(schedule)
        self.state.schedules.append(schedule)
        self.logger.debug(f"schedule {schedule} added")
        return ReturnValue(0)
    
    def show_status(self) -> ReturnValue:
        return ReturnValue(0, reply=json.dumps({
            "courses": [course.model_dump() for course in self.state.courses],
            "schedules": [schedule.model_dump() for schedule in self.state.schedules],
            "users": [user.model_dump() for user in self.state.users.values()],
            "user_schedules": {gid: [schedule.model_dump() for schedule in schedules] for gid, schedules in self.state.user_schedules.items()},
            "nickname_to_uid": {nickname: uid for uid, nickname in self.state.nickname_to_uid.items()},
        }, indent=4))
    
    
    def add_schedule(self, name: str) -> ReturnValue:
        uid = self.event.user_id
        if __assert_user_exists__ := self.__assert_user_exists__():
            if isinstance(__assert_user_exists__, ReturnValue):
                return __assert_user_exists__
        if (ret := self.__add_schedule__(uid, name)) is ReturnValue(0):
            return ReturnValue(0, reply=f"课程表 {name} 添加成功")
        return ret
    
    def __assert_user_exists__(self) -> bool | ReturnValue:
        if self.event.user_id not in self.state.users:
            return ReturnValue(1, reply="用户不存在，请先添加用户\n try: \'help schedule user add\'")
        return True

    def add_user(self, *nickname: str) -> ReturnValue:
        if len(nickname) == 0:
            nickname = [self.event.sender.nickname]
            self.logger.debug(f"{nickname}")
        try:
            if self.state == None:
                self.state = self.__init_state__()
            if self.event.user_id in self.state.users:
                return ReturnValue(1,reply=f"用户 {nickname[0]} 已存在")
            self.state.users[self.event.user_id] = SchedulePluginConfig.User(uid=self.event.user_id, nickname=nickname[0])
            self.state.nickname_to_uid[nickname[0]] = self.event.user_id
            self.logger.debug(f"用户 {nickname[0]} 添加成功")
            if (ret := self.__add_schedule__(self.event.user_id)) is not ReturnValue(0):
                return ret
            return ReturnValue(0,reply=f"用户 {nickname[0]} 添加成功")
        except Exception as e:
            self.logger.error(f"{__file__}:{__name__}:add_user error: {e}")
            return ReturnValue(2, report=f"{__file__}" + str(e))

    def list_user(self) -> ReturnValue:
        return ReturnValue(0,reply=f"用户列表：{', '.join([user.nickname for user in self.state.users.values()])}")
    
    def remove_user(self, nickname: str | None = None) -> ReturnValue:
        try:
            if nickname is None:
                nickname = self.state.users[self.event.user_id].nickname
            if (uid := int(self.state.nickname_to_uid.get(nickname, None))) in self.state.users:
                if uid in self.state.users:
                    self.state.users.pop(uid)
                if nickname in self.state.nickname_to_uid:
                    self.state.nickname_to_uid.pop(nickname)
                if uid in self.state.user_schedules:
                    for schedule in self.state.user_schedules[uid]:
                        self.state.schedules.remove(schedule)
                    self.state.user_schedules.pop(uid)
            else:
                return ReturnValue(1,reply=f"用户 {nickname} 不存在", report=f"{__file__}" + f"user {nickname} / {uid} not found\n {self.state.users}\n {type(uid)} \n {uid == 2055663122}")
            return ReturnValue(0,reply=f"用户 {nickname} 删除成功")
        except Exception as e:
            self.logger.error(f"{__file__}:{__name__}:remove_user error: {e}")
            return ReturnValue(2, reply=str(e), report=f"{__file__}" + str(e))

    def refresh_schedule(self) -> ReturnValue:
        for schedule in self.state.schedules:
            if schedule.uid not in self.state.user_schedules:
                self.state.schedules.remove(schedule)
        return ReturnValue(0, reply="课程表刷新成功")

    def list_schedule(self, uid: str | None) -> ReturnValue:
        self.logger.debug(f"type of uid: {type(uid)}")
        if uid is not None and len(uid) > 0:
            self.logger.debug(f"list_schedule uid: {uid[0]}")
            self.logger.debug(f"nickname_to_uid: {self.state.nickname_to_uid}")
            user_id = self.state.nickname_to_uid.get(uid[0], None)
            if user_id is None:
                try:
                    user_id = int(uid[0])
                except:
                    return ReturnValue(1,reply=f"用户 {uid[0]} 不存在")
        else:
            user_id = self.event.user_id
        if user_id in self.state.user_schedules:
            schedule_list = self.state.user_schedules[user_id]
        else:
            return ReturnValue(1,reply=f"请先创建用户\n try: \'help schedule user add\'")
        return ReturnValue(0,reply=f"课程表列表：{', '.join([schedule.name for schedule in schedule_list])}")

    def __create_course__(self, name: str, place: str, time_: str, add_to_schedule: bool, *valid_weeks_: int) -> ReturnValue:
        try:
            time = Time.from_str(time_)
        except ScheduleException as e:
            return ReturnValue(1, reply=f"时间格式错误: {e.message}")
        except Exception as e:
            self.logger.error(f"create_course error: {e}")
            return ReturnValue(2, report=f"{__file__}" + str(e))
        if  len(valid_weeks_) == 0:
            course = SchedulePluginConfig.Course(name=name, place=place, time=time)
        elif len(valid_weeks_) % 2 != 0:
            return ReturnValue(3, reply="有效周列表格式错误: 每两个输入一组，如 2 2 5 7 表示第2，5-7周上课")
        else:
            valid_weeks = []
            for i in range(0, len(valid_weeks_), 2):
                valid_weeks.extend(list(range(valid_weeks_[i], valid_weeks_[i+1]+1)))
            course = SchedulePluginConfig.Course(name=name, place=place, time=time, valid_weeks=valid_weeks)
        self.state.courses.append(course)
        if add_to_schedule:
            if self.event.user_id not in self.state.user_schedules:
                self.__add_schedule__(self.event.user_id)
            self.state.user_schedules[self.event.user_id][0].course_list.append(course)
        return ReturnValue(0,reply=f"课程 {name} 添加成功")
    
    def create_course_with_schedule(self, name: str, place: str, time_: str, *valid_weeks_: int) -> ReturnValue:
        return self.__create_course__(name, place, time_, True, *valid_weeks_)
    def create_course(self, name: str, place: str, time_: str, *valid_weeks_: int) -> ReturnValue:
        return self.__create_course__(name, place, time_, False, *valid_weeks_)
    
    async def set_default_schedule(self, schedule_name: str | None = None) -> ReturnValue:
        uid = self.event.user_id
        if __assert_user_exists__ := self.__assert_user_exists__():
            if isinstance(__assert_user_exists__, ReturnValue):
                return __assert_user_exists__
        if len(self.state.user_schedules[uid]) == 0:
            return ReturnValue(1, reply="用户没有课程表，请先创建课程表")
        if schedule_name is None or len(schedule_name) == 0:
            try:
                Q = await self.event.ask(f"🫷请选择课程表\n*" + "\n".join([str(i+1) + " : " + s.name for i, s in enumerate(self.state.user_schedules[uid])]), timeout=30)
                schedule_name = self.state.user_schedules[uid][int(str(Q.message).strip()) - 1].name
            except GetEventTimeout:
                return ReturnValue(1, reply="操作超时")
            except Exception as e:
                self.logger.error(f"set_default_schedule error: {e}")
                return ReturnValue(2, reply="选择课程表失败", report=f"{__file__}" + str(e))

        for schedule in self.state.user_schedules[self.event.user_id]:
            if schedule.name == schedule_name:
                self.state.user_schedules[self.event.user_id].remove(schedule)
                self.state.user_schedules[self.event.user_id].insert(0, schedule)
                return ReturnValue(0, reply=f"已将 {schedule_name} 设为默认课程表")
        return ReturnValue(2, reply=f"课程表 {schedule_name} 不存在")

    async def add_course(self, course_name: str, schedule_name: str | None = None) -> ReturnValue:
        uid = self.event.user_id
        if __assert_user_exists__ := self.__assert_user_exists__():
            if isinstance(__assert_user_exists__, ReturnValue):
                return __assert_user_exists__
        courses = [c for c in self.state.courses if c.name == course_name]
        if not courses:
            return ReturnValue(2, reply=f"课程 {course_name} 不存在")
        elif len(courses) > 1:
            try:
                Q = await self.event.ask(f"🫷根据 {course_name} 找到多个课程，请输入课程编号选择课程：\n" + "\n".join([f"{i+1}. {str(c)}" for i, c in enumerate(courses)]), timeout=30)
                course = courses[int(str(Q.message).strip()) - 1]
            except GetEventTimeout:
                return ReturnValue(5, reply="操作超时")
            except Exception as e:
                self.logger.error(f"add_course error: {e}")
                return ReturnValue(6, reply="选择课程失败，请输入正确的课程编号", report=f"{__file__}" + str(e))
        course = courses[0]
        if schedule_name is None or len(schedule_name) == 0:
            schedule = self.state.user_schedules[uid][0]
        else:
            schedule = None
            for s in self.state.user_schedules[uid]:
                if s.name == schedule_name:
                    schedule = s
                    break
            if schedule is None:
                return ReturnValue(3, reply=f"课程表 {schedule_name} 不存在")
        if course in schedule.course_list:
            return ReturnValue(4, reply=f"课程 {course_name} 已在课程表 {schedule.name} 中")
        schedule.course_list.append(course)
        return ReturnValue(0, reply=f"已将课程 {course_name} 加入课程表 {schedule.name}")
    
    def list_course(self, course_name:str | None = None) -> ReturnValue:
        if course_name is None or len(course_name) == 0:
            return ReturnValue(0, reply="课程列表：\n" + "\n".join([str(c) for c in self.state.courses[:5]]) if self.state.courses else "课程列表为空")
        courses = [c for c in self.state.courses if course_name in c.name]
        if not courses:
            return ReturnValue(1, reply=f"课程 {course_name} 不存在")
        return ReturnValue(0, reply="查询结果：\n" + "\n".join([str(c) for c in courses]))

    async def test_ask(self) -> ReturnValue:
        try:
            Q = await self.event.ask("🫷你是人类吗？",timeout=1)
        except GetEventTimeout :
            return ReturnValue(2, reply="操作超时，你真是人类吗？")
        if Q and "是" in Q.message:
            return ReturnValue(0, reply="你是人类！")
        else:
            return ReturnValue(1, reply="你不是人类！")

    command = RootCommand(
        name="schedule",
        desc="课程表管理命令",
        limited_roles=None,
        subcommand_list=[
            InternalCommand(
                name="user",
                desc="用户相关命令",
                limited_roles=None,
                subcommand_list=[
                    LeafCommand(
                        name="add",
                        desc="添加用户",
                        limited_roles=None,
                        function=FunctionWithVariableParams(
                            func=add_user,
                            fixed_param_desc_list=[],
                            variable_param_desc=(
                                "nickname",
                                str,
                                "用户昵称",
                            ),
                        ),
                    ),
                    LeafCommand(
                        name="list",
                        desc="列出所有用户",
                        limited_roles=None,
                        function=FunctionWithFixedParams(func=list_user, fixed_param_desc_list=[]),
                    ),
                    LeafCommand(
                        name="remove",
                        desc="删除用户",
                        limited_roles={"admin"},
                        function=FunctionWithOptionalParam(func=remove_user, fixed_param_desc_list=[],
                            optional_param_desc=(
                            "nickname",
                            str,
                            "用户昵称",
                            )
                        ),
                    )
                ]
                
            ),
            InternalCommand(
                name="course",
                desc="课程相关命令",
                limited_roles=None,
                subcommand_list=[
                    LeafCommand( #createwithschedule
                        name="create",
                        desc="创建课程",
                        limited_roles=None,
                        function=FunctionWithVariableParams(
                            func=create_course_with_schedule,
                            fixed_param_desc_list=[
                                (
                                    "name",
                                    str,
                                    "课程名称",
                                ),
                                (
                                    "place",
                                    str,
                                    "上课地点",
                                ),
                                (
                                    "time",
                                    str,
                                    "上课时间, 格式和教务系统类似3(1,2),5(6,7)",
                                )
                            ],
                            variable_param_desc=(
                                "valid week",
                                int,
                                "有效周列表, 每两个输入一组，如 2 2 5 7 表示第2，5-7周上课，默认1-20周",
                            ),
                        ),
                    ),
                    LeafCommand( #createonly
                        name="createonly",
                        desc="仅创建课程（不加入课程表）",
                        limited_roles=None,
                        function=FunctionWithVariableParams(
                            func=create_course,
                            fixed_param_desc_list=[
                                (
                                    "name",
                                    str,
                                    "课程名称",
                                ),
                                (
                                    "place",
                                    str,
                                    "上课地点",
                                ),
                                (
                                    "time",
                                    str,
                                    "上课时间, 格式和教务系统类似3(1,2),5(6,7)",
                                )
                            ],
                            variable_param_desc=(
                                "valid week",
                                int,
                                "有效周列表, 每两个输入一组，如 2 2 5 7 表示第2，5-7周上课，默认1-20周",
                            ),
                        ),

                    ),
                    LeafCommand( # list
                        name="list",
                        desc="列出所有课程",
                        limited_roles=None,
                        function=FunctionWithOptionalParam(
                            func=list_course,
                            fixed_param_desc_list=[],
                            optional_param_desc=(
                                "course_name",
                                str,
                                "查询的课程名称, 默认列出所有课程",
                            )
                        )
                    ),
                    
                    LeafCommand(
                        name="add",
                        desc="将课程加入课程表",
                        limited_roles=None,
                        function=FunctionWithOptionalParam(
                            func=add_course,
                            fixed_param_desc_list=[
                                (
                                    "course_name",
                                    str,
                                    "课程名称",
                                )
                            ],
                            optional_param_desc=(
                                "schedule_name",
                                str,
                                "课程表名称, 默认添加到默认课程表",
                            )
                        )
                    ),
                ]
            ),
            LeafCommand(
                name="list",
                desc="列出所有课程表",
                limited_roles=None,
                function=FunctionWithOptionalParam(
                    func=list_schedule,
                    fixed_param_desc_list=[],
                    optional_param_desc=(
                        "uid",
                        str,
                        "用户 ID 或昵称, 默认当前用户",
                    ),
                ),
            ),
            LeafCommand(
                name="set",
                desc="设置默认课程表",
                limited_roles=None,
                function=FunctionWithOptionalParam(
                    func=set_default_schedule,
                    fixed_param_desc_list=[
                        
                    ],
                    optional_param_desc=
                    (
                        "schedule_name",
                        str,
                        "课程表名称",
                    )
                )
            ),
            LeafCommand(
                name="add",
                desc="添加课程表",
                limited_roles=None,
                function=FunctionWithFixedParams(
                    func=add_schedule,
                    fixed_param_desc_list=[
                        (
                            "name",
                            str,
                            "课程表名称",
                        )
                    ],
                ),
            ),
            LeafCommand(
                name="refresh",
                desc="刷新课程表",
                limited_roles={"admin"},
                function=FunctionWithFixedParams(func=refresh_schedule, fixed_param_desc_list=[]),
            ),
            LeafCommand(
                name="status",
                desc="查看课程表状态",
                limited_roles={"admin"},
                function=FunctionWithFixedParams(func=show_status, fixed_param_desc_list=[]),
            ),
            LeafCommand(
                name="testask",
                desc="测试ask功能",
                limited_roles=None,
                function=FunctionWithFixedParams(
                    func=test_ask,
                    fixed_param_desc_list=[]
                )
            )
        
        ]
    )