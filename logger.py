# Splatlogger (c) 2025 Shadow Doggo.

import os
import time
from datetime import datetime
from typing import TypedDict

from tcpgecko import TCPGecko
import names


class PlayerDict(TypedDict):
    number: int
    player_info: bytes
    pid: int
    pnid: str
    name: str
    mii_name: str


class Logger:
    """Provides the logging functionality of Splatlogger."""

    STATS_ADR: int = 0x107AF944  # A bunch of data including player stats. I'm not exactly sure what this is, but it works.
    WIN_TEAM_ADR: int = 0x107AF917
    MATCH_HOUR_OFFSET: int = 0x237
    VERSUS_MODE_OFFSET: int = 0x23B
    VERSUS_RULE_OFFSET: int = 0x23F
    STAGE_OFFSET: int = 0x28
    SCENE_ID_OFFSET: int = 0x162

    def __init__(
        self, gecko: TCPGecko, auto_logging: bool, log_stats: bool, aroma: bool, static_mem_adr: int, scene_mgr_adr: int
    ) -> None:
        self._gecko: TCPGecko = gecko
        self._auto_logging: bool = auto_logging
        self._log_stats: bool = log_stats
        self._static_mem_adr: int = static_mem_adr
        self._scene_mgr_adr: int = scene_mgr_adr
        self._date: datetime = datetime.now()
        self._align: int = 0
        if auto_logging:
            self._align = 2
        self._stats_offset: int = 0x0
        if aroma:
            self._stats_offset = 0x30
        self._versus_rule: int = 0
        self._disconnect: bool = False

    def create_new_log(self) -> None:
        """Initialize a new log file."""

        if not os.path.isdir(f"./logs/{self._date.strftime('%Y-%m-%d')}"):
            os.makedirs(f"./logs/{self._date.strftime('%Y-%m-%d')}")

        self._write_log(log=f"Splatlogger log from {self._date.strftime('%Y-%m-%d %H:%M:%S')}\n", mode="w")

    def log_match(self, session_id: int, match_count: int, player_dict: PlayerDict) -> None:
        """Write player and match data to the log file."""

        player_info: bytes = player_dict["player_info"]
        region: int = int.from_bytes(player_info[0x2C:0x30], byteorder="big")
        team: int = int.from_bytes(player_info[0x33:0x34], byteorder="big")
        gender: int = int.from_bytes(player_info[0x37:0x38], byteorder="big")
        skin_tone: int = int.from_bytes(player_info[0x3B:0x3C], byteorder="big")
        eye_color: int = int.from_bytes(player_info[0x3F:0x40], byteorder="big")
        shoes: int = int.from_bytes(player_info[0x54:0x58], byteorder="big")
        clothes: int = int.from_bytes(player_info[0x70:0x74], byteorder="big")
        headgear: int = int.from_bytes(player_info[0x8C:0x90], byteorder="big")
        level: int = int.from_bytes(player_info[0xAF:0xB0], byteorder="big", signed=True) + 1
        rank: int = int.from_bytes(player_info[0xB3:0xB4], byteorder="big", signed=True)
        weapon: int = int.from_bytes(player_info[0x46:0x48], byteorder="big")
        sub_weapon: int = int.from_bytes(player_info[0x4A:0x4C], byteorder="big")
        special_weapon: int = int.from_bytes(player_info[0x4D:0x50], byteorder="big")
        match_log: str = ""

        if player_dict["number"] == 1:
            match_log += self._new_match(session_id, match_count)

        match_log += (
            f"\n{' ' * self._align}[Player {player_dict['number']}]\n"
            f"{' ' * (self._align + 2)}Name: {player_dict['name']}"
            f"{' (Mii name: ' + player_dict['mii_name'] + ')' if player_dict['name'] != player_dict['mii_name'] else ''}\n"
            f"{' ' * (self._align + 2)}PID: {player_dict['pid']:X} ({player_dict['pid']})\n"
            f"{' ' * (self._align + 2)}PNID: {player_dict['pnid']}\n"
            f"{' ' * (self._align + 2)}Region: {region}\n"
            f"{' ' * (self._align + 2)}Team: {names.TEAM_NAME.get(team, 'Unknown')} ({team})\n"
            f"{' ' * (self._align + 2)}Level: {level}\n"
            f"{' ' * (self._align + 2)}Rank: {names.RANK_NAME.get(rank, 'Unknown')} ({rank})\n"
            f"{' ' * (self._align + 2)}Appearance: Gender: {names.GENDER_NAME.get(gender, 'Unknown')} ({gender}),"
            f" Skin tone: {skin_tone}, Eye color: {names.EYE_COLOR_NAME.get(eye_color, 'Unknown')} ({eye_color})\n"
            f"{' ' * (self._align + 2)}Gear: Headgear: {names.HEADGEAR_NAME.get(headgear, 'Unknown')} ({headgear}),"
            f" Clothes: {names.CLOTHES_NAME.get(clothes, 'Unknown')} ({clothes}),"
            f" Shoes: {names.SHOES_NAME.get(shoes, 'Unknown')} ({shoes})\n"
            f"{' ' * (self._align + 2)}Weapons: Main: {names.WEAPON_NAME.get(weapon, 'Unknown')} ({weapon}),"
            f" Sub: {names.SUB_WEAPON_NAME.get(sub_weapon, 'Unknown')} ({sub_weapon}),"
            f" Special: {names.SPECIAL_WEAPON_NAME.get(special_weapon, 'Unknown')} ({special_weapon})\n"
        )  # Long ass string.

        if self._log_stats and not self._disconnect:
            match_log += self._get_stats(team, player_dict)

        self._write_log(log=match_log, mode="a")

    def _write_log(self, log: str, mode: str) -> None:
        with open(
            f"./logs/{self._date.strftime('%Y-%m-%d')}/{self._date.strftime('%Y-%m-%d %H-%M-%S')} log.txt",
            mode, encoding="utf-8"
        ) as f:
            f.write(log)

    def _new_match(self, session_id: int, match_count: int) -> str:
        self._disconnect = False
        match_hour: int = int.from_bytes(
            self._gecko.readmem(self._static_mem_adr + self.MATCH_HOUR_OFFSET, length=0x1), byteorder="big"
        )
        versus_mode: int = int.from_bytes(
            self._gecko.readmem(self._static_mem_adr + self.VERSUS_MODE_OFFSET, length=0x1), byteorder="big"
        )
        self._versus_rule = int.from_bytes(
            self._gecko.readmem(self._static_mem_adr + self.VERSUS_RULE_OFFSET, length=0x1), byteorder="big"
        )
        stage: str = (
            self._gecko.readmem(self._static_mem_adr + self.STAGE_OFFSET, length=0x20)
            .decode("utf-8")
            .split("\u0000")[0]
        )
        match_info: str

        if self._auto_logging:
            match_info = (
                f"\n[Match {match_count}]\n"
                f"{' ' * self._align}Time: {datetime.now().strftime('%H:%M:%S')}\n"
                f"{' ' * self._align}Session ID: {session_id:X} ({session_id})\n"
                f"{' ' * self._align}Versus mode: {names.VERSUS_MODE_NAME.get(versus_mode, 'Unknown')}\n"
                f"{' ' * self._align}Versus rule: {names.VERSUS_RULE_NAME.get(self._versus_rule, 'Unknown')}\n"
                f"{' ' * self._align}Stage: {names.STAGE_NAME.get(stage, 'Unknown')}\n"
                f"{' ' * self._align}Day/Night: {names.MATCH_HOUR_NAME.get(match_hour, 'Unknown')}\n"
            )
        else:
            match_info = (
                f"{' ' * self._align}\nSession ID: {session_id:X} ({session_id})\n"
                f"{' ' * self._align}Versus mode: {names.VERSUS_MODE_NAME.get(versus_mode, 'Unknown')}\n"
                f"{' ' * self._align}Versus rule: {names.VERSUS_RULE_NAME.get(self._versus_rule, 'Unknown')}\n"
                f"{' ' * self._align}Stage: {names.STAGE_NAME.get(stage, 'Unknown')}\n"
                f"{' ' * self._align}Day/Night: {names.MATCH_HOUR_NAME.get(match_hour, 'Unknown')}\n"
            )

        return match_info

    def _get_stats(self, team: int, player_dict: PlayerDict) -> str:
        stats: bytes = self._gecko.readmem(self.STATS_ADR - self._stats_offset, length=0x124)

        # Buffer player 1 data until stats are updated.
        if player_dict["number"] == 1:
            while self._gecko.readmem(self.STATS_ADR - self._stats_offset, length=0x124) == stats:
                if int.from_bytes(
                        self._gecko.readmem(self._scene_mgr_adr + self.SCENE_ID_OFFSET, length=0x2), byteorder="big"
                ) != 7:  # Fallback to scene change in case the match is not finished.
                    self._disconnect = True
                    break

                time.sleep(5)

        if not self._disconnect:  # Don't log stats if the match didn't end properly.
            winning_team: int = int.from_bytes(
                self._gecko.readmem(self.WIN_TEAM_ADR - self._stats_offset, length=0x1), byteorder="big"
            )
            stats = self._gecko.readmem(self.STATS_ADR - self._stats_offset, length=0x124)  # Read the updated stats again.
            offset: int = (player_dict["number"] - 1) * 0x20
            points: int = int.from_bytes(stats[offset + 0x3A:offset + 0x3C], byteorder="big")
            kills: int = int.from_bytes(stats[offset + 0x3E:offset + 0x40], byteorder="big")
            deaths: int = int.from_bytes(stats[offset + 0x42:offset + 0x44], byteorder="big")
            points_log: str = ""

            # Only log points in turf war cause in ranked they're the same for all players.
            if self._versus_rule == 0:
                if team == winning_team:
                    points_log = f"{' ' * (self._align + 2)}Points: {points + 1000}p ({points}p w/o win bonus)\n"
                else:
                    points_log = f"{' ' * (self._align + 2)}Points: {points}p\n"

            player_stats = (
                f"{points_log}"
                f"{' ' * (self._align + 2)}Kills: {kills}\n"
                f"{' ' * (self._align + 2)}Deaths: {deaths}\n"
                f"{' ' * (self._align + 2)}Result: {'Win' if team == winning_team else 'Lose'}\n"
            )

            return player_stats

        return ""
