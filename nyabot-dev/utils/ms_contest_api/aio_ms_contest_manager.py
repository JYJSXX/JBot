import asyncio
import hashlib
import hmac
import time
from functools import wraps
from typing import Awaitable, Callable, Generic, ParamSpec, Self, TypeVar, cast

from aiohttp import ClientResponse, ClientSession
from pydantic import BaseModel


class LoginResponse(BaseModel):
    """
    登陆操作返回值
    """

    token: str


class AccountInfo(BaseModel):
    """
    赛事管理者的帐号信息

    :var account_id: 帐号ID
    :vartype account_id: int
    :var currency: 虚拟货币信息
    :vartype currency: list[AccountInfo.CurrencyPart]
    :var nickname: 昵称
    :vartype nickname: str
    """

    class CurrencyPart(BaseModel):
        """
        虚拟货币信息

        :var count: 数量
        :vartype count: int
        :var id: 种类
        :vartype id: int
        """

        count: int
        id: int

    account_id: int
    currency: list[CurrencyPart]
    nickname: str


class PlayerInfo(BaseModel):
    """
    参赛选手信息

    :var account_id: 帐号ID
    :vartype account_id: int
    :var nickname: 昵称
    :vartype nickname: str
    :var create_time: 创建时间
    :vartype create_time: int
    :var account_data: 帐号比赛数据
    :vartype account_data: str
    :var info: 选手信息
    :vartype info: str
    :var remark: 备注
    :vartype remark: str
    :var state: 状态
    :vartype state: int
    :var unique_id: 赛事 ID
    :vartype unique_id: int
    :var season_id: 赛季 ID
    :vartype season_id: int
    """

    account_id: int
    nickname: str
    create_time: int
    account_data: str
    info: str
    remark: str
    state: int
    unique_id: int
    season_id: int


class PlayerList(BaseModel):
    """
    参赛选手列表

    :var list: 选手信息列表
    :vartype list: list[PlayerInfo]
    :var total: 选手总数
    :vartype total: int
    """

    list: list[PlayerInfo]
    total: int


class ReadyPlayerInfo(BaseModel):
    """
    准备就绪选手信息

    :var account_id: 帐号ID
    :vartype account_id: int
    :var nickname: 昵称
    :vartype nickname: str
    :var remark: 备注
    :vartype remark: str
    """

    account_id: int
    nickname: str
    remark: str


class GamePlanInfo(BaseModel):
    """
    预约对局信息

    :var uuid: 对局唯一 ID
    :vartype uuid: str
    :var accounts: 对局选手信息列表
    :vartype accounts: list[GamePlanInfo.AccountInfo]
    :var game_start_time: 预约开始时间
    :vartype game_start_time: int
    :var remark: 备注
    :vartype remark: str
    :var shuffle_seat: 是否随机座位
    :vartype shuffle_seat: bool
    """

    class AccountInfo(BaseModel):
        """
        对局选手信息

        :var account_id: 帐号 ID
        :vartype account_id: int
        :var nickname: 昵称（电脑玩家无此字段）
        :vartype nickname: str | None
        :var seat: 座次
        :vartype seat: int
        :var init_points: 初始点数
        :vartype init_points: int
        :var remark: 备注（电脑玩家无此字段）
        :vartype remark: str | None
        """

        account_id: int
        nickname: str | None
        seat: int
        init_points: int
        remark: str | None

    uuid: str
    accounts: list[AccountInfo]

    game_start_time: int
    remark: str
    shuffle_seat: bool


class RunningGameInfo(BaseModel):
    """
    进行中的对局信息

    :var game_uuid: 对局唯一 ID
    :vartype game_uuid: str
    :var players: 对局选手信息列表
    :vartype players: list[RunningGameInfo.PlayerInfo]
    :var start_time: 开始时间
    :vartype start_time: int
    :var tag: 标签
    :vartype tag: str
    """

    class PlayerInfo(BaseModel):
        """
        对局选手信息

        :var account_id: 帐号 ID
        :vartype account_id: int
        :var nickname: 昵称（电脑玩家无此字段）
        :vartype nickname: str | None
        """

        account_id: int
        nickname: str | None = None

    game_uuid: str
    players: list[PlayerInfo]
    start_time: int
    tag: str


