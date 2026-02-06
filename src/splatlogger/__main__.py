# Splatlogger (c) 2025 Shadow Doggo.

import argparse
import ipaddress
import os
import sys
import time
import xml.etree.ElementTree as ElementTree
from datetime import datetime
from typing import NamedTuple

import requests
import userpaths  # type: ignore[import-untyped]

from .data import Pointers, Offsets, PlayerInfo
from .match_logger import MatchLogger
from .tcpgecko import TCPGecko, TCPGeckoException
from .tcpgecko_aroma import TCPGeckoAroma

_VERSION: str = "1.5.2"


class Options(NamedTuple):
    log_level: str
    auto_logging: bool
    log_latest: bool
    silent_logging: bool
    aroma: bool


class AccountInfo(NamedTuple):
    pnid: str
    mii_name: str
    request_error: str


def main() -> None:
    print(f"Splatlogger v{_VERSION} by Shadow Doggo\n")

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="A PID/PNID grabber and match logger for Splatoon using TCPGecko."
    )
    parser.add_argument("-ip", help="Your Wii U's LAN IP address.", required=True)
    parser.add_argument("-log-level", help="Set how much data should be logged (see README).",
                        choices=["none", "basic", "full", "stats"], nargs="?", const="none", default="none")
    parser.add_argument("-auto",
                        help="Enable auto logging (all to log every match, latest to only log the latest match).",
                        choices=["all", "latest"], nargs="?", const="all")
    parser.add_argument("-aroma", help="Enable Aroma mode.", action="store_true")
    parser.add_argument("-silent", help="Disable printing logs to the console.", action="store_true")

    args: argparse.Namespace
    if os.path.isfile(f"{userpaths.get_my_documents()}/Splatlogger/args.txt"):
        with open(f"{userpaths.get_my_documents()}/Splatlogger/args.txt", encoding="utf-8") as f:
            args = parser.parse_args(f.read().split())
    else:
        args = parser.parse_args()

    options: Options = Options(log_level=args.log_level,
                               auto_logging=args.auto in ("all", "latest"),
                               log_latest=args.auto == "latest",
                               silent_logging=args.silent,
                               aroma=args.aroma)

    gecko: TCPGecko
    try:
        ipaddress.ip_address(args.ip)
        print(f"Connecting to: {args.ip}")
        gecko = TCPGeckoAroma(args.ip) if options.aroma else TCPGecko(args.ip)
    except ValueError:
        print("Please provide a valid IP address.\nExiting.")
        sys.exit()
    except OSError as e:
        print(f"Failed to connect: {e}\nExiting.")
        sys.exit()

    static_mem_adr: int = 0
    player_info_ary_adr: int = 0
    for _ in range(3):
        try:
            static_mem_adr = gecko.peek32(Pointers.STATIC_MEM)
            player_info_ary_adr = gecko.peek32(static_mem_adr + Offsets.PLAYER_INFO_ARY)
            print("Connected.\n")
            break
        except (OSError, TimeoutError, TCPGeckoException) as e:
            print(f"\nAn error has occurred: {e}\nRetrying in 10 seconds...")
            time.sleep(10)
    else:
        print("\nFailed after 3 tries.\nExiting.")
        sys.exit()

    match_logger: MatchLogger | None = None
    if options.log_level != "none":
        match_logger = MatchLogger(gecko, options.log_level, options.auto_logging, options.aroma, static_mem_adr)
        try:
            match_logger.create_new_log()
        except OSError as e:
            print(f"Failed to create log file: {e}\nExiting.")
            sys.exit()

    if options.auto_logging and match_logger is not None:
        print("Auto logging enabled.")
        _auto_log(options, gecko, match_logger, player_info_ary_adr)

    for _ in range(3):
        try:
            _splatlog(options, gecko, match_logger, player_info_ary_adr, match_count=1)
            break
        except (OSError, TimeoutError, TCPGeckoException) as e:
            print(f"\nAn error has occurred: {e}\nRetrying in 10 seconds...")
            time.sleep(10)
    else:
        print("\nFailed after 3 tries.\nExiting.")
        sys.exit()


def _auto_log(options: Options, gecko: TCPGecko, match_logger: MatchLogger,
              player_info_ary_adr: int) -> None:
    match_in_progress: bool = False
    count: int = 0
    retry_count: int = 0
    while True:
        try:
            main_mgr_vs_game_adr: int = gecko.peek32(Pointers.MAIN_MGR_VS_GAME)
            if main_mgr_vs_game_adr == 0:
                match_in_progress = False

            if not match_in_progress and main_mgr_vs_game_adr != 0:  # Trigger logging when a VS match is loaded.
                match_in_progress = True
                count += 1

                if options.log_latest:
                    match_logger.create_new_log()

                if not options.silent_logging:
                    print(f"\nMatch {count}\n")

                time.sleep(1)
                for _ in range(3):
                    try:
                        _splatlog(options, gecko, match_logger, player_info_ary_adr, count)
                        break
                    except (OSError, TimeoutError, TCPGeckoException) as e:
                        print(f"\nAn error has occurred: {e}\nRetrying in 10 seconds...")
                        time.sleep(10)
                else:
                    print("\nFailed after 3 tries.\nExiting.")
                    sys.exit()

            retry_count = 0
            time.sleep(10)
        except KeyboardInterrupt:
            print("\nExiting.")
            sys.exit()
        except (OSError, TimeoutError, TCPGeckoException) as e:
            if retry_count < 3:
                print(f"\nAn error has occurred: {e}\nRetrying in 10 seconds...")
                retry_count += 1
                time.sleep(10)
            else:
                print("\nFailed after 3 tries.\nExiting.")
                sys.exit()


