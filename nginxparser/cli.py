import argparse
import pathlib
import nginxparser.process
import nginxparser.nginxparser


def main():
    parser = argparse.ArgumentParser(
        description="Parse nginx config, optionally filter it and reindents"
    )
    parser.add_argument(
        "--skip-comments",
        "-c",
        dest="comments",
        action="store_const",
        const=False,
        default=True,
        help="Strip comments from output",
    )
    parser.add_argument(
        "--structure",
        "-s",
        action="store_const",
        const=True,
        default=False,
        help="Show paths to loaded configuration files",
    )
    parser.add_argument(
        "--minimal",
        "-m",
        action="store_const",
        const=True,
        default=False,
        help="Show only directives listen/server_name/server_name/root/proxy_pass (don't forget -c)",
    )
    parser.add_argument(
        "--skip-dummy",
        "-d",
        dest="dummy",
        action="store_const",
        const=False,
        default=True,
        help="Skip several directives (types/events/load_module) from garbaging output"
        + " (ignored with -m)",
    )
    parser.add_argument(
        "path", nargs="?", type=pathlib.Path, default="/etc/nginx/nginx.conf"
    )
    ns = parser.parse_args()
    cfg = nginxparser.process.load_path(ns.path)
    if ns.minimal:
        opt_cmd = [
            "http",
            "server",
            "location",
            "listen",
            "if",
            "server_name",
            "root",
            "proxy_pass",
        ]
        if ns.structure:
            opt_cmd.append("##")
        if ns.comments:
            opt_cmd.append("#")
        cfg = nginxparser.process.filter_only(cfg, *opt_cmd)
    else:
        opt_cmd = []
        if not ns.structure:
            opt_cmd.append("##")
        if not ns.comments:
            opt_cmd.append("#")
        if not ns.dummy:
            opt_cmd.extend([["types"], "load_module", ["events"]])
        if opt_cmd:
            cfg = nginxparser.process.filter_out(cfg, *opt_cmd)
    print(nginxparser.nginxparser.dumps(cfg))
