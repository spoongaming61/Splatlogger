# Splatlogger (c) 2025 Shadow Doggo.

import os
import time
from datetime import datetime

from tcpgecko import TCPGecko
from data import Pointers, Addresses, Offsets, PlayerInfo, Names


class MatchLogger:
    """Provides the match logging functionality of Splatlogger."""

    def __init__(
            self, gecko: TCPGecko, auto_logging: bool, log_stats: bool, aroma: bool, static_mem_adr: int
    ) -> None:
        self._gecko: TCPGecko = gecko
        self._auto_logging: bool = auto_logging
        self._log_stats: bool = log_stats
        self._static_mem_adr: int = static_mem_adr
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

    def log_match(self, session_id: int, match_count: int, player_info_list: list[PlayerInfo]) -> None:
        """Write player and match data to the log file."""

        match_log: str = ""

        for player_info in player_info_list:
            if player_info.index == 0:
                match_log += self._new_match(session_id, match_count)

            appearance: str = (
                f"Gender: {Names.GENDER_NAME.get(player_info.gender, 'Unknown')} ({player_info.gender}), "
                f"Skin tone: {player_info.skin_tone}, "
                f"Eye color: {Names.EYE_COLOR_NAME.get(player_info.eye_color, 'Unknown')} ({player_info.eye_color})"
            )
            gear: str = (
                f"Headgear: {Names.HEADGEAR_NAME.get(player_info.headgear, 'Unknown')} ({player_info.headgear}), "
                f"Clothes: {Names.CLOTHES_NAME.get(player_info.clothes, 'Unknown')} ({player_info.clothes}), "
                f"Shoes: {Names.SHOES_NAME.get(player_info.shoes, 'Unknown')} ({player_info.shoes})"
            )
            weapons: str = (
                f"Main: {Names.WEAPON_NAME.get(player_info.weapon, 'Unknown')} ({player_info.weapon}), "
                f"Sub: {Names.SUB_WEAPON_NAME.get(player_info.sub_weapon, 'Unknown')} ({player_info.sub_weapon}), "
                f"Special: {Names.SPECIAL_WEAPON_NAME.get(player_info.special_weapon, 'Unknown')} "
                f"({player_info.special_weapon})"
            )

            match_log += (
                f"\n{' ' * self._align}[Player {player_info.index + 1}]\n"
                f"{' ' * (self._align + 2)}Name: {player_info.name}"
                f"{' (Mii name: ' + player_info.mii_name + ')' if player_info.name != player_info.mii_name else ''}\n"
                f"{' ' * (self._align + 2)}PID: {player_info.pid:X} ({player_info.pid})\n"
                f"{' ' * (self._align + 2)}PNID: {player_info.pnid}\n"
                f"{' ' * (self._align + 2)}Region: {player_info.region}\n"
                f"{' ' * (self._align + 2)}Team: {Names.TEAM_NAME.get(player_info.team, 'Unknown')} "
                f"({player_info.team})\n"
                f"{' ' * (self._align + 2)}Level: {player_info.level}\n"
                f"{' ' * (self._align + 2)}Rank: {Names.RANK_NAME.get(player_info.rank, 'Unknown')} "
                f"({player_info.rank})\n"
                f"{' ' * (self._align + 2)}Appearance: {appearance}\n"
                f"{' ' * (self._align + 2)}Gear: {gear}\n"
                f"{' ' * (self._align + 2)}Weapons: {weapons}\n"
            )

            if self._log_stats and not self._disconnect:
                match_log += self._get_stats(player_info.team, player_info)

        self._write_log(log=match_log, mode="a")

    def _write_log(self, log: str, mode: str) -> None:
        with open(
            f"./logs/{self._date.strftime('%Y-%m-%d')}/{self._date.strftime('%Y-%m-%d %H-%M-%S')} log.txt",
            mode, encoding="utf-8"
        ) as f:
            f.write(log)

    def _new_match(self, session_id: int, match_count: int) -> str:
        self._disconnect = False
        match_hour: int = self._gecko.peek8(self._static_mem_adr + Offsets.MATCH_HOUR)
        versus_mode: int = self._gecko.peek8(self._static_mem_adr + Offsets.VERSUS_MODE)
        self._versus_rule = self._gecko.peek8(self._static_mem_adr + Offsets.VERSUS_RULE)
        stage: str = self._gecko.read_string(self._static_mem_adr + Offsets.STAGE, strlen=32).split("\u0000")[0]

        match_info: str
        if self._auto_logging:
            match_info = (
                f"\n[Match {match_count}]\n"
                f"{' ' * self._align}Time: {datetime.now().strftime('%H:%M:%S')}\n"
                f"{' ' * self._align}Session ID: {session_id:X} ({session_id})\n"
                f"{' ' * self._align}Versus mode: {Names.VERSUS_MODE_NAME.get(versus_mode, 'Unknown')}\n"
                f"{' ' * self._align}Versus rule: {Names.VERSUS_RULE_NAME.get(self._versus_rule, 'Unknown')}\n"
                f"{' ' * self._align}Stage: {Names.STAGE_NAME.get(stage, 'Unknown')}\n"
                f"{' ' * self._align}Day/Night: {Names.MATCH_HOUR_NAME.get(match_hour, 'Unknown')}\n"
            )
        else:
            match_info = (
                f"{' ' * self._align}\nSession ID: {session_id:X} ({session_id})\n"
                f"{' ' * self._align}Versus mode: {Names.VERSUS_MODE_NAME.get(versus_mode, 'Unknown')}\n"
                f"{' ' * self._align}Versus rule: {Names.VERSUS_RULE_NAME.get(self._versus_rule, 'Unknown')}\n"
                f"{' ' * self._align}Stage: {Names.STAGE_NAME.get(stage, 'Unknown')}\n"
                f"{' ' * self._align}Day/Night: {Names.MATCH_HOUR_NAME.get(match_hour, 'Unknown')}\n"
            )

        return match_info

    def _get_stats(self, team: int, player_info: PlayerInfo) -> str:
        stats: bytes = self._gecko.peek_raw(Addresses.STATS - self._stats_offset, length=0x124)

        # Buffer player 1 data until stats are updated.
        if player_info.index == 0:
            while self._gecko.peek_raw(Addresses.STATS - self._stats_offset, length=0x124) == stats:
                if self._gecko.peek32(Pointers.MAIN_MGR_VS_GAME) == 0:  # Fallback in case the match is not finished.
                    self._disconnect = True
                    break

                time.sleep(5)

        if not self._disconnect:
            winning_team: int = self._gecko.peek8(Addresses.WIN_TEAM - self._stats_offset)
            stats = self._gecko.peek_raw(Addresses.STATS - self._stats_offset, length=0x124)
            offset: int = player_info.index * 0x20
            points: int = int.from_bytes(stats[offset + 0x3A:offset + 0x3C], byteorder="big")
            kills: int = int.from_bytes(stats[offset + 0x3E:offset + 0x40], byteorder="big")
            deaths: int = int.from_bytes(stats[offset + 0x42:offset + 0x44], byteorder="big")

            # Only log points in turf war cause in ranked they're the same for all players.
            points_log: str = ""
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
