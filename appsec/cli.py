import asyncio
import traceback
import argparse

from rich.style import Style
from rich import print as rprint

from .appsec import main


def cli():
    parser = argparse.ArgumentParser(prog="appsec", description="AppSec PR requestor")
    parser.add_argument('--repo', help='The GitHub repo to which the commit(s) belong')
    parser.add_argument('--from_event', help='The source commit SHA or tag to compare from')
    parser.add_argument('--to_event', help='The target commit SHA or tag to compare against', required=True)

    args = parser.parse_args()

    try:
        asyncio.run(
            main(
                repo=args.repo,
                to_event=args.to_event,
                from_event=args.from_event,
            )
        )
    except Exception as e:
        print(traceback.format_exc())
        rprint(f":x: {str(e)}", Style(color="red", bold=False, underline=True))
        exit(1)
