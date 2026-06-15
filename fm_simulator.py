import os
import sys
import json
import random
import ctypes
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, ttk

SAVE_DIR = r"C:\MANAGER_SIMULATOR"
SAVE_FILE = os.path.join(SAVE_DIR, "fm_ultimate_v13.json")
TRANSFER_MONTHS = {1, 7, 8}

INSTRUCTIONS = ["기본", "공격 가담", "수비 대기", "오버래핑", "인버티드 런", "딥 라잉", "박스 투 박스", "전진 플레이메이커", "타깃맨", "압박 선봉"]

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

# ── 1. 날짜 시스템 ────────────────────────────────────────────────────────
class GameDate:
    MONTH_NAMES = ["","1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
    def __init__(self, year=2026, month=8, day=1):
        self.year = year; self.month = month; self.day = day
    def advance_match(self, team=None, pool=None):
        self.day += 7
        if self.day > 28:
            self.day -= 28; self.month += 1
            if self.month > 12:
                self.month = 1; self.year += 1
                if team:
                    for p in team.all_players(): p.age += 1
                if pool:
                    for p in pool: p.age += 1
    def is_transfer_window(self): return self.month in TRANSFER_MONTHS
    def __str__(self): return f"{self.year}년 {self.MONTH_NAMES[self.month]} {self.day}일"
    def to_dict(self): return {"year": self.year, "month": self.month, "day": self.day}
    @classmethod
    def from_dict(cls, d): return cls(d.get("year", 2026), d.get("month", 8), d.get("day", 1))

# ── 2. Player & Team ──────────────────────────────────────────────────────
class Player:
    def __init__(self, name, pos, age, base_pac, base_sho, base_pas, base_def, base_phy, price, stamina=100, inj=0, instr="기본", loaded_stats=None):
        self.name = name; self.position = pos; self.age = age; self.price = price
        self.stamina = stamina; self.injured_days = inj; self.instruction = instr

        if loaded_stats:
            for k, v in loaded_stats.items(): setattr(self, k, v)
        else:
            self.spd = max(30, min(99, base_pac + random.randint(-5, 5)))
            self.acc = max(30, min(99, base_pac + random.randint(-5, 5)))
            self.fin = max(30, min(99, base_sho + random.randint(-5, 5)))
            self.pow = max(30, min(99, base_sho + random.randint(-3, 6)))
            self.spa = max(30, min(99, base_pas + random.randint(-4, 6)))
            self.vis = max(30, min(99, base_pas + random.randint(-6, 6)))
            self.tak = max(30, min(99, base_def + random.randint(-5, 5)))
            self.mrk = max(30, min(99, base_def + random.randint(-5, 5)))
            self.str = max(30, min(99, base_phy + random.randint(-4, 6)))
            self.jum = max(30, min(99, base_phy + random.randint(-6, 6)))

    @property
    def rating(self):
        if self.position in ['ST','LW','RW']: return int(self.fin*0.3 + self.spd*0.2 + self.acc*0.2 + self.pow*0.1 + self.str*0.1 + self.spa*0.1)
        elif self.position in ['CM','CAM','CDM']: return int(self.spa*0.3 + self.vis*0.3 + self.tak*0.1 + self.str*0.1 + self.pow*0.1 + self.spd*0.1)
        elif self.position in ['CB','FB']: return int(self.tak*0.3 + self.mrk*0.3 + self.str*0.2 + self.spd*0.1 + self.jum*0.1)
        elif self.position == 'GK': return int(self.tak*0.5 + self.jum*0.3 + self.str*0.2)
        return int((self.spd+self.fin+self.spa+self.tak+self.str)/5)

    def to_dict(self):
        return {"name": self.name, "position": self.position, "age": self.age, "price": self.price,
                "stamina": self.stamina, "injured_days": self.injured_days, "instruction": self.instruction,
                "detailed": {"spd":self.spd,"acc":self.acc,"fin":self.fin,"pow":self.pow,"spa":self.spa,
                             "vis":self.vis,"tak":self.tak,"mrk":self.mrk,"str":self.str,"jum":self.jum}}

# ── 3. 이적 풀 (포지션별 200명+) ────────────────────────────────────────────
# (name, pos, age, pac, sho, pas, def, phy, price)
TRANSFER_POOL_DATA = [
    # ══ 스트라이커 (ST) ══════════════════════════════════════════════════════
    ("Haaland",           "ST", 25, 88, 94, 65, 40, 90, 200),
    ("Mbappe",            "ST", 27, 96, 91, 80, 38, 82, 190),
    ("Kane",              "ST", 32, 72, 93, 86, 42, 82,  85),
    ("Osimhen",           "ST", 27, 90, 86, 70, 38, 86, 110),
    ("Gyokeres",          "ST", 28, 84, 89, 72, 44, 88, 110),
    ("Isak",              "ST", 26, 88, 85, 75, 40, 78,  95),
    ("Endrick",           "ST", 20, 88, 84, 70, 42, 82,  95),
    ("L. Martinez",       "ST", 28, 82, 88, 75, 45, 84, 105),
    ("Zirkzee",           "ST", 25, 78, 83, 78, 44, 80,  70),
    ("Watkins",           "ST", 30, 84, 84, 76, 46, 78,  65),
    ("Nunez",             "ST", 26, 90, 82, 68, 42, 85,  75),
    ("Sesko",             "ST", 23, 88, 82, 70, 44, 82,  85),
    ("Openda",            "ST", 25, 90, 82, 72, 42, 80,  80),
    ("Balde Keita",       "ST", 27, 80, 82, 72, 40, 78,  65),
    ("Vlahovic",          "ST", 26, 78, 86, 70, 44, 84,  75),
    ("Fullkrug",          "ST", 33, 70, 84, 72, 50, 86,  40),
    ("Arnaut Danjuma",    "ST", 29, 84, 78, 70, 42, 74,  35),
    ("Benzema",           "ST", 38, 68, 84, 80, 42, 74,  20),
    ("Giroud",            "ST", 40, 64, 80, 74, 50, 82,  10),
    ("Depay",             "ST", 32, 86, 82, 78, 44, 76,  25),
    ("Firmino",           "ST", 34, 76, 80, 82, 50, 74,  15),
    ("Mitrovic",          "ST", 31, 72, 88, 62, 48, 86,  45),
    ("Calvert-Lewin",     "ST", 29, 80, 82, 68, 46, 80,  45),
    ("Havertz",           "ST", 27, 80, 82, 84, 58, 78,  80),
    ("Joelinton",         "ST", 29, 82, 76, 76, 62, 86,  50),
    ("Rashford",          "LW", 28, 88, 84, 78, 46, 76,  55),
    # ══ 좌·우 윙어 (LW/RW) ════════════════════════════════════════════════
    ("Vinicius Jr",       "LW", 25, 96, 86, 80, 40, 78, 170),
    ("Yamal",             "RW", 19, 93, 85, 82, 42, 68, 165),
    ("Saka",              "RW", 24, 88, 84, 84, 60, 74, 115),
    ("Kvaratskhelia",     "LW", 25, 88, 82, 80, 48, 76, 125),
    ("Leao",              "LW", 27, 92, 80, 76, 42, 78, 115),
    ("Rodrygo",           "RW", 25, 88, 82, 80, 42, 70,  95),
    ("Salah",             "RW", 34, 86, 88, 82, 46, 74,  50),
    ("Diaz",              "LW", 29, 88, 80, 76, 52, 78,  80),
    ("Raphinha",          "RW", 29, 90, 84, 78, 50, 76,  90),
    ("Foden",             "LW", 26, 88, 85, 86, 52, 68, 120),
    ("Son Heung-min",     "LW", 34, 88, 88, 80, 42, 72,  55),
    ("Pulisic",           "RW", 28, 86, 80, 80, 52, 72,  55),
    ("Lookman",           "LW", 28, 88, 82, 76, 50, 74,  75),
    ("Antony",            "RW", 26, 86, 76, 74, 46, 68,  30),
    ("Doku",              "LW", 23, 96, 76, 74, 44, 76,  90),
    ("Coman",             "LW", 30, 92, 78, 76, 52, 76,  50),
    ("Gnabry",            "RW", 31, 88, 80, 78, 52, 76,  45),
    ("Mane",              "LW", 35, 86, 82, 76, 46, 78,  20),
    ("Zaha",              "LW", 34, 86, 78, 74, 50, 76,  15),
    ("Sancho",            "RW", 26, 86, 78, 80, 50, 70,  35),
    ("Sterling",          "LW", 32, 86, 78, 78, 50, 72,  25),
    ("Neto",              "RW", 25, 88, 78, 76, 48, 72,  60),
    ("Chukwueze",         "RW", 28, 86, 78, 74, 50, 72,  50),
    ("Asensio",           "RW", 31, 84, 80, 82, 52, 70,  30),
    ("Ferran Torres",     "LW", 26, 88, 78, 76, 52, 72,  45),
    ("Orban",             "RW", 24, 86, 74, 74, 48, 70,  50),
    ("Hudson-Odoi",       "LW", 25, 86, 74, 76, 48, 70,  30),
    ("Garnacho",          "RW", 22, 86, 78, 74, 44, 64,  55),
    ("Madueke",           "RW", 24, 86, 78, 76, 48, 70,  55),
    ("Mudryk",            "LW", 25, 88, 76, 74, 48, 72,  45),
    ("Ikoné",             "RW", 28, 86, 74, 74, 50, 70,  30),
    ("Almada",            "CAM",25, 82, 78, 84, 56, 72,  60),
    ("Savinho",           "RW", 22, 90, 76, 76, 46, 72,  75),
    ("Conceicao",         "RW", 23, 90, 78, 74, 46, 70,  70),
    # ══ 공격형 미드필더 (CAM) ════════════════════════════════════════════
    ("Bellingham",        "CAM", 23, 82, 87, 88, 72, 84, 165),
    ("Wirtz",             "CAM", 23, 84, 86, 90, 62, 74, 160),
    ("Musiala",           "CAM", 23, 86, 83, 87, 60, 74, 145),
    ("Odegaard",          "CAM", 27, 80, 83, 92, 62, 72, 105),
    ("Guler",             "CAM", 21, 80, 78, 85, 52, 62,  75),
    ("Zaire-Emery",       "CM",  21, 82, 72, 86, 80, 80,  95),
    ("Olise",             "CAM", 24, 84, 82, 82, 54, 70,  90),
    ("Diaz B.",           "CAM", 24, 80, 78, 86, 60, 72,  75),
    ("Szoboszlai",        "CAM", 25, 82, 78, 84, 64, 80,  80),
    ("De Bruyne",         "CM",  35, 74, 85, 94, 60, 72,  55),
    ("Mata",              "CAM", 37, 68, 74, 86, 52, 62,   5),
    ("Griezmann",         "CAM", 35, 78, 84, 82, 62, 72,  45),
    ("Papu Gomez",        "CAM", 38, 78, 76, 80, 52, 66,   5),
    ("Coutinho",          "CAM", 34, 78, 80, 84, 56, 66,  10),
    ("Mount",             "CAM", 27, 78, 80, 84, 66, 72,  50),
    ("Havertz K.",        "CAM", 27, 80, 82, 84, 58, 78,  80),
    ("Fernandez B.",      "CM",  25, 76, 74, 86, 78, 76,  80),
    ("Pellegrini",        "CAM", 32, 76, 80, 84, 56, 72,  40),
    ("Skov Olsen",        "RW",  27, 88, 76, 74, 50, 72,  35),
    # ══ 중앙 미드필더 (CM) ════════════════════════════════════════════════
    ("Pedri",             "CM",  23, 82, 78, 91, 74, 70, 110),
    ("Gavi",              "CM",  22, 82, 74, 88, 78, 76,  95),
    ("Valverde",          "CM",  28, 88, 82, 86, 80, 84, 105),
    ("Barella",           "CM",  28, 80, 78, 86, 82, 84,  90),
    ("Camavinga",         "CM",  23, 84, 75, 84, 82, 80,  95),
    ("Mac Allister",      "CM",  27, 76, 80, 86, 78, 78,  85),
    ("Kimmich",           "CM",  31, 76, 72, 90, 86, 78,  75),
    ("Alexander-Arnold",  "CM",  27, 80, 76, 90, 78, 74,  85),
    ("Eriksen",           "CM",  34, 64, 78, 90, 58, 64,  20),
    ("Kroos",             "CM",  36, 64, 78, 92, 72, 66,  15),
    ("Modric",            "CM",  41, 72, 74, 90, 70, 66,   5),
    ("Arthur",            "CM",  29, 76, 68, 84, 72, 68,  20),
    ("Goretzka",          "CM",  31, 80, 76, 84, 78, 84,  50),
    ("Thuram M.",         "CM",  28, 82, 74, 84, 76, 82,  80),
    ("Neves R.",          "CM",  29, 76, 74, 86, 80, 78,  65),
    ("Veiga",             "CM",  26, 78, 78, 84, 72, 74,  60),
    ("Loftus-Cheek",      "CM",  30, 78, 76, 78, 72, 84,  40),
    ("Soucek",            "CM",  31, 74, 72, 74, 82, 86,  30),
    ("Fred",              "CDM", 33, 78, 66, 76, 78, 80,  15),
    ("Wijnaldum",         "CM",  35, 74, 72, 80, 74, 80,  10),
    ("Gallagher",         "CM",  26, 82, 72, 78, 78, 84,  55),
    ("Greenwood",         "RW",  24, 84, 80, 76, 54, 76,  45),
    ("Diawara",           "CM",  29, 76, 66, 76, 80, 78,  30),
    ("Fabian",            "CM",  30, 76, 72, 84, 74, 76,  40),
    ("Bissouma",          "CDM", 29, 78, 64, 76, 82, 82,  45),
    ("Saul",              "CDM", 31, 78, 68, 76, 78, 80,  20),
    ("Ruiz F.",           "CM",  24, 78, 74, 86, 70, 74,  65),
    ("Pavlidis",          "ST",  28, 78, 84, 68, 42, 82,  50),
    # ══ 수비형 미드필더 (CDM) ════════════════════════════════════════════
    ("Rodri",             "CDM", 30, 76, 78, 90, 88, 86, 115),
    ("Rice",              "CDM", 27, 80, 70, 84, 86, 86, 105),
    ("Caicedo",           "CDM", 24, 78, 68, 80, 86, 86,  90),
    ("Tchouameni",        "CDM", 26, 78, 70, 82, 86, 85,  90),
    ("Ugarte",            "CDM", 26, 80, 66, 82, 86, 86,  60),
    ("Partey",            "CDM", 33, 78, 68, 76, 82, 82,  30),
    ("Ndidi",             "CDM", 29, 76, 60, 72, 84, 82,  35),
    ("Guendouzi",         "CDM", 26, 78, 68, 78, 80, 78,  45),
    ("Lokonga",           "CDM", 27, 74, 62, 76, 78, 76,  25),
    ("Douglas Luiz",      "CDM", 28, 76, 70, 80, 82, 80,  60),
    ("Pellegrino",        "CDM", 26, 76, 64, 78, 82, 80,  40),
    ("Zakaria",           "CDM", 28, 78, 66, 74, 80, 82,  30),
    ("Tolisso",           "CM",  32, 76, 72, 78, 78, 82,  15),
    ("Florentino",        "CDM", 27, 76, 62, 78, 80, 80,  35),
    ("Andre",             "CDM", 24, 76, 64, 80, 82, 82,  60),
    ("Joao Neves",        "CDM", 21, 78, 66, 82, 82, 78,  90),
    ("Mainoo K.",         "CM",  21, 80, 74, 86, 78, 74,  55),
    # ══ 센터백 (CB) ═══════════════════════════════════════════════════════
    ("Van Dijk",          "CB",  35, 82, 56, 74, 90, 88,  65),
    ("Saliba",            "CB",  25, 78, 40, 72, 88, 86,  95),
    ("Bastoni",           "CB",  27, 76, 45, 78, 88, 82,  90),
    ("Araujo",            "CB",  27, 82, 46, 66, 88, 86,  85),
    ("Dias",              "CB",  29, 72, 40, 70, 88, 88,  80),
    ("Gvardiol",          "CB",  24, 80, 56, 78, 86, 84,  98),
    ("Kim Min-jae",       "CB",  29, 84, 40, 70, 86, 88,  75),
    ("Romero",            "CB",  28, 76, 50, 72, 86, 85,  75),
    ("Yoro",              "CB",  20, 80, 40, 70, 82, 80,  80),
    ("Branthwaite",       "CB",  24, 74, 46, 68, 84, 86,  70),
    ("Upamecano",         "CB",  27, 82, 48, 74, 87, 88,  65),
    ("Tah",               "CB",  30, 78, 52, 76, 88, 86,  55),
    ("Sule",              "CB",  31, 82, 48, 70, 86, 88,  35),
    ("Lovren",            "CB",  37, 72, 44, 66, 82, 80,   5),
    ("Gimenez",           "CB",  32, 82, 50, 66, 86, 84,  35),
    ("Pavard",            "CB",  29, 80, 50, 74, 84, 80,  60),
    ("Akanji",            "CB",  31, 80, 46, 72, 86, 84,  55),
    ("Skriniar",          "CB",  31, 74, 44, 68, 86, 86,  40),
    ("Koulibaly",         "CB",  35, 82, 46, 66, 88, 88,  15),
    ("Timber",            "CB",  24, 82, 52, 76, 84, 82,  80),
    ("Quenda",            "CB",  19, 78, 42, 70, 80, 78,  55),
    ("Dean Huijsen",      "CB",  21, 78, 44, 72, 82, 82,  70),
    ("Lacroix",           "CB",  25, 78, 44, 70, 84, 82,  55),
    ("Danilho Doekhi",    "CB",  27, 76, 44, 70, 82, 80,  35),
    ("Bailly",            "CB",  32, 78, 44, 64, 82, 82,  10),
    ("Maguire",           "CB",  33, 72, 54, 70, 84, 86,  25),
    ("Varane",            "CB",  33, 78, 46, 66, 86, 84,  10),
    ("Christensen",       "CB",  30, 74, 50, 76, 84, 80,  35),
    ("Todibo",            "CB",  26, 78, 44, 70, 84, 82,  55),
    ("Caleta-Car",        "CB",  29, 76, 44, 66, 82, 80,  30),
    ("Kounde",            "FB",  28, 84, 58, 76, 84, 80,  70),
    ("Laporte",           "CB",  32, 74, 50, 76, 86, 84,  30),
    # ══ 풀백 (FB) ════════════════════════════════════════════════════════
    ("Hakimi",            "FB",  27, 93, 75, 82, 78, 80,  95),
    ("Davies",            "FB",  25, 92, 66, 78, 80, 82,  80),
    ("Theo Hernandez",    "FB",  28, 90, 72, 78, 80, 82,  75),
    ("Alexander-Arnold T.","FB", 27, 80, 76, 92, 78, 76,  85),
    ("Frimpong",          "FB",  25, 93, 75, 80, 74, 70,  85),
    ("Udogie",            "FB",  23, 88, 68, 76, 78, 80,  70),
    ("White",             "FB",  28, 78, 60, 80, 84, 80,  65),
    ("Dimarco",           "FB",  28, 84, 78, 86, 76, 74,  70),
    ("Wan-Bissaka",       "FB",  28, 84, 42, 66, 86, 76,  30),
    ("Dalot",             "FB",  27, 85, 65, 80, 80, 76,  45),
    ("Mazraoui",          "FB",  28, 82, 62, 76, 82, 78,  40),
    ("Cancelo",           "FB",  32, 84, 68, 82, 78, 76,  30),
    ("Trent",             "FB",  28, 80, 76, 92, 76, 74,  80),
    ("Shaw",              "FB",  29, 78, 62, 80, 82, 80,  30),
    ("Robertson",         "FB",  33, 82, 64, 82, 80, 78,  30),
    ("Mendy",             "FB",  32, 84, 58, 72, 80, 80,  20),
    ("Chilwell",          "FB",  30, 82, 66, 78, 78, 80,  30),
    ("Reguilon",          "FB",  29, 82, 64, 74, 76, 76,  20),
    ("Balde",             "FB",  22, 88, 66, 76, 78, 80,  65),
    ("Spence",            "FB",  26, 86, 64, 72, 76, 76,  25),
    ("Henrichs",          "FB",  30, 84, 62, 76, 76, 76,  25),
    ("Dumfries",          "FB",  30, 86, 70, 76, 78, 78,  40),
    ("Mukiele",           "FB",  28, 84, 58, 72, 78, 78,  30),
    ("Telles",            "FB",  33, 80, 72, 76, 76, 76,  10),
    ("Alaba",             "CB",  34, 78, 66, 80, 84, 76,  15),
    ("Acuna",             "FB",  33, 80, 66, 76, 78, 78,  15),
    # ══ 골키퍼 (GK) ══════════════════════════════════════════════════════
    ("Alisson",           "GK",  33, 62, 15, 74, 91, 80,  70),
    ("Donnarumma",        "GK",  27, 60, 15, 68, 89, 85,  80),
    ("Courtois",          "GK",  34, 55, 15, 70, 90, 82,  55),
    ("Ederson",           "GK",  32, 64, 20, 86, 88, 78,  60),
    ("Maignan",           "GK",  31, 65, 18, 76, 88, 82,  65),
    ("Vicario",           "GK",  29, 60, 15, 72, 86, 78,  55),
    ("Kobel",             "GK",  28, 58, 15, 70, 86, 80,  60),
    ("Flekken",           "GK",  32, 56, 15, 70, 84, 76,  35),
    ("Raya",              "GK",  30, 58, 15, 74, 86, 78,  50),
    ("Vlachodimos",       "GK",  31, 56, 15, 68, 84, 78,  25),
    ("Ter Stegen",        "GK",  34, 56, 12, 80, 87, 76,  50),
    ("Oblak",             "GK",  33, 50, 12, 70, 89, 80,  50),
    ("Areola",            "GK",  34, 52, 12, 68, 84, 76,  20),
    ("Szczesny",          "GK",  36, 50, 12, 66, 86, 76,  10),
    ("Pope",              "GK",  34, 50, 12, 68, 86, 80,  30),
    ("Henderson J.",      "GK",  35, 48, 12, 68, 84, 78,  15),
    ("Neto P.",           "GK",  36, 52, 12, 66, 82, 74,  10),
    ("Guaita",            "GK",  38, 50, 12, 64, 82, 74,   5),
    ("Sanchez A.",        "GK",  30, 56, 15, 68, 84, 78,  35),
    ("Bounou",            "GK",  35, 52, 15, 66, 86, 78,  15),
    ("Nubel",             "GK",  29, 54, 15, 68, 84, 78,  40),
    ("Casteels",          "GK",  33, 52, 12, 68, 84, 76,  20),
    ("Kepa",              "GK",  31, 54, 12, 70, 84, 74,  20),
    ("de Gea",            "GK",  35, 48, 12, 66, 84, 72,   5),
]

def make_transfer_pool():
    seen = set(); pool = []
    for row in TRANSFER_POOL_DATA:
        if row[0] in seen: continue
        seen.add(row[0])
        pool.append(Player(*row))
    return pool

class Team:
    def __init__(self, name, budget, starters=None, subs=None):
        self.name = name; self.budget = budget
        self.starters = starters or []; self.subs = subs or []
        self.formation = "4-3-3"
        self.mentality = 50
        self.pass_dir  = 50
        self.tempo     = 50
        self.width     = 50
        self.press     = 50
        self.d_line    = 50
        self.wins = self.draws = self.losses = 0

    @property
    def points(self): return self.wins*3 + self.draws
    def all_players(self): return self.starters + self.subs
    def get_midfielders(self): return [p for p in self.starters if p.position in ['CM','CDM','CAM']]
    def get_attackers(self):   return [p for p in self.starters if p.position in ['ST','LW','RW']]
    def get_defenders(self):   return [p for p in self.starters if p.position in ['CB','FB']]
    def get_gk(self):          return next((p for p in self.starters if p.position == 'GK'), None)

    def to_dict(self):
        return {"name": self.name, "budget": self.budget, "formation": self.formation,
                "mentality": self.mentality, "pass_dir": self.pass_dir, "tempo": self.tempo,
                "width": self.width, "press": self.press, "d_line": self.d_line,
                "wins": self.wins, "draws": self.draws, "losses": self.losses,
                "starters": [p.to_dict() for p in self.starters],
                "subs":     [p.to_dict() for p in self.subs]}

# ── 4. 매치 엔진 ──────────────────────────────────────────────────────────
class SimulatorEngine:
    def __init__(self, root, log_callback, date_callback=None):
        self.root = root; self.log = log_callback; self.date_callback = date_callback
        self.game_date     = GameDate()
        self.transfer_pool = make_transfer_pool()
        self.opponents = [
            self._build_cpu("Man City",    90), self._build_cpu("Real Madrid",  89),
            self._build_cpu("Arsenal",     86), self._build_cpu("Liverpool",    87),
            self._build_cpu("Barcelona",   85), self._build_cpu("Bayern",       88),
            self._build_cpu("PSG",         87), self._build_cpu("Inter",        85),
        ]

    def _build_cpu(self, name, base):
        pos_list = ['GK','FB','CB','CB','FB','CDM','CM','CM','LW','ST','RW']
        starters = [Player(f"{name[:3]}{i+1}", pos, random.randint(22,32),
                           base, base, base, base, base, 50)
                    for i, pos in enumerate(pos_list)]
        t = Team(name, 500, starters, [])
        t.mentality = random.randint(30, 80); t.press = random.randint(40, 80)
        return t

    def _notify_date(self):
        if self.date_callback: self.date_callback(str(self.game_date))

    def setup_new_game(self):
        self.log("2026년, 무한한 자유도의 전술판이 열렸다. 너만의 팀을 만들어라.")
        starters = [
            Player("Onana",      "GK",  30, 62, 20, 82, 86, 82, 45),
            Player("Dalot",      "FB",  27, 85, 65, 80, 80, 76, 40),
            Player("L. Martinez","CB",  28, 78, 48, 76, 88, 84, 55),
            Player("De Ligt",    "CB",  26, 80, 48, 72, 88, 86, 50),
            Player("Mazraoui",   "FB",  28, 82, 62, 76, 82, 78, 40),
            Player("Ugarte",     "CDM", 25, 80, 68, 82, 86, 86, 55),
            Player("Mainoo",     "CM",  21, 80, 74, 86, 78, 74, 50),
            Player("Bruno",      "CAM", 31, 75, 85, 90, 65, 75, 80),
            Player("Rashford",   "LW",  28, 88, 84, 78, 46, 76, 60),
            Player("Garnacho",   "RW",  22, 86, 78, 74, 44, 64, 50),
            Player("Hojlund",    "ST",  23, 86, 84, 70, 42, 86, 60),
        ]
        subs = [
            Player("Amad",       "RW",  24, 84, 76, 74, 50, 68, 40),
            Player("Zirkzee",    "ST",  25, 78, 82, 78, 44, 80, 55),
            Player("Eriksen",    "CM",  34, 62, 76, 90, 58, 62, 25),
        ]
        self.my_team = Team("Manchester United", 250, starters, subs)
        self.game_date = GameDate(2026, 8, 8); self._notify_date(); self.save_game()

    def show_squad_detailed(self):
        squad_win = tk.Toplevel(self.root)
        squad_win.title("스쿼드 상세 전력망 (10-Attributes)")
        squad_win.geometry("1100x550")
        squad_win.configure(bg="#0d1117")
        cols = ("구분","이름","나이","포지션","OVR","속력","가속","골결","슛파워","짧패","시야","태클","대인방어","몸싸움","점프","체력")
        tree = ttk.Treeview(squad_win, columns=cols, show="headings", height=20)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=55 if c not in ["이름","구분","포지션"] else (120 if c=="이름" else 60), anchor="center")
        tree.column("이름", anchor="w")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for p in self.my_team.starters:
            tree.insert("","end", values=("선발", p.name, p.age, p.position, p.rating,
                                          p.spd, p.acc, p.fin, p.pow, p.spa, p.vis, p.tak, p.mrk, p.str, p.jum, p.stamina))
        for p in self.my_team.subs:
            tree.insert("","end", values=("후보", p.name, p.age, p.position, p.rating,
                                          p.spd, p.acc, p.fin, p.pow, p.spa, p.vis, p.tak, p.mrk, p.str, p.jum, p.stamina))
        t = self.my_team
        self.log(f"\n{'='*75}\n  [{self.game_date}] 팀: {t.name} | 예산: {t.budget}M | 승점: {t.points}pt\n{'='*75}")

    def substitute_player(self, si, bi):
        s, b = self.my_team.starters, self.my_team.subs
        if 0 <= si < len(s) and 0 <= bi < len(b):
            s[si], b[bi] = b[bi], s[si]
            self.log(f"[교체] {b[bi].name} OUT ↔ {s[si].name} IN")
        else: self.log("잘못된 번호다.")

    def set_player_instruction(self, is_starter, idx, instruction):
        lst = self.my_team.starters if is_starter else self.my_team.subs
        if 0 <= idx < len(lst):
            lst[idx].instruction = instruction
            self.log(f"[개인 지침] {lst[idx].name} → '{instruction}'")

    def transfer_buy(self, pool_idx, to_starter):
        if not self.game_date.is_transfer_window(): self.log("이적 시장이 닫혀 있다."); return
        if pool_idx < 0 or pool_idx >= len(self.transfer_pool): return
        player = self.transfer_pool[pool_idx]
        if self.my_team.budget < player.price: self.log(f"예산 부족! 필요: {player.price}M  보유: {self.my_team.budget}M"); return
        target = self.my_team.starters if to_starter else self.my_team.subs
        if len(target) >= (11 if to_starter else 12): self.log("해당 명단이 가득 찼다."); return
        self.my_team.budget -= player.price
        target.append(player); self.transfer_pool.pop(pool_idx)
        self.log(f"[영입] {player.name} ({player.age}세, OVR:{player.rating})  -{player.price}M  잔여: {self.my_team.budget}M")
        self.save_game()

    def transfer_sell(self, is_starter, idx):
        if not self.game_date.is_transfer_window(): self.log("이적 시장이 닫혀 있다."); return
        lst = self.my_team.starters if is_starter else self.my_team.subs
        if idx < 0 or idx >= len(lst): return
        player = lst.pop(idx)
        sell_price = int(player.price * random.uniform(0.6, 0.9))
        self.my_team.budget += sell_price; self.transfer_pool.append(player)
        self.log(f"[방출] {player.name}  +{sell_price}M  잔여: {self.my_team.budget}M")
        self.save_game()

    def play_match(self):
        if len(self.my_team.starters) < 11:
            self.log("선발이 11명이 아니다. 포메이션을 수정해라."); return
        home = self.my_team; away = random.choice(self.opponents)
        self.log(f"\n{'='*75}\n  📅 {self.game_date}  |  {home.name} VS {away.name}")
        self.log(f"  전술: {home.formation} | 성향: {home.mentality}/100 | 압박: {home.press}/100 | 템포: {home.tempo}/100")
        self.log(f"{'='*75}")
        hg = ag = 0
        for half in range(1, 3):
            offset = 0 if half == 1 else 45
            event_count = random.randint(12, 16) + int(home.tempo / 25)
            for t in sorted(random.sample(range(1, 45), k=event_count)):
                minute = offset + t
                home_mid = sum(p.vis + p.spa for p in (home.get_midfielders() or home.starters)) * (home.mentality / 50.0)
                away_mid = sum(p.vis + p.spa for p in (away.get_midfielders() or away.starters)) * (away.mentality / 50.0)
                atk = home if random.random() < (home_mid / (home_mid + away_mid + 1)) else away
                dfn = away if atk == home else home
                attacker = random.choice(atk.get_attackers() or atk.starters)
                passer   = random.choice(atk.get_midfielders() or atk.starters)
                defender = random.choice(dfn.get_defenders() or dfn.starters)
                gk       = dfn.get_gk()
                event_roll = random.random()
                if atk == home and random.randint(1, 100) < home.pass_dir:
                    if attacker.spd + attacker.str + random.randint(-15, 20) > defender.jum + (100 - dfn.d_line):
                        self.log(f"  {minute:2d}' | 🚀 다이렉트 패스! {attacker.name}이(가) 공중볼을 따냅니다!")
                        if attacker.fin + attacker.pow + random.randint(-10, 20) > (gk.tak + gk.jum if gk else 140):
                            self.log(f"  {minute:2d}' | ⚽ GOAL! 롱볼 전술 적중! {attacker.name}의 득점!"); hg += 1
                        else:
                            self.log(f"  {minute:2d}' | 💥 슛 파워가 약했습니다. 골키퍼 캐치.")
                    else:
                        self.log(f"  {minute:2d}' | 🛡️ 무의미한 롱볼. {defender.name}이(가) 헤더로 걷어냅니다.")
                elif event_roll < 0.40:
                    press_bonus = dfn.press / 5.0 if dfn == home else 10.0
                    if passer.vis + passer.spa + random.randint(-20, 20) > defender.mrk + defender.tak + press_bonus:
                        self.log(f"  {minute:2d}' | 🎯 {passer.name}의 창조적인 패스! (시야 {passer.vis})")
                        if attacker.fin + random.randint(-15, 20) > (gk.tak if gk else 70):
                            self.log(f"  {minute:2d}' | ⚽ GOAL! {attacker.name}의 골망을 가르는 슛!")
                            if atk == home: hg += 1
                            else: ag += 1
                        else:
                            self.log(f"  {minute:2d}' | 🥅 {attacker.name}의 아쉬운 슈팅! 빗나갑니다.")
                    else:
                        self.log(f"  {minute:2d}' | 🧱 강한 압박! {defender.name}이(가) 패스 길목을 완벽히 읽었습니다.")
                else:
                    self.log(f"  {minute:2d}' | {atk.name} 볼 점유 중... 치열한 허리 싸움이 전개됩니다.")
            if half == 1:
                self.log(f"\n  ─── 전반 종료 ───  {home.name} {hg} : {ag} {away.name}\n  ─── 후반 시작 ───\n")
        self.log(f"\n  최종 결과: {home.name} {hg} : {ag} {away.name}")
        if hg > ag:   home.wins   += 1; self.log("  ✅ 승리!")
        elif hg < ag: home.losses += 1; self.log("  ❌ 패배.")
        else:         home.draws  += 1; self.log("  🤝 무승부.")
        for p in home.starters:
            drain = 10 + int(home.tempo / 10) + int(home.press / 10) + random.randint(0, 5)
            p.stamina = max(0, p.stamina - drain)
            risk = (0.05 if p.age >= 33 else 0.02) + (0.04 if p.stamina < 30 else 0)
            if random.random() < risk:
                p.injured_days = random.randint(1, 4)
                self.log(f"  🚨 {p.name} 부상! ({p.injured_days}주 아웃)")
        for p in home.subs:
            p.stamina = min(100, p.stamina + (15 if p.age < 33 else 10))
        self.game_date.advance_match(home, self.transfer_pool); self._notify_date()
        for p in home.all_players():
            if p.injured_days > 0: p.injured_days -= 1
        self.save_game()

    def save_game(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        try:
            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump({"my_team": self.my_team.to_dict(),
                           "game_date": self.game_date.to_dict()}, f, ensure_ascii=False, indent=4)
        except: pass

    def load_game(self):
        if not os.path.exists(SAVE_FILE): self.setup_new_game(); return
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
            def parse_players(lst):
                res = []
                for p in lst:
                    det = p.get("detailed")
                    res.append(Player(p["name"], p["position"], p.get("age",25), 0,0,0,0,0,
                                      p.get("price",50), p.get("stamina",100), p.get("injured_days",0),
                                      p.get("instruction","기본"), loaded_stats=det))
                return res
            td = data["my_team"]
            self.my_team = Team(td["name"], td.get("budget",150),
                                parse_players(td.get("starters",[])),
                                parse_players(td.get("subs",[])))
            for attr, default in [("formation","4-3-3"),("mentality",50),("pass_dir",50),
                                   ("tempo",50),("width",50),("press",50),("d_line",50),
                                   ("wins",0),("draws",0),("losses",0)]:
                setattr(self.my_team, attr, td.get(attr, default))
            if "game_date" in data: self.game_date = GameDate.from_dict(data["game_date"])
            owned = {p.name for p in self.my_team.all_players()}
            self.transfer_pool = [p for p in self.transfer_pool if p.name not in owned]
            self._notify_date()
        except: self.setup_new_game()

# ── 5. GUI 모듈 ───────────────────────────────────────────────────────────
class TacticWindow(tk.Toplevel):
    def __init__(self, parent, engine):
        super().__init__(parent); self.engine = engine
        self.title("마스터 전술 보드 (1~100 스케일)")
        self.geometry("500x600"); self.configure(bg="#0d1117"); self._build()

    def _slider(self, parent, label_text, attr, desc_min, desc_max):
        f = tk.Frame(parent, bg="#0d1117"); f.pack(fill=tk.X, pady=8, padx=15)
        lbl_frame = tk.Frame(f, bg="#0d1117"); lbl_frame.pack(fill=tk.X)
        tk.Label(lbl_frame, text=label_text, bg="#0d1117", fg="#58a6ff", font=("Consolas",10,"bold")).pack(side=tk.LEFT)
        var = tk.IntVar(value=getattr(self.engine.my_team, attr))
        tk.Scale(f, from_=1, to=100, orient=tk.HORIZONTAL, variable=var,
                 bg="#0d1117", fg="white", highlightthickness=0,
                 troughcolor="#21262d", activebackground="#1f6feb").pack(fill=tk.X)
        desc_frame = tk.Frame(f, bg="#0d1117"); desc_frame.pack(fill=tk.X)
        tk.Label(desc_frame, text=desc_min, bg="#0d1117", fg="#8b949e", font=("Consolas",8)).pack(side=tk.LEFT)
        tk.Label(desc_frame, text=desc_max, bg="#0d1117", fg="#8b949e", font=("Consolas",8)).pack(side=tk.RIGHT)
        return var

    def _build(self):
        tk.Label(self, text="팀 세부 전술 조율 (1~100)", font=("Consolas",14,"bold"),
                 bg="#0d1117", fg="#f0c040").pack(pady=10)
        f0 = tk.Frame(self, bg="#0d1117"); f0.pack(fill=tk.X, pady=10, padx=15)
        tk.Label(f0, text="커스텀 포메이션:", bg="#0d1117", fg="#c9d1d9", font=("Consolas",10)).pack(side=tk.LEFT)
        self.v_form = tk.StringVar(value=self.engine.my_team.formation)
        tk.Entry(f0, textvariable=self.v_form, bg="#21262d", fg="white", font=("Consolas",10), width=15).pack(side=tk.LEFT, padx=10)
        self.v_mentality = self._slider(self, "팀 성향 (Mentality)",              "mentality", "텐백 우주방어",       "초공격적 (전원 공격)")
        self.v_pass_dir  = self._slider(self, "패스 다이렉트니스 (Pass Directness)","pass_dir",  "짧은 티키타카",       "다이렉트 롱볼")
        self.v_tempo     = self._slider(self, "경기 템포 (Tempo)",                 "tempo",     "매우 느리게",         "쉴새없이 몰아치기")
        self.v_width     = self._slider(self, "공격 폭 (Width)",                   "width",     "페널티박스 밀집",     "터치라인 끝까지 벌림")
        self.v_press     = self._slider(self, "압박 강도 (Pressing)",              "press",     "내려앉기 (체력보존)", "전방위 게겐프레싱")
        self.v_dline     = self._slider(self, "수비 라인 높이 (Defensive Line)",   "d_line",    "골대 앞 밀집",        "하프라인 위로 올림")
        tk.Button(self, text="전술 시스템 저장", width=20, bg="#1f6feb", fg="white",
                  font=("Consolas",10,"bold"), command=self._apply).pack(pady=15)

    def _apply(self):
        t = self.engine.my_team
        t.formation = self.v_form.get()
        t.mentality = self.v_mentality.get(); t.pass_dir = self.v_pass_dir.get()
        t.tempo     = self.v_tempo.get();     t.width    = self.v_width.get()
        t.press     = self.v_press.get();     t.d_line   = self.v_dline.get()
        messagebox.showinfo("전술 적용", f"포메이션 [{t.formation}] 및 세부 전술 수치가 적용되었습니다.", parent=self)


class InstructionWindow(tk.Toplevel):
    def __init__(self, parent, engine):
        super().__init__(parent); self.engine = engine
        self.title("개인 지침 부여"); self.geometry("740x500"); self.configure(bg="#0d1117"); self._build()

    def _build(self):
        cols = ("구분","번호","이름","포지션","현재 지침")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        for c in cols: self.tree.heading(c, text=c); self.tree.column(c, width=80, anchor="center")
        self.tree.column("이름", width=140, anchor="w"); self.tree.column("현재 지침", width=120, anchor="center")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0), pady=6)
        right = tk.Frame(self, bg="#0d1117", width=160); right.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=6)
        self.v_instr = tk.StringVar(value="기본")
        for ins in INSTRUCTIONS:
            tk.Radiobutton(right, text=ins, variable=self.v_instr, value=ins,
                           bg="#0d1117", fg="#c9d1d9", selectcolor="#1f6feb",
                           font=("Consolas",9), anchor="w", width=14).pack(pady=1)
        tk.Button(right, text="적용", bg="#1f6feb", fg="white", width=12, command=self._apply).pack(pady=10)
        self._refresh()

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, p in enumerate(self.engine.my_team.starters):
            self.tree.insert("","end", iid=f"s{i}", values=("선발", i+1, p.name, p.position, p.instruction))
        for i, p in enumerate(self.engine.my_team.subs):
            self.tree.insert("","end", iid=f"b{i}", values=("후보", i+1, p.name, p.position, p.instruction))

    def _apply(self):
        sel = self.tree.selection()
        if not sel: return
        iid = sel[0]
        self.engine.set_player_instruction(iid.startswith("s"), int(iid[1:]), self.v_instr.get())
        self._refresh()