class ErrorInfo(BaseModel):
    """
    错误信息

    :var error: 错误信息
    :vartype error: ErrorCodeInfo | None
    """

    class ErrorCodeInfo(BaseModel):
        """
        错误码信息

        :var code: 错误码
        :vartype code: int | None
        """

        code: int | None = None

    error: ErrorCodeInfo | None = None


class GameProgressInfo(BaseModel):
    """
    对局进度信息

    :var uuid: 对局唯一 ID
    :vartype uuid: str
    :var chang: 场数
    :vartype chang: int
    :var ju: 局数
    :vartype ju: int
    :var ben: 本场数
    :vartype ben: int
    :var is_end: 是否结束
    :vartype is_end: int
    :var scores: 分数列表
    :vartype scores: list[int]
    :var update_time: 更新时间
    :vartype update_time: int
    """

    uuid: str
    chang: int
    ju: int
    ben: int
    is_end: int
    scores: list[int] | None
    update_time: int


class GameRecordInfo(BaseModel):
    """
    对局记录信息

    :var uuid: 对局唯一 ID
    :vartype uuid: str
    :var accounts: 对局选手信息列表
    :vartype accounts: list[GameRecordInfo.AccountInfo]
    :var result: 对局结果信息
    :vartype result: GameRecordInfo.ResultInfo
    :var start_time: 开始时间
    :vartype start_time: int
    :var end_time: 结束时间
    :vartype end_time: int
    :var tag: 标签
    :vartype tag: str
    :var removed: 是否已删除
    :vartype removed: bool
    """

    class AccountInfo(BaseModel):
        """
        对局选手信息

        :var account_id: 帐号 ID
        :vartype account_id: int
        :var nickname: 昵称（电脑玩家无此字段）
        :vartype nickname: str | None
        :var remark: 备注（电脑玩家无此字段）
        :vartype remark: str | None
        :var seat: 座次
        :vartype seat: int
        """

        account_id: int
        nickname: str | None = None
        remark: str | None = None
        seat: int

    class ResultInfo(BaseModel):
        """
        对局结果信息

        :var players: 各选手结果信息列表
        :vartype players: list[GameRecordInfo.ResultInfo.PlayerInfo]
        """

        class PlayerInfo(BaseModel):
            """
            对局选手结果信息

            :var part_point_1: 素点
            :vartype part_point_1: int
            :var seat: 座次
            :vartype seat: int
            :var total_point: 精算点
            :vartype total_point: int
            """

            part_point_1: int
            seat: int
            total_point: int

        players: list[PlayerInfo]

    uuid: str

    accounts: list[AccountInfo]
    result: ResultInfo

    start_time: int
    end_time: int

    tag: str
    removed: bool


class GameRecordList(BaseModel):
    """
    对局记录列表

    :var record_list: 对局记录信息列表
    :vartype record_list: list[GameRecordInfo]
    :var total: 总记录数
    :vartype total: int
    :var token: 访问令牌
    :vartype token: str
    """

    record_list: list[GameRecordInfo]
    total: int

    token: str


T = TypeVar("T")


class DataWrapper(BaseModel, Generic[T]):
    """
    数据包装器：API 返回的结果都是 { "data": ... }

    :var data: 包装的数据
    :vartype data: T
    """

    data: T


ParamsT = ParamSpec("ParamsT")
ModelT = TypeVar("ModelT", bound=BaseModel)


