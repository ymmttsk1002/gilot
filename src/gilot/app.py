
import sys
import json
import argparse
from fnmatch import fnmatch
import gilot
from typing import Callable,List,Optional
from gilot import Duration

parser = argparse.ArgumentParser(description="""
gilot is a tool for analyzing and visualizing git logs

1) simple way (1 liner using pipe)
! gilot log REPO_DIR | gilot plot

2) 2-phase way
! gilot log REPO_DIR > repo.csv
! gilot plot -i repo.csv -o graph.png


""", formatter_class=argparse.RawDescriptionHelpFormatter)  # type:ignore


def compose_filter(allow: Optional[List[str]], deny: Optional[List[str]]) -> Callable[[str], bool]:
    allow_list = allow or []
    deny_list = deny or []

    def match(file_name: str) -> bool:
        # いずれかのallow条件にmatchするか
        is_allowed = any(fnmatch(file_name, p) for p in allow_list)
        # いずれかのdeny条件にmatchするか
        is_denyed = any(fnmatch(file_name, p) for p in deny_list)
        # 許可されており、拒否リストに含まれていない。
        return (is_allowed and not is_denyed)

    return match


def args_to_duration(args) -> Duration:

    if (args.since and args.until):
        return Duration.range(args.since, args.until)
    if (args.since and args.month):
        return Duration.months(int(args.month),since=args.since)
    if (args.since):
        return Duration.from_now(args.since)
    if (args.month):
        return Duration.months(int(args.month))
    return Duration.months(6)


def handle_log(args):
    duration = args_to_duration(args)
    df = gilot.from_dir(
        args.repo,
        branch=args.branch,
        duration=duration,
        full=args.full
    )
    df.to_csv(args.output)


def handle_plot(args):
    df = gilot.from_csvs(args.input)
    if (args.allow_files or args.deny_files):
        df = gilot.filter_files(df,compose_filter(allow=args.allow_files,deny=args.ignore_files))

    gilot.plot(df, output=args.output, name=args.name, timeslot=args.timeslot)


def handle_info(args):
    df = gilot.from_csvs(args.input)
    print(json.dumps(gilot.info(df), indent=4, sort_keys=False))


subparsers = parser.add_subparsers()

# log コマンドの parser を作成
parser_log = subparsers.add_parser(
    'log', help='make git log csv data/ see `log -h`')

parser_log.add_argument(
    'repo',
    help='REPO must be a root dir of git repository')

parser_log.add_argument(
    "-b", "--branch",
    help="target branch name. default 'origin/HEAD' ",
    default="origin/HEAD")

parser_log.add_argument(
    "-o", "--output",
    default=sys.__stdout__)

parser_log.add_argument(
    "--since",
    help="SINCE must be ISO format like 2020-01-01.")

parser_log.add_argument(
    "--until",
    help="UNTIL must be ISO format like 2020-06-01.")

parser_log.add_argument(
    "--full",
    action="store_true",
    help="UNTIL must be ISO format like 2020-06-01.")

parser_log.add_argument(
    "--month",
    help="MONTH is how many months of log data to output. default is 6")

parser_log.set_defaults(handler=handle_log)

# plot コマンドの parser を作成
parser_plot = subparsers.add_parser(
    'plot', help='plot graph using the csv file see `plot -h`')

parser_plot.add_argument(
    '-i', "--input",
    nargs="*",
    default=[sys.__stdin__])

parser_plot.add_argument(
    "--allow-files",
    nargs="*")

parser_plot.add_argument(
    "--ignore-files",
    nargs="*")

parser_plot.add_argument(
    '-t', "--timeslot",
    help="resample period like 2W or 7D or 1M ",
    default="2W")
parser_plot.add_argument(
    '-o', "--output",
    default=False,
    help="OUTPUT FILE ")
parser_plot.add_argument(
    "-n", "--name",
    default="GIT LOG REPORT",
    help="name")

parser_plot.set_defaults(handler=handle_plot)

# info コマンドの parser を作成
parser_info = subparsers.add_parser(
    'info', help='plot graph using the csv file see `info -h`')

parser_info.add_argument(
    '-i', "--input",
    nargs="*",
    default=[sys.__stdin__])

parser_info.add_argument(
    '-t', "--timeslot",
    help="resample period like 2W or 7D or 1M ",
    default="2W")

parser_info.set_defaults(handler=handle_info)


def main():
    # コマンドライン引数をパースして対応するハンドラ関数を実行
    args = parser.parse_args()
    if hasattr(args, 'handler'):
        args.handler(args)
    else:
        # 未知のサブコマンドの場合はヘルプを表示
        parser.print_help()


if __name__ == "__main__":
    main()
