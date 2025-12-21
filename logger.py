# Splatlogger (c) 2025 Shadow Doggo.

import os
import json
import time
from datetime import datetime

import names


class Logger:
    def __init__(self, gecko, static_mem_adr, scene_mgr_adr):
        self.date = datetime.now()
        self.regions = json.loads(open("regions.json").read())
        self.gecko = gecko
        self.static_mem_adr = static_mem_adr
        self.scene_mgr_adr = scene_mgr_adr
        self.align = 0
        self.session_id = 0


    def create_log(self):
        if not os.path.isdir(f"./logs/{self.date.strftime('%Y-%m-%d')}"):
            os.makedirs(f"./logs/{self.date.strftime('%Y-%m-%d')}")

        with open(
            f"./logs/{self.date.strftime('%Y-%m-%d')}/{self.date.strftime('%Y-%m-%d %H-%M-%S')} log.txt",
            "w", encoding="utf-8"
        ) as f:
            f.write(f"Splatlogger log from {self.date.strftime('%Y-%m-%d %H:%M:%S')}\n")


    def new_match(self, auto_logging, session_adr, count):
        match_hour = int.from_bytes(self.gecko.readmem(self.static_mem_adr + 0x237, 1), "big")
        versus_mode = int.from_bytes(self.gecko.readmem(self.static_mem_adr + 0x23B, 1), "big")
        versus_rule = int.from_bytes(self.gecko.readmem(self.static_mem_adr + 0x23F, 1), "big")
        stage = self.gecko.readmem(self.static_mem_adr + 0x28, 32).decode("utf-8").split("\u0000")[0]

        if auto_logging:
            self.align = 2

            if session_adr != 0:
                session_id_idx = int.from_bytes(self.gecko.readmem(session_adr + 0xBD, 1), "big")
                self.session_id = int.from_bytes(self.gecko.readmem(session_adr + session_id_idx * 4 + 0xCC, 4), "big")
            else:
                self.session_id = 0

            match_info = (
                    f"\n[Match {count}]\n\n"
                    f"{' ' * self.align}Time: {datetime.now().strftime('%H:%M:%S')}\n"
                    f"{' ' * self.align}Session ID: {self.session_id:X} ({self.session_id})\n"
                    f"{' ' * self.align}Versus mode: {names.VERSUS_MODE_NAME.get(versus_mode, 'Unknown')}\n"
                    f"{' ' * self.align}Versus rule: {names.VERSUS_RULE_NAME.get(versus_rule, 'Unknown')}\n"
                    f"{' ' * self.align}Day/Night: {names.MATCH_HOUR_NAME.get(match_hour, 'Unknown')}\n"
                    f"{' ' * self.align}Stage: {names.STAGE_NAME.get(stage, 'Unknown')}\n"
                )

            with open(
                f"./logs/{self.date.strftime('%Y-%m-%d')}/{self.date.strftime('%Y-%m-%d %H-%M-%S')} log.txt",
                "a", encoding="utf-8"
            ) as f:
                f.write(match_info)
        else:
            if session_adr != 0:
                session_id_idx = int.from_bytes(self.gecko.readmem(session_adr + 0xBD, 1), "big")
                self.session_id = int.from_bytes(self.gecko.readmem(session_adr + session_id_idx * 4 + 0xCC, 4), "big")
            else:
                self.session_id = 0

            match_info = (
                    f"{' ' * self.align}\nSession ID: {self.session_id:X} ({self.session_id})\n"
                    f"{' ' * self.align}Versus mode: {names.VERSUS_MODE_NAME.get(versus_mode, 'Unknown')}\n"
                    f"{' ' * self.align}Versus rule: {names.VERSUS_RULE_NAME.get(versus_rule, 'Unknown')}\n"
                    f"{' ' * self.align}Day/Night: {names.MATCH_HOUR_NAME.get(match_hour, 'Unknown')}\n"
                    f"{' ' * self.align}Stage: {names.STAGE_NAME.get(stage, 'Unknown')}\n"
                )

            with open(
                f"./logs/{self.date.strftime('%Y-%m-%d')}/{self.date.strftime('%Y-%m-%d %H-%M-%S')} log.txt",
                "a", encoding="utf-8"
            ) as f:
                f.write(match_info)


    def log(self, log_stats, player_dict):
        region = int.from_bytes(player_dict["PlayerInfo"][0x2C:0x30], "big")
        team = int.from_bytes(player_dict["PlayerInfo"][0x33:0x34], "big")
        gender = int.from_bytes(player_dict["PlayerInfo"][0x37:0x38], "big")
        skin_tone = int.from_bytes(player_dict["PlayerInfo"][0x3B:0x3C], "big")
        eye_color = int.from_bytes(player_dict["PlayerInfo"][0x3F:0x40], "big")
        shoes = int.from_bytes(player_dict["PlayerInfo"][0x54:0x58], "big")
        clothes = int.from_bytes(player_dict["PlayerInfo"][0x70:0x74], "big")
        headgear = int.from_bytes(player_dict["PlayerInfo"][0x8C:0x90], "big")
        level = int.from_bytes(player_dict["PlayerInfo"][0xAF:0xB0], "big", signed=True) + 1
        rank = int.from_bytes(player_dict["PlayerInfo"][0xB3:0xB4], "big", signed=True)
        weapon = int.from_bytes(player_dict["PlayerInfo"][0x46:0x48], "big")  # Main weapon ID. Also possible to get the weapon set ID but that can be spoofed.
        sub_weapon = int.from_bytes(player_dict["PlayerInfo"][0x4A:0x4C], "big")
        special_weapon = int.from_bytes(player_dict["PlayerInfo"][0x4D:0x50], "big")

        player_log = (
            f"\n{' ' * self.align}[Player {player_dict['Number']}]\n\n"
            f"{' ' * (self.align + 2)}Name: {player_dict['Name']}\n"
            f"{' ' * (self.align + 2)}PID: {player_dict['PID']:X} ({player_dict['PID']})\n"
            f"{' ' * (self.align + 2)}PNID: {player_dict['PNID']}\n"
            f"{' ' * (self.align + 2)}Mii name: {player_dict['Mii name']}\n"
            f"{' ' * (self.align + 2)}Mii icon: {player_dict['Mii icon']}\n"
            f"{' ' * (self.align + 2)}Country: {self.get_region(region)[1]} ({self.get_region(region)[0]})\n"
            f"{' ' * (self.align + 2)}Region: {self.get_region(region)[2]} ({region})\n"
            f"{' ' * (self.align + 2)}Team: {names.TEAM_NAME.get(team, 'Unknown')} ({team})\n"
            f"{' ' * (self.align + 2)}Gender: {names.GENDER_NAME.get(gender, 'Unknown')} ({gender})\n"
            f"{' ' * (self.align + 2)}Skin tone: {skin_tone}\n"
            f"{' ' * (self.align + 2)}Eye color: {names.EYE_COLOR_NAME.get(eye_color, 'Unknown')} ({eye_color})\n"
            f"{' ' * (self.align + 2)}Shoes: {names.SHOES_NAME.get(shoes, 'Unknown')} ({shoes})\n"
            f"{' ' * (self.align + 2)}Clothes: {names.CLOTHES_NAME.get(clothes, 'Unknown')} ({clothes})\n"
            f"{' ' * (self.align + 2)}Headgear: {names.HEADGEAR_NAME.get(headgear, 'Unknown')} ({headgear})\n"
            f"{' ' * (self.align + 2)}Level: {level}\n"
            f"{' ' * (self.align + 2)}Rank: {names.RANK_NAME.get(rank, 'Unknown')} ({rank})\n"
            f"{' ' * (self.align + 2)}Weapon: {names.WEAPON_NAME.get(weapon, 'Unknown')} ({weapon})\n"
            f"{' ' * (self.align + 2)}Sub weapon: {names.SUB_WEAPON_NAME.get(sub_weapon, 'Unknown')} ({sub_weapon})\n"
            f"{' ' * (self.align + 2)}Special weapon: {names.SPECIAL_WEAPON_NAME.get(special_weapon, 'Unknown')} ({special_weapon})\n"
        )  # Long ass string.

        with open(
            f"./logs/{self.date.strftime('%Y-%m-%d')}/{self.date.strftime('%Y-%m-%d %H-%M-%S')} log.txt",
            "a", encoding="utf-8"
        ) as f:
            f.write(player_log)

        if log_stats:
            stats = self.gecko.readmem(0x107AF944, 292)  # A bunch of data including player stats. I'm not exactly sure what this is, but it works.

            if player_dict["Number"] == 1:  # Buffer player 1 data until stats are updated.
                while (
                    self.gecko.readmem(0x107AF944, 292) == stats and
                    int.from_bytes(self.gecko.readmem(self.scene_mgr_adr + 0x162, 2), "big") == 7  # Fallback to scene change in case the match is not finished.
                ):
                    time.sleep(10)

            winning_team = int.from_bytes(self.gecko.readmem(0x107AF917, 1), "big")
            stats = self.gecko.readmem(0x107AF944, 292)  # Read the updated stats again.
            offset = (player_dict["Number"] - 1) * 0x20
            points = int.from_bytes(stats[offset + 0x3A:offset + 0x3C], "big")
            kills = int.from_bytes(stats[offset + 0x3E:offset + 0x40], "big")
            deaths = int.from_bytes(stats[offset + 0x42:offset + 0x44], "big")

            player_stats = (
                f"{' ' * (self.align + 2)}Points: {points}p\n"
                f"{' ' * (self.align + 2)}Kills: {kills}\n"
                f"{' ' * (self.align + 2)}Deaths: {deaths}\n"
                f"{' ' * (self.align + 2)}Result: {'Win' if team == winning_team else 'Lose'}\n"
            )

            with open(
                f"./logs/{self.date.strftime('%Y-%m-%d')}/{self.date.strftime('%Y-%m-%d %H-%M-%S')} log.txt",
                "a", encoding="utf-8"
            ) as f:
                f.write(player_stats)


    def get_region(self, region):
        for i in self.regions:
            for j in range(len(i["regions"])):
                if i["regions"][j]["id"] == region:
                    return (
                        i["id"],
                        i["name"],
                        i["regions"][j]["name"]
                        .encode("utf-8", errors="ignore")
                        .decode("utf-8"),
                    )

        return "None", "None", "None"
