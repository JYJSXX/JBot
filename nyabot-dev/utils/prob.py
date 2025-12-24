import bisect
import random
from itertools import accumulate
from typing import Callable, Generic, ParamSpec, TypeVar

T = TypeVar("T")
ParamsT = ParamSpec("ParamsT")


class WeightedArg(Generic[ParamsT]):
    def __init__(self, weight: int, *args: ParamsT.args, **kwargs: ParamsT.kwargs):
        self.weight = weight
        self.args = args
        self.kwargs = kwargs


def weighted_call(
    func: Callable[ParamsT, T], *weighted_args: WeightedArg[ParamsT]
) -> T:
    if not weighted_args:
        raise ValueError("至少需要提供一组带权参数")

    if any(weighted_arg.weight < 0 for weighted_arg in weighted_args):
        raise ValueError("权重必须不小于 0")

    # 计算权重部分和
    weight_partial_sum = list(
        accumulate(weighted_arg.weight for weighted_arg in weighted_args)
    )
    total_weight = weight_partial_sum[-1]

    # 取 [1, total_weight] 之间的随机值
    rand = random.randint(1, total_weight)
    # 二分查找找到对应的参数
    idx = bisect.bisect_left(weight_partial_sum, rand)

    return func(*weighted_args[idx].args, **weighted_args[idx].kwargs)