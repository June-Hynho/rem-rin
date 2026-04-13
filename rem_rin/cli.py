#-----------------------
# FULLY_AI_GENERATED
#-----------------------
import argparse
import asyncio
from typing import Optional

import aiohttp

from rem_rin.kaido import KaidoClient

from rem_rin import APP_NAME

from rem_rin.handler import *

# -----------------------
# PARSER
# -----------------------
def build_parser():
    parser = argparse.ArgumentParser(prog=APP_NAME)
    sub = parser.add_subparsers(dest="command", required=True)

    # -------- SEARCH --------
    search = sub.add_parser("search")
    search.add_argument("query")

    # -------- DOWNLOAD --------
    download = sub.add_parser("download")
    dl_sub = download.add_subparsers(dest="mode", required=True)

    dl_id = dl_sub.add_parser("id")
    dl_id.add_argument("value", type=int)

    dl_search = dl_sub.add_parser("search")
    dl_search.add_argument("query")

    for p in (dl_id, dl_search):
        p.add_argument("--episodes", "-e")
        p.add_argument("--no-confirm", "-y", action="store_true")
        p.add_argument("--dub", action="store_true")
        p.add_argument("--quality", "-q", type=int, default = 1080)
        p.add_argument("--destination", "-d", default = '.')

    # -------- INFO --------
    info = sub.add_parser("info")
    info_sub = info.add_subparsers(dest="mode", required=True)

    info_id = info_sub.add_parser("id")
    info_id.add_argument("value", type=int)

    info_search = info_sub.add_parser("search")
    info_search.add_argument("query")

    # -------- LIST EPISODES --------
    eps = sub.add_parser("list-episodes")
    eps_sub = eps.add_subparsers(dest="mode", required=True)

    eps_id = eps_sub.add_parser("id")
    eps_id.add_argument("value", type=int)

    eps_search = eps_sub.add_parser("search")
    eps_search.add_argument("query")

    for p in (eps_id, eps_search):
        p.add_argument("--limit", "-l", type=int)
        p.add_argument("--reverse", "-r", action="store_true")

    return parser




# -----------------------
# MAIN
# -----------------------
async def main():
    parser = build_parser()
    args = parser.parse_args()

    async with aiohttp.ClientSession() as session:
        client = KaidoClient(session)

        if args.command == "search":
            await handle_search(client, args.query)

        elif args.command == "download":
            if args.mode == "id":
                await handle_download_id(client, args)
            else:
                await handle_download_search(client, args)

        elif args.command == "info":
            if args.mode == "id":
                await handle_info_id(client, args.value)
            else:
                await handle_info_search(client, args.query)

        elif args.command == "list-episodes":
            if args.mode == "id":
                await handle_eps_id(client, args)
            else:
                await handle_eps_search(client, args)

def run():
    asyncio.run(main())

if __name__ == "__main__":
    run()