class TransferWindow(tk.Toplevel):
    def __init__(self, parent, engine):
        super().__init__(parent); self.engine = engine
        self.title("이적 시장"); self.geometry("920x600"); self.configure(bg="#0d1117")
        self._build(); self._refresh()

    def _build(self):
        top = tk.Frame(self, bg="#0d1117"); top.pack(fill=tk.X, padx=10, pady=6)
        self.lbl_budget = tk.Label(top, text="", font=("Consolas",10), bg="#0d1117", fg="#f0c040")
        self.lbl_budget.pack(side=tk.RIGHT)
        self.lbl_window = tk.Label(top, text="", font=("Consolas",9), bg="#0d1117", fg="#aaa")
        self.lbl_window.pack(side=tk.RIGHT, padx=10)

        nb = ttk.Notebook(self); nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        # ── 영입 탭 ───────────────────────────────────────────────────────
        buy_frame = tk.Frame(nb, bg="#0d1117"); nb.add(buy_frame, text="영입 리스트")

        # 포지션 필터
        filter_frame = tk.Frame(buy_frame, bg="#0d1117"); filter_frame.pack(fill=tk.X, padx=6, pady=4)
        tk.Label(filter_frame, text="포지션 필터:", bg="#0d1117", fg="#c9d1d9",
                 font=("Consolas",9)).pack(side=tk.LEFT, padx=4)
        self.v_filter = tk.StringVar(value="전체")
        for pos in ["전체","GK","CB","FB","CDM","CM","CAM","LW","RW","ST"]:
            tk.Radiobutton(filter_frame, text=pos, variable=self.v_filter, value=pos,
                           command=self._refresh, bg="#0d1117", fg="#c9d1d9",
                           selectcolor="#1f6feb", font=("Consolas",8)).pack(side=tk.LEFT, padx=2)

        cols = ("번호","이름","나이","포지션","OVR","속력","골결","시야","태클","몸값(M)")
        self.buy_tree = ttk.Treeview(buy_frame, columns=cols, show="headings", height=16)
        for c in cols:
            self.buy_tree.heading(c, text=c)
            self.buy_tree.column(c, width=62, anchor="center")
        self.buy_tree.column("이름", width=145, anchor="w")
        sb = ttk.Scrollbar(buy_frame, orient=tk.VERTICAL, command=self.buy_tree.yview)
        self.buy_tree.configure(yscrollcommand=sb.set)
        self.buy_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        bf = tk.Frame(self, bg="#0d1117"); bf.pack(pady=4)
        tk.Button(bf, text="선발로 영입", width=14, bg="#1f6feb", fg="white",
                  command=lambda: self._buy(True)).pack(side=tk.LEFT, padx=6)
        tk.Button(bf, text="후보로 영입", width=14, bg="#238636", fg="white",
                  command=lambda: self._buy(False)).pack(side=tk.LEFT, padx=6)
        tk.Button(bf, text="새로고침",    width=10, command=self._refresh).pack(side=tk.LEFT, padx=6)

        # ── 방출 탭 ───────────────────────────────────────────────────────
        sell_frame = tk.Frame(nb, bg="#0d1117"); nb.add(sell_frame, text="방출 리스트")
        cols2 = ("구분","번호","이름","포지션","OVR","체력","예상 이적료")
        self.sell_tree = ttk.Treeview(sell_frame, columns=cols2, show="headings", height=16)
        for c in cols2:
            self.sell_tree.heading(c, text=c)
            self.sell_tree.column(c, width=90, anchor="center")
        self.sell_tree.column("이름", width=150, anchor="w")
        sb2 = ttk.Scrollbar(sell_frame, orient=tk.VERTICAL, command=self.sell_tree.yview)
        self.sell_tree.configure(yscrollcommand=sb2.set)
        self.sell_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)

        sf = tk.Frame(self, bg="#0d1117"); sf.pack(pady=4)
        tk.Button(sf, text="선수 매각", width=16, bg="#da3633", fg="white", command=self._sell).pack(side=tk.LEFT, padx=6)

    def _refresh(self):
        eng = self.engine
        is_open = eng.game_date.is_transfer_window()
        self.lbl_budget.config(text=f"예산: {eng.my_team.budget}M")
        self.lbl_window.config(
            text=f"이적 시장 {'열림 ✅' if is_open else '닫힘 ❌'}  ({eng.game_date})",
            fg="#3fb950" if is_open else "#f85149")

        pos_filter = self.v_filter.get()
        self.buy_tree.delete(*self.buy_tree.get_children())
        display_idx = 0
        for i, p in enumerate(eng.transfer_pool):
            if pos_filter != "전체" and p.position != pos_filter:
                continue
            display_idx += 1
            self.buy_tree.insert("","end", iid=str(i),
                values=(display_idx, p.name, p.age, p.position, p.rating,
                        p.spd, p.fin, p.vis, p.tak, p.price))

        self.sell_tree.delete(*self.sell_tree.get_children())
        for i, p in enumerate(eng.my_team.starters):
            self.sell_tree.insert("","end", iid=f"s{i}",
                values=("선발", i+1, p.name, p.position, p.rating, p.stamina, f"{int(p.price*0.75)}M"))
        for i, p in enumerate(eng.my_team.subs):
            self.sell_tree.insert("","end", iid=f"b{i}",
                values=("후보", i+1, p.name, p.position, p.rating, p.stamina, f"{int(p.price*0.75)}M"))

    def _buy(self, to_starter):
        sel = self.buy_tree.selection()
        if not sel: messagebox.showinfo("알림", "영입할 선수를 선택하라.", parent=self); return
        real_idx = int(sel[0])
        self.engine.transfer_buy(real_idx, to_starter)
        self._refresh()

    def _sell(self):
        sel = self.sell_tree.selection()
        if not sel: messagebox.showinfo("알림", "방출할 선수를 선택하라.", parent=self); return
        iid = sel[0]
        name = self.sell_tree.item(iid)["values"][2]
        if not messagebox.askyesno("방출 확인", f"{name}을(를) 방출하겠습니까?", parent=self): return
        self.engine.transfer_sell(iid.startswith("s"), int(iid[1:]))
        self._refresh()


