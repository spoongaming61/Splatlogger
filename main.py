# Splatlogger (c) 2025 Shadow Doggo.

import sys
import time
import urllib.error
import xml.etree.ElementTree as ElementTree
from datetime import datetime
from urllib.request import Request, urlopen

from tcpgecko import TCPGecko
from tcpgecko_aroma import TCPGeckoAroma
from logger import Logger, PlayerDict

_VERSION: str = "1.4"
_VALID_ARGS: list[str] = ["log", "silent", "stats", "auto", "auto-latest", "aroma"]
STATIC_MEM_PTR: int = 0x106E0330
SESSION_PTR: int = 0x106EB980
SCENE_MGR_PTR: int = 0x106E9770
MAIN_MGR_BASE_PTR: int = 0x106E5814
PLAYER_INFO_ARY_OFFSET: int = 0x10
PLAYER_MGR_OFFSET: int = 0x268
PLAYER_COUNT_OFFSET: int = 0x323
SESSION_IDX_OFFSET: int = 0xBD
SESSION_ID_OFFSET: int = 0xCC
SCENE_ID_OFFSET: int = 0x162


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
        epic_fail: bool = False
        session_id: int = 0
        player_count: int = 8  # Default to 8 to log all players from the last match.
        main_mgr_base_adr: int = int.from_bytes(gecko.readmem(MAIN_MGR_BASE_PTR, length=0x4), byteorder="big")

        if session_adr != 0:
            session_id_idx: int = int.from_bytes(gecko.readmem(
                session_adr + SESSION_IDX_OFFSET, length=0x1), byteorder="big"
            )
            session_id = int.from_bytes(gecko.readmem(
                session_adr + session_id_idx * 4 + SESSION_ID_OFFSET, length=0x4), byteorder="big"
            )

        if main_mgr_base_adr != 0:
            player_mgr_adr: int = int.from_bytes(
                gecko.readmem(main_mgr_base_adr + PLAYER_MGR_OFFSET, length=0x4), byteorder="big"
            )
            player_count = int.from_bytes(
                gecko.readmem(player_mgr_adr + PLAYER_COUNT_OFFSET, length=0x1), byteorder="big"
            )
        else:
            print(
                "You are currently not in a match. Logging previous match data"
                " (Player 1 data will be your own, Session ID will be the current one).\n"
            )

        player_num: int
        for player_num in range(1, player_count + 1):
            player_idx: int = (player_num - 1) * 0x4
            player_info_adr: int = int.from_bytes(
                gecko.readmem(player_info_ary_adr + player_idx, length=0x4), byteorder="big"
            )
            player_info: bytes = gecko.readmem(player_info_adr, length=0xD4)
            player_pid: int = int.from_bytes(player_info[0xD0:0xD4], byteorder="big")

            if player_pid != 0:
                player_name: str = (
                    player_info[0x6:0x26]
                    .decode("utf-16-be")
                    .split("\u0000")[0]
                    .replace("\n", "")
                    .replace("\r", "")
                )

                # Get user data from the account server.
                player_pnid: str = ""
                player_mii_name: str = ""
                req: Request = Request(
                    f"http://account.pretendo.cc/v1/api/miis?pids={player_pid}",
                    headers={
                        "X-Nintendo-Client-ID": "a2efa818a34fa16b8afbc8a74eba3eda",
                        "X-Nintendo-Client-Secret": "c91cdb5658bd4954ade78533a339cf9a",
                    },
                )
                try:
                    response: ElementTree.Element[str] = ElementTree.fromstring(
                        urlopen(req)
                        .read()
                        .decode("utf-8")
                    )
                    player_pnid = response[0].find("user_id").text  # type: ignore
                    player_mii_name = (
                        response[0].find("name")  # type: ignore
                        .text
                        .replace("\n", "")
                        .replace("\r", "")
                    )  # Always get the real mii name in case a player used name changer.
                except urllib.error.URLError:
                    epic_fail = True

                if logging_enabled:
                    player_dict: PlayerDict = {
                        "number": player_num, "player_info": player_info,
                        "pid": player_pid, "pnid": player_pnid,
                        "name": player_name, "mii_name": player_mii_name
                    }

                    logger.log_match(session_id, match_count, player_dict)

                if not silent_logging:
                    print(
                        f"Player {player_num} | "
                        f"PID: {player_pid:X} ({player_pid}) {' ' * 16 if player_pid == 0 else ''}| "
                        f"PNID: {player_pnid} {' ' * (16 - len(player_pnid))}| "
                        f"Name: {player_name}"
                        f"{' (Mii name: ' + player_mii_name + ')' if player_name != player_mii_name else ''}"
                    )

        if not silent_logging:
            print()
            if epic_fail:
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
            if arg not in _VALID_ARGS:
                print(f"Invalid argument: {arg}")

        if "silent" in args[1:]:
            silent_logging = True

        if "stats" in args[1:]:
            log_stats = True

        if "log" in args[1:]:
            logging_enabled = True

        if "auto" in args[1:]:
            logging_enabled = True
            auto_logging = True

        if "auto-latest" in args[1:]:
            logging_enabled = True
            auto_logging = True
            log_latest = True

        if "aroma" in args[1:]:
            aroma = True

    try:
        print(f"Connecting to: {args[0]}")
        gecko: TCPGecko
        if aroma:
            gecko = TCPGeckoAroma(ip=args[0], port=7332, timeout=10)
        else:
            gecko = TCPGecko(ip=args[0], port=7331, timeout=10)
    except IndexError:
        print("No IP address was provided.")
        exit()
    except OSError as e:
        print(f"Failed to connect: {e}")
        exit()

    try:  # Check if any data can be received. This will fail if something else is connected.
        gecko.readmem(STATIC_MEM_PTR, length=0x1)
        print("Connected.\n")
    except TimeoutError:
        print("Connection timed out.")
        exit()

    static_mem_adr: int = int.from_bytes(gecko.readmem(STATIC_MEM_PTR, length=0x4), byteorder="big")
    session_adr: int = int.from_bytes(gecko.readmem(SESSION_PTR, length=0x4), byteorder="big")
    scene_mgr_adr: int = int.from_bytes(gecko.readmem(SCENE_MGR_PTR, length=0x4), byteorder="big")
    player_info_ary_adr: int = int.from_bytes(
        gecko.readmem(static_mem_adr + PLAYER_INFO_ARY_OFFSET, length=0x4), byteorder="big"
    )

    logger: Logger
    if logging_enabled and not auto_logging:
        logger = Logger(gecko, auto_logging, log_stats, aroma, static_mem_adr, scene_mgr_adr)
        try:  # This should catch any permission issues.
            logger.create_new_log()
        except OSError as e:
            print(f"Failed to create log file: {e}")
            exit()

    if auto_logging:
        print("Auto logging enabled.")

        logger = Logger(gecko, auto_logging, log_stats, aroma, static_mem_adr, scene_mgr_adr)
        try:
            logger.create_new_log()
        except OSError as e:
            print(f"Failed to create log file: {e}")
            exit()

        match_in_progress: bool = False
        count: int = 0
        while True:
            try:
                scene_id: int = int.from_bytes(
                    gecko.readmem(scene_mgr_adr + SCENE_ID_OFFSET, length=0x2), byteorder="big"
                )
                if scene_id != 7:
                    match_in_progress = False

                if (
                    not match_in_progress and scene_id == 7
                ):  # Trigger logging when scene changes to a vs match.
                    match_in_progress = True
                    session_adr = int.from_bytes(gecko.readmem(SESSION_PTR, length=0x4), byteorder="big")
                    count += 1

                    if log_latest:
                        logger.create_new_log()

                    if not silent_logging:
                        print(f"\nMatch {count}\n")

                    time.sleep(1)  # Wait a bit after the scene changes for the match to load.
                    splatlog(match_count=count)

                time.sleep(10)
            except KeyboardInterrupt:
                print("\nExiting.")
                break

    if not auto_logging:
        splatlog(match_count=1)


if __name__ == "__main__":
    main(sys.argv[1:])