def _splatlog(options: Options, gecko: TCPGecko, match_logger: MatchLogger | None,
              player_info_ary_adr: int, match_count: int) -> None:
    session_id: int = 0
    player_count: int = 8
    request_errors: list[str] = []
    player_info_list: list[PlayerInfo] = []

    session_adr = gecko.peek32(Pointers.SESSION)
    if session_adr != 0:
        session_id_idx: int = int.from_bytes(gecko.peek_raw(session_adr + Offsets.SESSION_ID_IDX,
                                                            length=0x1), byteorder="big")
        session_id = gecko.peek32(session_adr + session_id_idx * 4 + Offsets.SESSION_ID)

    main_mgr_base_adr: int = gecko.peek32(Pointers.MAIN_MGR_BASE)
    if main_mgr_base_adr != 0 and gecko.peek8(Pointers.MAIN_MGR_VS_GAME) != 0:
        player_mgr_adr: int = gecko.peek32(main_mgr_base_adr + Offsets.PLAYER_MGR)
        if player_mgr_adr != 0:
            player_count = gecko.peek8(player_mgr_adr + Offsets.PLAYER_COUNT)
    else:
        print("You are currently not in a match. Logging previous match data "
              "(Player 1 data will be your own, Session ID will be the current one).\n")

    player_idx: int
    for player_idx in range(player_count):
        player_info_raw: bytes = gecko.peek_raw(gecko.peek32(player_info_ary_adr + player_idx * 0x4),
                                                length=0xD4)

        player_pid: int = int.from_bytes(player_info_raw[0xD0:0xD4], byteorder="big")
        if player_pid != 0:
            player_name: str = (player_info_raw[0x6:0x26]
                                .decode("utf-16-be")
                                .split("\u0000")[0]
                                .replace("\n", "")
                                .replace("\r", ""))

            act_info: AccountInfo = _get_act_info(player_pid)
            if act_info.request_error != "":
                request_errors.append(act_info.request_error)

            if options.log_level != "none":
                player_info: PlayerInfo = PlayerInfo(
                    idx=player_idx,
                    pid=player_pid,
                    pnid=act_info.pnid,
                    name=player_name,
                    mii_name=act_info.mii_name,
                    region=int.from_bytes(player_info_raw[0x2C:0x30], byteorder="big"),
                    team=int.from_bytes(player_info_raw[0x33:0x34], byteorder="big"),
                    gender=int.from_bytes(player_info_raw[0x37:0x38], byteorder="big"),
                    skin_tone=int.from_bytes(player_info_raw[0x3B:0x3C], byteorder="big"),
                    eye_color=int.from_bytes(player_info_raw[0x3F:0x40], byteorder="big"),
                    weapon=int.from_bytes(player_info_raw[0x46:0x48], byteorder="big"),
                    sub_weapon=int.from_bytes(player_info_raw[0x4A:0x4C], byteorder="big"),
                    special_weapon=int.from_bytes(player_info_raw[0x4D:0x50], byteorder="big"),
                    shoes=int.from_bytes(player_info_raw[0x54:0x58], byteorder="big"),
                    clothes=int.from_bytes(player_info_raw[0x70:0x74], byteorder="big"),
                    headgear=int.from_bytes(player_info_raw[0x8C:0x90], byteorder="big"),
                    level=int.from_bytes(player_info_raw[0xAF:0xB0], byteorder="big", signed=True) + 1,
                    rank=int.from_bytes(player_info_raw[0xB3:0xB4], byteorder="big", signed=True)
                )
                player_info_list.append(player_info)

            if not options.silent_logging:
                print(f"Player {player_idx + 1} | "
                      f"PID: {player_pid:X} ({player_pid}) {' ' * 16 if player_pid == 0 else ''}| "
                      f"PNID: {act_info.pnid} {' ' * (16 - len(act_info.pnid))}| "
                      f"Name: {player_name}"
                      f"{' (Mii name: ' + act_info.mii_name + ')' if player_name != act_info.mii_name else ''}")

    if not options.silent_logging:
        print()
        if request_errors:
            print("Failed to get account data for one or more players: "
                  f"{'; '.join(request_errors)}\n")

        if session_id != 0:
            print(f"Session ID: {session_id:X} ({session_id})")
        else:
            print("Session ID: None")

        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if options.log_level != "none" and match_logger is not None:
        match_logger.log_match(session_id, match_count, player_info_list)


def _get_act_info(player_pid: int) -> AccountInfo:
    pnid: str = ""
    mii_name: str = ""
    request_error: str = ""

    for _ in range(3):
        try:
            response: requests.Response = requests.get(
                f"https://account.pretendo.cc/v1/api/miis?pids={player_pid}",
                headers={"X-Nintendo-Client-ID": "a2efa818a34fa16b8afbc8a74eba3eda",
                         "X-Nintendo-Client-Secret": "c91cdb5658bd4954ade78533a339cf9a"},
                timeout=10
            )

            root: ElementTree.Element[str] = ElementTree.fromstring(response.text)
            assert (isinstance(root[0].find("user_id"), ElementTree.Element) and
                    isinstance(root[0].find("name"), ElementTree.Element))
            pnid = root[0].find("user_id").text  # type: ignore
            mii_name = (root[0].find("name")  # type: ignore
                               .text
                               .replace("\n", "")
                               .replace("\r", ""))
            break
        except (requests.HTTPError, AssertionError) as ex:
            request_error = str(ex)
            time.sleep(1)

    return AccountInfo(pnid, mii_name, request_error)


if __name__ == "__main__":
    main()