class FM_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FM 2026 PRO - ULTIMATE FREEDOM")
        self.root.geometry("880x700"); self.root.configure(bg="#0d1117")

        bar = tk.Frame(self.root, bg="#161b22", pady=5); bar.pack(fill=tk.X)
        tk.Label(bar, text="⚽ FM 2026 PRO", font=("Consolas",11,"bold"),
                 bg="#161b22", fg="#58a6ff").pack(side=tk.LEFT, padx=12)
        self.lbl_date = tk.Label(bar, text="", font=("Consolas",10),
                                 bg="#161b22", fg="#f0c040")
        self.lbl_date.pack(side=tk.RIGHT, padx=12)

        self.text_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, width=118, height=33,
            font=("Consolas",9), bg="#0d1117", fg="#c9d1d9")
        self.text_area.pack(pady=6, padx=10, fill=tk.BOTH, expand=True)

        f1 = tk.Frame(self.root, bg="#0d1117"); f1.pack(pady=3)
        for txt, cmd in [
            ("스쿼드 전력 (10-스탯)", lambda: self.engine.show_squad_detailed()),
            ("전술 슬라이더 조절",    lambda: TacticWindow(self.root, self.engine)),
            ("개인 지침",             lambda: InstructionWindow(self.root, self.engine)),
            ("선수 교체",             self.cmd_substitute),
        ]:
            tk.Button(f1, text=txt, command=cmd, bg="#21262d", fg="#c9d1d9",
                      font=("Consolas",9), padx=8, pady=3).pack(side=tk.LEFT, padx=4)

        f2 = tk.Frame(self.root, bg="#0d1117"); f2.pack(pady=3)
        tk.Button(f2, text="다음 경기 진행", command=lambda: self.engine.play_match(),
                  width=15, bg="#1f6feb", fg="white", font=("Consolas",9,"bold")).pack(side=tk.LEFT, padx=4)
        tk.Button(f2, text="이적 시장", command=lambda: TransferWindow(self.root, self.engine),
                  width=12, bg="#8957e5", fg="white", font=("Consolas",9)).pack(side=tk.LEFT, padx=4)
        tk.Button(f2, text="게임 저장", command=lambda: self.engine.save_game(),
                  width=12, bg="#238636", fg="white", font=("Consolas",9)).pack(side=tk.LEFT, padx=4)

        self.engine = SimulatorEngine(self.root, self.write_log, self.update_date_label)
        self.engine.load_game()

    def update_date_label(self, date_str): self.lbl_date.config(text=f"📅 {date_str}")
    def write_log(self, text): self.text_area.insert(tk.END, text + "\n"); self.text_area.see(tk.END)

    def cmd_substitute(self):
        si = simpledialog.askinteger("OUT", "뺄 선발 번호 (1~11):", parent=self.root)
        if si:
            bi = simpledialog.askinteger("IN", "투입할 후보 번호 (1~12):", parent=self.root)
            if bi: self.engine.substitute_player(si-1, bi-1)


if __name__ == "__main__":
    if not is_admin():
        try: ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        except: pass
        sys.exit()
    root = tk.Tk()
    app = FM_GUI(root)
    root.mainloop()
