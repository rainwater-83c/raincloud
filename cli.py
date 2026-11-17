"""Command-line interface for Raincloud."""

import argparse

from .cli_tools.build import build_project
from .cli_tools.init import initialize_project


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="raincloud", description="Raincloud game engine")
    commands = parser.add_subparsers(dest="command", required=True)

    init_parser = commands.add_parser("init", help="create a game project")
    init_parser.add_argument("path", nargs="?", default=".", help="empty project directory")

    build_parser = commands.add_parser("build", help="build a game project")
    build_parser.add_argument("path", nargs="?", default=".", help="game project directory")
    build_parser.add_argument("-o", "--output", help="build output directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            destination = initialize_project(args.path)
            print(f"Created Raincloud project at {destination}")
        else:
            output = build_project(args.path, args.output)
            print(f"Built game distribution at {output}")
    except (FileExistsError, FileNotFoundError, RuntimeError, ValueError) as error:
        parser.error(str(error))
    return 0