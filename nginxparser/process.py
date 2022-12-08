import typing as t
import pathlib
import os.path
from .nginxparser import load, UnspacedList

_nginx_cmd_type = str | list[str]
_nginx_row_type = tuple[_nginx_cmd_type, str | UnspacedList]
_nginx_type = UnspacedList
_T = t.TypeVar("_T")


def load_path(
    path: pathlib.Path = pathlib.Path("/etc/nginx/nginx.conf"),
) -> UnspacedList:
    conf = load(path.open())
    conf.insert(0, ["##", str(path)])
    return load_includes(conf, path)


def _flatten(obj: t.Sequence[list[_T]]) -> list[_T]:
    return sum(obj, [])


def load_includes(conf: UnspacedList, path: pathlib.Path) -> UnspacedList:
    # conf = list(conf)
    res = UnspacedList([])
    for cmd, arg in conf:
        if cmd == "include":
            rel = os.path.relpath(str(path / str(arg)), str(path.parent))
            for p in path.parent.glob(rel):
                res.extend(load_path(p.resolve()))
        elif isinstance(cmd, list):
            assert isinstance(cmd, UnspacedList)
            res.append([cmd, load_includes(arg, path)])
        else:
            res.append([cmd, arg])
    return res


def conf_apply_filter(
    conf: UnspacedList, func: t.Callable[[UnspacedList], UnspacedList]
) -> UnspacedList:
    res = UnspacedList([])
    for cmd, arg in func(conf):
        if isinstance(cmd, list) and isinstance(arg, UnspacedList):
            res.append([cmd, conf_apply_filter(arg, func)])
        else:
            res.append([cmd, arg])
    return res


def conf_apply_opt_filter(
    conf: UnspacedList,
    func: t.Callable[
        [_nginx_cmd_type, str | UnspacedList], _nginx_row_type | UnspacedList | None
    ],
    *opt_cmd: _nginx_cmd_type,
) -> UnspacedList:
    res = UnspacedList([])
    for cmd, arg in conf:
        if (
            not opt_cmd
            or cmd in opt_cmd
            or (isinstance(cmd, list) and cmd[0] in opt_cmd)
        ):
            row = func(cmd, arg)
            if row is None:
                continue
            if isinstance(row, UnspacedList):
                res.extend(row)
                continue
            cmd, arg = row
        if isinstance(cmd, list):
            res.append([cmd, conf_apply_opt_filter(arg, func, *opt_cmd)])
        else:
            res.append([cmd, arg])
    return res


def filter_comments(conf: UnspacedList, *opt_cmd: _nginx_cmd_type) -> UnspacedList:
    res = UnspacedList([])
    for cmd, arg in conf:
        # print(repr(cmd))
        if not (cmd == "#" or cmd in opt_cmd):
            res.append([cmd, arg])
    return res


def filter_all_comments(conf: UnspacedList, *opt_cmd: _nginx_cmd_type) -> UnspacedList:
    return conf_apply_filter(conf, lambda c: filter_comments(c, *opt_cmd))


def filter_out(conf: UnspacedList, *opt_cmd: _nginx_cmd_type) -> UnspacedList:
    def func(
        cmd: _nginx_cmd_type, arg: str | UnspacedList
    ) -> _nginx_row_type | UnspacedList | None:
        if cmd in opt_cmd or (isinstance(cmd, list) and cmd[0] in opt_cmd):
            return None
        return cmd, arg

    return conf_apply_opt_filter(conf, func)


def filter_only(conf: UnspacedList, *opt_cmd: _nginx_cmd_type) -> UnspacedList:
    def func(
        cmd: _nginx_cmd_type, arg: str | UnspacedList
    ) -> _nginx_row_type | UnspacedList | None:
        if cmd in opt_cmd or (isinstance(cmd, list) and cmd[0] in opt_cmd):
            return cmd, arg
        return None

    return conf_apply_opt_filter(conf, func)
