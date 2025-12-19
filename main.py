# Splatlogger (c) 2025 Shadow Doggo.

import sys
import time
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.request import Request, urlopen

from tcpgecko import TCPGecko
from logger import Logger


def main():
    epic_fail = False

    if not auto_logging and logging_enabled:
        logger.new_match(gecko, auto_logging, session_adr, 1)

    if not silent_logging: print()

    main_mgr_base_adr = int.from_bytes(gecko.readmem(MAIN_MGR_BASE_PTR, 4), "big")

    if main_mgr_base_adr != 0:
        player_mgr_adr = int.from_bytes(gecko.readmem(main_mgr_base_adr + 0x268, 4), "big")
        player_count = int.from_bytes(gecko.readmem(player_mgr_adr + 0x323, 1), "big")
    else:
        player_count = 8
        if silent_logging: print()
        print(
            "You are currently not in a match. Logging previous match data"
            " (Player 1 data will be your own, Session ID will be the current one).\n"
        )

    for player_num in range(1, player_count + 1):
        player_idx = (player_num - 1) * 0x4
        player_info_adr = int.from_bytes(gecko.readmem(player_info_ary_adr + player_idx, 4), "big")

        player_dict = {"Number": player_num, "PlayerInfo": gecko.readmem(player_info_adr, 212)}

        player_dict["PID"] = int.from_bytes(player_dict["PlayerInfo"][0xD0:0xD4], "big")

        if player_dict["PID"] != 0:
            player_dict["PNID"] = ""
            player_dict["Name"] = (
                player_dict["PlayerInfo"][0x6:0x26]
                .decode("utf-16-be")
                .split("\u0000")[0]
                .replace("\n", "")
                .replace("\r", "")
            )

            req = Request(
                f"http://account.pretendo.cc/v1/api/miis?pids={player_dict['PID']}",
                headers={
                    "X-Nintendo-Client-ID": "a2efa818a34fa16b8afbc8a74eba3eda",
                    "X-Nintendo-Client-Secret": "c91cdb5658bd4954ade78533a339cf9a",
                },
            )  # Get user data from the account server.

            try:
                response = ET.fromstring(urlopen(req).read().decode("utf-8"))
                player_dict["PNID"] = response[0].find("user_id").text
                player_dict["Mii name"] = response[0].find("name").text.replace("\n", "").replace("\r", "")  # Always get the real mii name in case a player used name changer.
                player_dict["Mii icon"] = response[0].find("images").find("image").find("url").text
            except urllib.error.URLError:
                epic_fail = True

            if logging_enabled:
                logger.log(gecko, log_stats, player_dict)

            if not silent_logging:
                print(
                    f"Player {player_num} | "
                    f"PID: {player_dict['PID']:X} ({player_dict['PID']}) {' ' * 16 if player_dict['PID'] == 0 else ''}| "
                    f"PNID: {player_dict['PNID']} {' ' * (16 - len(player_dict['PNID']))}| "
                    f"Name: {player_dict['Name']} "
                    f"{'(' + player_dict['Mii name'] + ')' if player_dict['Name'] != player_dict['Mii name'] else ''}"
                )

    if not silent_logging:
        if epic_fail:
            print("Failed to get PNID for one or more players.")

        if not logging_enabled and session_adr != 0:
            session_id_idx = int.from_bytes(gecko.readmem(session_adr + 0xBD, 1), "big")
            session_id = int.from_bytes(gecko.readmem(session_adr + session_id_idx * 4 + 0xCC, 4), "big")

            print(f"\nSession ID: {session_id:X} ({session_id})")
        elif logging_enabled:  # Don't fetch the session ID again if it was fetched by the logger.
            print(f"\nSession ID: {logger.session_id:X} ({logger.session_id})")
        else:
            print("\nSession ID: None")

        print(f"\nFetched at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    logging_enabled = False
    silent_logging = False
    log_stats = False
    auto_logging = False
    logger = None

    print("Splatlogger v1.0 by Shadow Doggo\n")

    try:
        gecko = TCPGecko(sys.argv[1])
    except IndexError:
        print("No IP address was provided")
        exit()
    except OSError as ex:
        print(f"Failed to connect: {ex}")
        exit()

    STATIC_MEM_PTR = 0x106E0330
    SESSION_PTR = 0x106EB980
    SCENE_MGR_PTR = 0x106E9770
    MAIN_MGR_BASE_PTR = 0x106E5814

    static_mem_adr = int.from_bytes(gecko.readmem(STATIC_MEM_PTR, 4), "big")
    session_adr = int.from_bytes(gecko.readmem(SESSION_PTR, 4), "big")
    scene_mgr_adr = int.from_bytes(gecko.readmem(SCENE_MGR_PTR, 4), "big")
    player_info_ary_adr = int.from_bytes(gecko.readmem(static_mem_adr + 0x10, 4), "big")

    VALID_ARGS = ["log", "silent", "stats", "auto"]

    for arg in sys.argv[2:]:
        if arg not in VALID_ARGS:
            print(f"Invalid argument: {arg}")

    if len(sys.argv) > 2 and "log" in sys.argv[2:]:
        logging_enabled = True
        logger = Logger(static_mem_adr, scene_mgr_adr)
        logger.create_log()

    if len(sys.argv) > 2 and "silent" in sys.argv[2:]:
        silent_logging = True

    if len(sys.argv) > 2 and "stats" in sys.argv[2:]:
        log_stats = True

    if len(sys.argv) > 2 and "auto" in sys.argv[2:]:
        print("\nAuto logging enabled")

        if not logging_enabled:
            logging_enabled = True
            logger = Logger(static_mem_adr, scene_mgr_adr)
            logger.create_log()

        auto_logging = True
        match_in_progress = False
        count = 0

        while True:
            scene_id = int.from_bytes(gecko.readmem(scene_mgr_adr + 0x162, 2), "big")

            if scene_id != 7:
                match_in_progress = False

            if (
                not match_in_progress and scene_id == 7
            ):  # Trigger logging when scene changes to a vs match.
                match_in_progress = True
                session_adr = int.from_bytes(gecko.readmem(SESSION_PTR, 4), "big")
                count += 1

                logger.new_match(gecko, auto_logging, session_adr, count)

                if not silent_logging:
                    print(f"\nMatch {count}")

                main()

            time.sleep(10)

    main()
