# Splatlogger (c) 2025 Shadow Doggo.

import sys
import time
import urllib.error
import xml.etree.ElementTree as ElementTree
from datetime import datetime
from urllib.request import Request, urlopen

from data import Pointers, Offsets, PlayerInfo
from match_logger import MatchLogger
from tcpgecko import TCPGecko
from tcpgecko_aroma import TCPGeckoAroma

_VERSION: str = "1.4a"


def main(args: list[str]) -> None:
    """Arguments:
    log - Write full match log to file.

    silent - Enable silent logging (don't print logs to console).

    stats - Enable logging of player stats (points, kills, deaths, win/loss). Requires the match to complete to finish logging, also makes logging slower.

    auto - Enable auto logging. When enabled will automatically log every match you play.

    auto-latest - Same as above but will save only the latest match you played.

    aroma - Enable aroma mode. Compatible with TCPGeckoAroma.
    """

    def splatlog(match_count: int) -> None:
        request_fail: bool = False
        session_id: int = 0
        player_count: int = 8  # Default to 8 to log all players from the last match.
        main_mgr_base_adr: int = gecko.peek32(Pointers.MAIN_MGR_BASE)
        player_info_list: list[PlayerInfo] = []

        if session_adr != 0:
            session_id_idx: int = int.from_bytes(gecko.peek_raw(
                session_adr + Offsets.SESSION_IDX, length=0x1), byteorder="big"
            )
            session_id = gecko.peek32(session_adr + session_id_idx * 4 + Offsets.SESSION_ID)

        if main_mgr_base_adr != 0:
            player_mgr_adr: int = gecko.peek32(main_mgr_base_adr + Offsets.PLAYER_MGR)
            if player_mgr_adr != 0:
                player_count = gecko.peek8(player_mgr_adr + Offsets.PLAYER_COUNT)
        else:
            print(
                "You are currently not in a match. Logging previous match data "
                "(Player 1 data will be your own, Session ID will be the current one).\n"
            )

        player_idx: int
        for player_idx in range(player_count):
            player_info_adr: int = gecko.peek32(player_info_ary_adr + player_idx * 0x4)
            player_info_raw: bytes = gecko.peek_raw(player_info_adr, length=0xD4)

            player_pid: int = int.from_bytes(player_info_raw[0xD0:0xD4], byteorder="big")
            if player_pid != 0:
                player_name: str = (player_info_raw[0x6:0x26]
                                    .decode("utf-16-be")
                                    .split("\u0000")[0]
                                    .replace("\n", "")
                                    .replace("\r", ""))

                player_pnid: str = ""
                player_mii_name: str = ""
                req: Request = Request(f"https://account.pretendo.cc/v1/api/miis?pids={player_pid}",
                                       headers={"X-Nintendo-Client-ID": "a2efa818a34fa16b8afbc8a74eba3eda",
                                                "X-Nintendo-Client-Secret": "c91cdb5658bd4954ade78533a339cf9a"})
                try:
                    response: ElementTree.Element[str] = ElementTree.fromstring(urlopen(req)
                                                                                .read()
                                                                                .decode("utf-8"))
                    assert (isinstance(response[0].find("user_id"), ElementTree.Element) and
                            isinstance(response[0].find("name"), ElementTree.Element))
                    player_pnid = response[0].find("user_id").text  # type: ignore
                    player_mii_name = (response[0].find("name")  # type: ignore
                                       .text
                                       .replace("\n", "")
                                       .replace("\r", ""))
                except (urllib.error.URLError, AssertionError):
                    request_fail = True

                if logging_enabled:
                    player_info: PlayerInfo = PlayerInfo(
                        index=player_idx,
                        pid=player_pid,
                        pnid=player_pnid,
                        name=player_name,
                        mii_name=player_mii_name,
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

                if not silent_logging:
                    print(
                        f"Player {player_idx + 1} | "
                        f"PID: {player_pid:X} ({player_pid}) {' ' * 16 if player_pid == 0 else ''}| "
                        f"PNID: {player_pnid} {' ' * (16 - len(player_pnid))}| "
                        f"Name: {player_name}"
                        f"{' (Mii name: ' + player_mii_name + ')' if player_name != player_mii_name else ''}"
                    )

        if logging_enabled:
            match_logger.log_match(session_id, match_count, player_info_list)

        if not silent_logging:
            print()
            if request_fail:
                print("Failed to get account data for one or more players.\n")

            if session_id != 0:
                print(f"Session ID: {session_id:X} ({session_id})\n")
            else:
                print("Session ID: None\n")

            print(f"Fetched at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Main driver code.
    logging_enabled: bool = False
    silent_logging: bool = False
    log_stats: bool = False
    auto_logging: bool = False
    log_latest: bool = False
    aroma: bool = False

    print(f"Splatlogger v{_VERSION} by Shadow Doggo\n")

    if len(args) > 1:
        arg: str
        for arg in args[1:]:
            match arg:
                case "log":
                    logging_enabled = True
                case "silent":
                    silent_logging = True
                case "stats":
                    log_stats = True
                case "auto":
                    logging_enabled = True
                    auto_logging = True
                case "auto-latest":
                    logging_enabled = True
                    auto_logging = True
                    log_latest = True
                case "aroma":
                    aroma = True
                case _:
                    print(f"Invalid argument: {arg}")

    gecko: TCPGecko
    try:
        print(f"Connecting to: {args[0]}")
        gecko = TCPGeckoAroma(args[0]) if aroma else TCPGecko(args[0])
    except IndexError:
        print("No IP address was provided.")
        exit()
    except OSError as e:
        print(f"Failed to connect: {e}")
        exit()

    try:  # Check if any data can be received. This will fail if something else is connected.
        gecko.peek_raw(Pointers.STATIC_MEM, length=0x1)
        print("Connected.\n")
    except TimeoutError:
        print("Connection timed out.")
        exit()

    static_mem_adr: int = gecko.peek32(Pointers.STATIC_MEM)
    session_adr: int = gecko.peek32(Pointers.SESSION)
    player_info_ary_adr: int = gecko.peek32(static_mem_adr + Offsets.PLAYER_INFO_ARY)

    match_logger: MatchLogger
    if logging_enabled and not auto_logging:
        match_logger = MatchLogger(gecko, auto_logging, log_stats, aroma, static_mem_adr)
        try:  # This should catch any permission issues.
            match_logger.create_new_log()
        except OSError as e:
            print(f"Failed to create log file: {e}")
            exit()

    if auto_logging:
        print("Auto logging enabled.")

        match_logger = MatchLogger(gecko, auto_logging, log_stats, aroma, static_mem_adr)
        try:
            match_logger.create_new_log()
        except OSError as e:
            print(f"Failed to create log file: {e}")
            exit()

        match_in_progress: bool = False
        count: int = 0
        while True:
            try:
                main_mgr_vs_game_adr: int = gecko.peek32(Pointers.MAIN_MGR_VS_GAME)
                if main_mgr_vs_game_adr == 0:
                    match_in_progress = False

                if not match_in_progress and main_mgr_vs_game_adr != 0:  # Trigger logging when MainMgrVSGame is loaded.
                    match_in_progress = True
                    session_adr = gecko.peek32(Pointers.SESSION)
                    count += 1

                    if log_latest:
                        match_logger.create_new_log()

                    if not silent_logging:
                        print(f"\nMatch {count}\n")

                    time.sleep(1)
                    splatlog(count)

                time.sleep(10)
            except KeyboardInterrupt:
                print("\nExiting.")
                break

    if not auto_logging:
        splatlog(match_count=1)


if __name__ == "__main__":
    main(sys.argv[1:])