class MSContestManager:
    """
    赛事后台管理器
    """

    def __init__(self, account: str, hashed_password: str):
        self.account = account
        self.hashed_password = hashed_password
        self.contest_manipulator_session = ClientSession(
            base_url="https://contest-gate-202411.maj-soul.com/api/"
        )
        self.contest_monitor_session = ClientSession(
            base_url="https://common-202411.maj-soul.com/api/"
        )
        self.token: str | None = None

        self.logged_in = False
        self.login_lock = asyncio.Lock()

    @staticmethod
    def _init_login(
        func: Callable[ParamsT, Awaitable[ClientResponse]],
    ) -> Callable[ParamsT, Awaitable[ClientResponse]]:
        @wraps(func)
        async def wrapper(
            *args: ParamsT.args, **kwargs: ParamsT.kwargs
        ) -> ClientResponse:
            if not cast(Self, args[0]).logged_in:
                async with cast(Self, args[0]).login_lock:
                    if not cast(Self, args[0]).logged_in:
                        cast(Self, args[0]).logged_in = await cast(
                            Self, args[0]
                        ).login()

            resp = await func(*args, **kwargs)
            return resp

        return wrapper

    @staticmethod
    def _login_and_retry(
        func: Callable[ParamsT, Awaitable[ClientResponse]],
    ) -> Callable[ParamsT, Awaitable[ClientResponse | None]]:
        @wraps(func)
        async def wrapper(
            *args: ParamsT.args, **kwargs: ParamsT.kwargs
        ) -> ClientResponse | None:
            resp = await func(*args, **kwargs)
            while resp.status == 401:
                # Unauthorized, call self.login()
                async with cast(Self, args[0]).login_lock:
                    if not await cast(Self, args[0]).login():
                        return
                resp = await func(*args, **kwargs)
            return resp

        return wrapper

    @staticmethod
    def _retry(
        times: int,
    ) -> Callable[
        [Callable[ParamsT, Awaitable[ClientResponse | None]]],
        Callable[ParamsT, Awaitable[ClientResponse | None]],
    ]:
        def decorator(
            func: Callable[ParamsT, Awaitable[ClientResponse | None]],
        ) -> Callable[ParamsT, Awaitable[ClientResponse | None]]:
            @wraps(func)
            async def wrapper(
                *args: ParamsT.args, **kwargs: ParamsT.kwargs
            ) -> ClientResponse | None:
                if times <= 0:
                    return await func(*args, **kwargs)

                resp = None
                for _ in range(times):
                    resp = await func(*args, **kwargs)
                    if resp and resp.status == 200:
                        return resp
                return resp

            return wrapper

        return decorator

    @staticmethod
    def _to_model(
        model: type[ModelT],
    ) -> Callable[
        [Callable[ParamsT, Awaitable[ClientResponse | None]]],
        Callable[ParamsT, Awaitable[ModelT | None]],
    ]:
        def decorator(
            func: Callable[ParamsT, Awaitable[ClientResponse | None]],
        ) -> Callable[ParamsT, Awaitable[ModelT | None]]:
            @wraps(func)
            async def wrapper(
                *args: ParamsT.args, **kwargs: ParamsT.kwargs
            ) -> ModelT | None:
                resp = await func(*args, **kwargs)
                if resp and resp.status == 200:
                    return model.model_validate(await resp.json())
                return None

            return wrapper

        return decorator

    @staticmethod
    def _take_data(
        func: Callable[ParamsT, Awaitable[DataWrapper[T] | None]],
    ) -> Callable[ParamsT, Awaitable[T | None]]:
        @wraps(func)
        async def wrapper(*args: ParamsT.args, **kwargs: ParamsT.kwargs) -> T | None:
            result = await func(*args, **kwargs)
            if result is None:
                return None
            return result.data

        return wrapper

    @staticmethod
    def _set_token(
        func: Callable[ParamsT, Awaitable[LoginResponse | None]],
    ) -> Callable[ParamsT, Awaitable[bool]]:
        @wraps(func)
        async def wrapper(*args: ParamsT.args, **kwargs: ParamsT.kwargs) -> bool:
            result = await func(*args, **kwargs)
            if result:
                cast(Self, args[0]).token = result.token
                return True
            return False

        return wrapper

    @_set_token
    @_take_data
    @_to_model(DataWrapper[LoginResponse])
    @_retry(0)
    async def login(self) -> ClientResponse:
        return await self.contest_manipulator_session.post(
            url="login",
            headers=self._get_headers(token=None),
            json={"account": self.account, "password": self.hashed_password, "type": 1},
        )

    @_take_data
    @_to_model(DataWrapper[AccountInfo])
    @_retry(0)
    @_login_and_retry
    @_init_login
    async def fetch_account_info(self) -> ClientResponse:
        """
        获取赛事管理者账户信息
        """
        return await self.contest_manipulator_session.get(
            url="contest/fetch_account_info",
            headers=self._get_headers(token=self.token),
        )

    async def fetch_player_list(
        self, contest_unique_id: int, season_id: int
    ) -> list[PlayerInfo] | None:
        """
        获取参赛选手列表
        """
        player_list_raw = await self._fetch_player_list_raw(
            contest_unique_id, season_id, 0, 10
        )
        if not player_list_raw:
            return None

        player_count = player_list_raw.total
        player_list: list[PlayerInfo] = []
        player_list.extend(player_list_raw.list)

        for offset in range(10, player_count, 10):
            player_list_raw = await self._fetch_player_list_raw(
                contest_unique_id, season_id, offset, 10
            )
            if not player_list_raw:
                return None
            player_list.extend(player_list_raw.list)

        return

    @_take_data
    @_to_model(DataWrapper[list[PlayerInfo]])
    @_retry(0)
    @_login_and_retry
    @_init_login
    async def fetch_ready_player_list(
        self, contest_unique_id: int, season_id: int
    ) -> ClientResponse:
        """
        获取准备中的选手列表
        """
        return await self.contest_manipulator_session.get(
            url="contest/ready_player_list",
            headers=self._get_headers(token=self.token),
            params={
                "unique_id": contest_unique_id,
                "season_id": season_id,
            },
        )

    @_take_data
    @_to_model(DataWrapper[list[GamePlanInfo]])
    @_retry(0)
    @_login_and_retry
    @_init_login
    async def fetch_game_plan_list(
        self, contest_unique_id: int, season_id: int
    ) -> ClientResponse:
        return await self.contest_manipulator_session.get(
            url="contest/fetch_contest_game_plan_list",
            headers=self._get_headers(token=self.token),
            params={
                "unique_id": contest_unique_id,
                "season_id": season_id,
            },
        )

    @_take_data
    @_to_model(DataWrapper[ErrorInfo])
    @_retry(0)
    @_login_and_retry
    @_init_login
    async def create_game_plan(
        self,
        contest_unique_id: int,
        season_id: int,
        account_list: list[int],
        *,
        init_points: list[int] = [25000, 25000, 25000, 25000],
        game_start_time: int = int(time.time()),
        shuffle_seats: bool = False,
        ai_level: int = 1,
        remark: str = "",
    ) -> ClientResponse:
        return await self.contest_manipulator_session.post(
            url="contest/create_game_plan",
            headers=self._get_headers(token=self.token),
            json={
                "unique_id": contest_unique_id,
                "season_id": season_id,
                "account_list": account_list,
                "init_points": init_points,
                "game_start_time": game_start_time,
                "shuffle_seats": shuffle_seats,
                "ai_level": ai_level,
                "remark": remark,
            },
        )

    @_take_data
    @_to_model(DataWrapper[ErrorInfo])
    @_retry(0)
    @_login_and_retry
    @_init_login
    async def remove_game_plan(
        self, contest_unique_id: int, season_id: int, game_uuid: str
    ) -> ClientResponse:
        return await self.contest_manipulator_session.post(
            url="contest/remove_contest_plan_game",
            headers=self._get_headers(token=self.token),
            json={
                "unique_id": str(contest_unique_id),
                "season_id": str(season_id),
                "uuid": game_uuid,
            },
        )

    @_take_data
    @_to_model(DataWrapper[list[RunningGameInfo]])
    @_retry(0)
    @_login_and_retry
    @_init_login
    async def fetch_running_game_list(
        self, contest_unique_id: int, season_id: int
    ) -> ClientResponse:
        return await self.contest_manipulator_session.get(
            url="contest/contest_running_game_list",
            headers=self._get_headers(token=self.token),
            params={
                "unique_id": contest_unique_id,
                "season_id": season_id,
            },
        )

    @_take_data
    @_to_model(DataWrapper[ErrorInfo])
    @_retry(0)
    @_login_and_retry
    @_init_login
    async def pause_game(
        self, contest_unique_id: int, game_uuid: str
    ) -> ClientResponse:
        # ! code = 1209 已在暂停状态
        return await self.contest_manipulator_session.post(
            url="contest/pause_contest_running_game",
            headers=self._get_headers(token=self.token),
            json={"unique_id": contest_unique_id, "game_uuid": game_uuid, "resume": 1},
        )

    @_take_data
    @_to_model(DataWrapper[ErrorInfo])
    @_retry(0)
    @_login_and_retry
    @_init_login
    async def resume_game(
        self, contest_unique_id: int, game_uuid: str
    ) -> ClientResponse:
        # ! code = 1210 已在恢复状态
        return await self.contest_manipulator_session.post(
            url="contest/pause_contest_running_game",
            headers=self._get_headers(token=self.token),
            json={"unique_id": contest_unique_id, "game_uuid": game_uuid, "resume": 2},
        )

    @_take_data
    @_to_model(DataWrapper[ErrorInfo])
    @_retry(0)
    @_login_and_retry
    @_init_login
    async def terminate_game(
        self, contest_unique_id: int, game_uuid: str
    ) -> ClientResponse:
        return await self.contest_manipulator_session.post(
            url="contest/terminate_contest_running_game",
            headers=self._get_headers(token=self.token),
            json={"unique_id": str(contest_unique_id), "uuid": game_uuid},
        )

    async def fetch_game_record_list(
        self, contest_unique_id: int, season_id: int
    ) -> list[GameRecordInfo] | None:
        game_list_raw = await self._fetch_game_record_list_raw(
            contest_unique_id, season_id, 0, 10
        )
        if not game_list_raw:
            return None

        game_count = game_list_raw.total
        game_list: list[GameRecordInfo] = []
        game_list.extend(game_list_raw.record_list)

        for offset in range(10, game_count, 10):
            game_list_raw = await self._fetch_game_record_list_raw(
                contest_unique_id, season_id, offset, 10
            )
            if not game_list_raw:
                return None
            game_list.extend(game_list_raw.record_list)

        return game_list

    @_to_model(GameProgressInfo)
    @_retry(0)
    async def view_game_progress(self, game_uuid: str) -> ClientResponse:
        return await self.contest_monitor_session.get(
            url=f"game/realtime/{game_uuid}/progress/latest",
            headers=self._get_headers(token=None),
        )

    # password hashing
    @staticmethod
    def hash_password(password: str) -> str:
        key = b"lailai"
        msg = password.encode("utf-8")
        result = hmac.new(key, msg, hashlib.sha256).hexdigest()
        return result

    @_take_data
    @_to_model(DataWrapper[PlayerList])
    @_retry(0)
    @_login_and_retry
    @_init_login
    async def _fetch_player_list_raw(
        self, contest_unique_id: int, season_id: int, offset: int, limit: int
    ) -> ClientResponse:
        return await self.contest_manipulator_session.get(
            url="contest/contest_season_player_list",
            headers=self._get_headers(token=self.token),
            params={
                "unique_id": contest_unique_id,
                "season_id": season_id,
                "search": "",
                "state": 2,
                "offset": offset,
                "limit": limit,
            },
        )

    @_take_data
    @_to_model(DataWrapper[GameRecordList])
    @_retry(0)
    @_login_and_retry
    @_init_login
    async def _fetch_game_record_list_raw(
        self, contest_unique_id: int, season_id: int, offset: int, limit: int
    ) -> ClientResponse:
        return await self.contest_manipulator_session.get(
            url="contest/fetch_contest_game_records",
            headers=self._get_headers(token=self.token),
            params={
                "unique_id": contest_unique_id,
                "season_id": season_id,
                "offset": offset,
                "limit": limit,
            },
        )

    @staticmethod
    def _get_headers(*, token: str | None) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Origin": "https://www.maj-soul.com",
            "Referer": "https://www.maj-soul.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "X-Web-Client-Version": "v1.0.0-142-g71d8162",
        }
        if token:
            headers["Authorization"] = f"Majsoul {token}"
        return headers
