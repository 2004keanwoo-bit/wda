import os
import sys
import json
import random
import ctypes
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, ttk

SAVE_DIR = r"C:\MANAGER_SIMULATOR"
SAVE_FILE = os.path.join(SAVE_DIR, "save_data_v6.json")

TRANSFER_MONTHS = {1, 7, 8}

# ── 전술 옵션 정의 ────────────────────────────────────────────────────────────
FORMATIONS     = ["4-3-3", "4-2-3-1", "4-4-2", "3-5-2", "3-4-3", "5-3-2", "4-1-4-1"]
PASS_STYLES    = ["짧은 패스", "다이렉트", "혼합"]
PRESS_LINES    = ["전방 압박", "일반", "내려앉기"]
TEMPO_OPTIONS  = ["빠른 템포", "보통 템포", "느린 템포"]
WIDTH_OPTIONS  = ["넓은 공간 활용", "중앙 집중", "균형"]
DEFEND_OPTIONS = ["맨투맨 수비", "지역 수비", "혼합 수비"]
SET_PIECE_OPTS = ["짧은 코너", "크로스 위주", "직접 슈팅"]
COUNTER_OPTS   = ["빠른 역습", "점유 전환", "상황 판단"]

# 개인 지침 목록 (포지션 무관 / 포지션 별로 UI 안내만)
INSTRUCTIONS = ["기본", "공격 가담", "수비 대기", "오버래핑", "인버티드 런",
                "딥 라잉", "박스 투 박스", "자유 역할", "타깃맨", "압박 선봉"]

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ── 날짜 시스템 ──────────────────────────────────────────────────────────────
class GameDate:
    MONTH_NAMES = ["","1월","2월","3월","4월","5월","6월",
                   "7월","8월","9월","10월","11월","12월"]

    def __init__(self, year=2026, month=8, day=1):
        self.year  = year
        self.month = month
        self.day   = day

    def advance_match(self):
        self.day += 7
        if self.day > 28:
            self.day -= 28
            self.month += 1
            if self.month > 12:
                self.month = 1
                self.year += 1

    def is_transfer_window(self):
        return self.month in TRANSFER_MONTHS

    def season_str(self):
        return f"{self.year}/{self.year+1}" if self.month >= 8 else f"{self.year-1}/{self.year}"

    def __str__(self):
        return f"{self.year}년 {self.MONTH_NAMES[self.month]} {self.day}일"

    def to_dict(self):
        return {"year": self.year, "month": self.month, "day": self.day}

    @classmethod
    def from_dict(cls, d):
        return cls(d.get("year", 2026), d.get("month", 8), d.get("day", 1))


# ── 이적시장 선수 풀 (2026 기준) ─────────────────────────────────────────────
TRANSFER_POOL_DATA = [
    # name,               pos,   pac, sho, pas, def, phy, price(M)
    ("Yamal",             "RW",   93,  85,  82,  42,  68,  160),
    ("Wirtz",             "CAM",  84,  86,  90,  62,  74,  155),
    ("Guiu",              "ST",   83,  84,  72,  42,  80,   80),
    ("Musiala",           "CAM",  86,  83,  87,  60,  74,  140),
    ("Gavi",              "CM",   80,  74,  89,  76,  78,   90),
    ("Pedri",             "CM",   82,  78,  91,  74,  72,  110),
    ("Bellingham",        "CAM",  82,  87,  88,  72,  84,  160),
    ("Vinicius Jr",       "LW",   96,  86,  80,  40,  78,  160),
    ("Rodrygo",           "RW",   88,  83,  79,  45,  72,  110),
    ("Endrick",           "ST",   88,  84,  70,  42,  82,   90),
    ("Raphinha",          "RW",   90,  84,  78,  50,  76,  100),
    ("Salah",             "RW",   88,  87,  78,  46,  74,   90),
    ("Saka",              "RW",   88,  84,  84,  60,  74,  110),
    ("Bukayo Saka",       "RW",   88,  84,  84,  60,  74,  110),
    ("Odegaard",          "CAM",  80,  83,  92,  62,  72,  100),
    ("Rice",              "CDM",  80,  70,  84,  86,  86,  100),
    ("Caicedo",           "CDM",  84,  66,  80,  86,  85,   90),
    ("Mainoo",            "CM",   80,  73,  85,  78,  74,   70),
    ("Kobbie Mainoo",     "CM",   80,  73,  85,  78,  74,   70),
    ("Zirkzee",           "ST",   76,  82,  78,  44,  80,   65),
    ("Isak",              "ST",   90,  84,  74,  42,  82,  110),
    ("Gyokeres",          "ST",   84,  88,  72,  44,  88,  100),
    ("Kvaratskhelia",     "LW",   88,  82,  80,  48,  76,  120),
    ("Diaz",              "LW",   88,  80,  76,  52,  78,   80),
    ("Coman",             "LW",   92,  78,  76,  52,  76,   55),
    ("Musiala",           "CAM",  86,  83,  87,  60,  74,  140),
    ("Kimmich",           "CM",   76,  72,  90,  86,  78,   85),
    ("Tah",               "CB",   78,  52,  76,  88,  86,   60),
    ("Upamecano",         "CB",   82,  48,  74,  87,  88,   65),
    ("Davies",            "FB",   92,  66,  78,  80,  82,   75),
    ("Theo Hernandez",    "FB",   92,  68,  80,  80,  86,   85),
    ("Hakimi",            "FB",   93,  70,  80,  78,  80,   90),
    ("Alexander-Arnold",  "CM",   86,  74,  92,  74,  76,   85),
    ("Van Dijk",          "CB",   82,  56,  74,  90,  88,   70),
    ("Alisson",           "GK",   62,  15,  74,  91,  80,   70),
    ("Ederson",           "GK",   58,  20,  80,  88,  80,   60),
    ("Maignan",           "GK",   65,  14,  72,  88,  82,   70),
    ("Donnarumma",        "GK",   60,  12,  68,  89,  86,   65),
    ("Osimhen",           "ST",   90,  86,  70,  38,  86,  110),
    ("Lookman",           "LW",   88,  82,  76,  48,  74,   80),
    ("De Bruyne",         "CM",   76,  85,  94,  62,  78,   80),
    ("Kane",              "ST",   76,  92,  84,  42,  80,   90),
    ("Haaland",           "ST",   87,  93,  65,  40,  90,  180),
    ("Doku",              "LW",   96,  76,  74,  42,  76,   80),
    ("Nunes",             "CM",   84,  74,  82,  76,  82,   75),
    ("Gundogan",          "CM",   72,  80,  90,  66,  72,   40),
    ("Rudiger",           "CB",   82,  58,  68,  88,  90,   50),
    ("Camavinga",         "CM",   84,  72,  82,  80,  80,   90),
    ("Tchouameni",        "CDM",  80,  68,  78,  86,  84,   85),
]

def make_transfer_pool():
    seen = set()
    pool = []
    for row in TRANSFER_POOL_DATA:
        name = row[0]
        if name in seen:
            continue
        seen.add(name)
        name_, pos, pac, sho, pas, def_, phy, price = row
        pool.append(Player(name_, pos, pac, sho, pas, def_, phy, price))
    return pool


# ── Player ────────────────────────────────────────────────────────────────────
class Player:
    def __init__(self, name, position, pac, sho, pas, def_, phy, price,
                 stamina=100, injured_days=0, instruction="기본"):
        self.name        = name
        self.position    = position
        self.pac         = pac
        self.sho         = sho
        self.pas         = pas
        self.def_        = def_
        self.phy         = phy
        self.price       = price
        self.stamina     = stamina
        self.injured_days = injured_days
        self.instruction = instruction

    @property
    def rating(self):
        if self.position in ['ST','LW','RW']:
            v = self.sho*0.40 + self.pac*0.30 + self.pas*0.10 + self.phy*0.20
        elif self.position in ['CM','CAM','CDM']:
            v = self.pas*0.40 + self.def_*0.20 + self.sho*0.20 + self.phy*0.20
        elif self.position in ['CB','FB']:
            v = self.def_*0.40 + self.phy*0.30 + self.pac*0.20 + self.pas*0.10
        elif self.position == 'GK':
            v = self.def_*0.60 + self.phy*0.40
        else:
            v = (self.pac+self.sho+self.pas+self.def_+self.phy)/5
        return int(v)

    def get_effective_rating(self):
        if self.injured_days > 0:
            return 0
        stamina_pen = max(0.4, self.stamina / 100.0)
        bonus = 1.0
        instr = self.instruction
        pos   = self.position
        # 개인 지침별 포지션 시너지
        if instr == "공격 가담"   and pos in ['CM','FB','CDM']:  bonus = 1.06
        if instr == "수비 대기"   and pos in ['CM','FB','CAM']:  bonus = 1.05
        if instr == "오버래핑"    and pos == 'FB':                bonus = 1.07
        if instr == "인버티드 런" and pos in ['LW','RW']:         bonus = 1.07
        if instr == "딥 라잉"     and pos == 'ST':                bonus = 1.05
        if instr == "박스 투 박스" and pos == 'CM':               bonus = 1.06
        if instr == "타깃맨"      and pos == 'ST':                bonus = 1.07
        if instr == "압박 선봉"   and pos in ['ST','LW','RW']:    bonus = 1.05
        return self.rating * stamina_pen * bonus

    def to_dict(self):
        return {
            "name": self.name, "position": self.position,
            "pac": self.pac, "sho": self.sho, "pas": self.pas,
            "def": self.def_, "phy": self.phy, "price": self.price,
            "stamina": self.stamina, "injured_days": self.injured_days,
            "instruction": self.instruction,
        }


# ── Team ──────────────────────────────────────────────────────────────────────
class Team:
    def __init__(self, name, budget, starters=None, subs=None):
        self.name      = name
        self.budget    = budget
        self.starters  = starters or []
        self.subs      = subs or []
        # 기본 전술
        self.formation    = "4-3-3"
        self.passing_style = "혼합"
        self.pressing_line = "일반"
        # 세부 전술
        self.tempo        = "보통 템포"
        self.width        = "균형"
        self.defend_style = "지역 수비"
        self.set_piece    = "크로스 위주"
        self.counter      = "상황 판단"
        # 시즌 통계
        self.wins = self.draws = self.losses = 0
        self.goals_for = self.goals_against = 0

    @property
    def points(self):
        return self.wins*3 + self.draws

    def tactic_power_bonus(self):
        """세부 전술 조합에 따른 전력 배율"""
        b = 1.0
        if self.passing_style == "짧은 패스":  b *= 1.03
        if self.pressing_line == "전방 압박":  b *= 1.03
        if self.tempo  == "빠른 템포":         b *= 1.02
        if self.width  == "넓은 공간 활용":    b *= 1.02
        if self.defend_style == "맨투맨 수비": b *= 1.02
        if self.counter == "빠른 역습":        b *= 1.02
        return b

    def get_match_power(self):
        if len(self.starters) < 11:
            return 0
        base = sum(p.get_effective_rating() for p in self.starters) / 11
        return base * self.tactic_power_bonus()

    def all_players(self):
        return self.starters + self.subs

    def get_attackers(self):
        return [p for p in self.starters if p.position in ['ST','LW','RW','CAM']]

    def get_midfielders(self):
        return [p for p in self.starters if p.position in ['CM','CDM','CAM']]

    def get_defenders(self):
        return [p for p in self.starters if p.position in ['CB','FB']]

    def get_gk(self):
        g = [p for p in self.starters if p.position == 'GK']
        return g[0] if g else None

    def to_dict(self):
        return {
            "name": self.name, "budget": self.budget,
            "formation": self.formation, "passing_style": self.passing_style,
            "pressing_line": self.pressing_line,
            "tempo": self.tempo, "width": self.width,
            "defend_style": self.defend_style, "set_piece": self.set_piece,
            "counter": self.counter,
            "wins": self.wins, "draws": self.draws, "losses": self.losses,
            "goals_for": self.goals_for, "goals_against": self.goals_against,
            "starters": [p.to_dict() for p in self.starters],
            "subs":     [p.to_dict() for p in self.subs],
        }


# ── 경기 중계 ─────────────────────────────────────────────────────────────────
class MatchCommentator:
    ATTACK_EVENTS = [
        "{attacker}가 왼쪽 측면 드리블로 수비를 제치고 올라간다!",
        "{attacker}가 중원에서 전방으로 날카로운 스루 패스!",
        "{attacker}가 박스 근처에서 결정적인 기회를 잡았다!",
        "{attacker}가 오른쪽 사이드를 빠르게 파고든다!",
        "{attacker}가 헤더 경합에서 이기며 공을 이어받는다!",
        "코너킥! {attacker}가 공을 올린다...",
        "{attacker}가 프리킥 자리를 잡는다. 위협적인 거리다!",
        "{attacker}가 원투패스로 수비 뒤 공간을 노린다!",
        "{attacker}가 돌아서며 중거리 슛 자리를 잡는다!",
        "{attacker}가 박스 안으로 파고들며 찬스를 만든다!",
        "{attacker}가 수비수를 제치고 1대1 상황을 만들었다!",
        "{attacker}의 크로스가 박스 안으로 정확하게 떨어진다!",
    ]
    SHOT_SAVED = [
        "슈팅! {gk}가 몸을 던져 막아낸다! 아깝다!",
        "강렬한 슈팅이지만 {gk}가 정면으로 잡아낸다!",
        "{gk}의 신들린 반응 세이브! 구석을 노렸지만 막혔다!",
        "슈팅이 구석으로... {gk}가 뻗어서 코너 처리!",
        "{gk}가 원핸드 세이브! 훌륭한 반응이다!",
        "{gk}가 발로 막아냈다! 기적적인 세이브!",
    ]
    SHOT_MISS = [
        "슈팅은 크게 빗나가 골대 밖으로!",
        "슈팅이 크로스바를 강타하며 튕겨 나온다!",
        "너무 급하게 찼다. 슈팅이 하늘로 솟구쳐 버린다!",
        "결정적인 기회였지만 슈팅이 골포스트를 강타!",
        "마지막 수비수에게 걷혀 나간다. 아쉬운 장면!",
        "오프사이드! 득점이 취소된다.",
    ]
    GOAL_TEXTS = [
        "골!!!!! {scorer}의 환상적인 마무리! {home} {hg}:{ag} {away}",
        "골!!!!! {scorer}가 해냈다! 골망이 흔들린다! {home} {hg}:{ag} {away}",
        "골!!!!! 완벽한 위치 선정, {scorer}가 차갑게 마무리! {home} {hg}:{ag} {away}",
        "골!!!!! {scorer}의 강렬한 슈팅이 골키퍼 손을 뚫고 들어간다! {home} {hg}:{ag} {away}",
        "골!!!!! {scorer}! 기가 막힌 골이다! {home} {hg}:{ag} {away}",
        "골!!!!! 헤더! {scorer}가 정확하게 꽂아넣는다! {home} {hg}:{ag} {away}",
    ]
    FOUL_TEXTS = [
        "{fouler}의 거친 태클! 파울 선언.",
        "{fouler}가 뒤에서 잡아당겼다. 프리킥 허용.",
        "반칙! {fouler}가 경고를 받는다. 옐로카드!",
        "{fouler}의 슬라이딩 태클이 늦게 들어갔다. 파울.",
        "{fouler}가 핸드볼! 페널티킥 선언!",
    ]
    POSSESSION_TEXTS = [
        "양 팀이 중원에서 볼 경합을 펼치고 있다.",
        "{team}이 점유율을 끌어올리며 경기를 지배하려 한다.",
        "{team}의 짧은 패스 연결이 이어지고 있다.",
        "{team} 수비진이 안정적으로 빌드업 중이다.",
        "상대 진영에서 {team}이 공을 오래 돌린다.",
        "{team}의 강도 높은 압박이 상대를 괴롭히고 있다.",
    ]
    # 전술 연계 이벤트 문구
    TACTIC_EVENTS = {
        "빠른 역습":      "{attacker}가 공을 빼앗자마자 빠른 역습으로 달려나간다!",
        "오버래핑":       "{attacker}가 측면 오버래핑으로 수비 뒤 공간을 파고든다!",
        "타깃맨":         "{attacker}가 몸을 이용해 공을 받아낸다. 타깃맨 플레이!",
        "인버티드 런":    "{attacker}가 안쪽으로 파고들며 슈팅 각도를 만든다!",
        "전방 압박":      "전방 압박! 상대 골키퍼를 압박해 볼을 빼앗는다!",
        "넓은 공간 활용": "{attacker}가 넓게 벌어진 공간으로 볼을 받아 측면 돌파!",
    }

    @staticmethod
    def random_player_name(team, role="any"):
        if   role == "attacker": pool = team.get_attackers() or team.starters
        elif role == "defender": pool = team.get_defenders() or team.starters
        elif role == "gk":
            gk = team.get_gk()
            return gk.name if gk else "골키퍼"
        else: pool = team.starters
        return random.choice(pool).name if pool else "선수"

    @classmethod
    def attack_commentary(cls, atk, dfn):
        attacker = cls.random_player_name(atk, "attacker")
        gk       = cls.random_player_name(dfn, "gk")
        # 전술 연계 이벤트 20% 확률로 삽입
        tactic_key = None
        if random.random() < 0.20:
            candidates = []
            if atk.counter == "빠른 역습":        candidates.append("빠른 역습")
            if atk.width   == "넓은 공간 활용":   candidates.append("넓은 공간 활용")
            if atk.pressing_line == "전방 압박":   candidates.append("전방 압박")
            for p in atk.starters:
                if p.instruction in ("오버래핑","타깃맨","인버티드 런"):
                    candidates.append(p.instruction)
                    attacker = p.name
                    break
            if candidates:
                tactic_key = random.choice(candidates)
        if tactic_key and tactic_key in cls.TACTIC_EVENTS:
            line = cls.TACTIC_EVENTS[tactic_key].format(attacker=attacker)
        else:
            line = random.choice(cls.ATTACK_EVENTS).format(attacker=attacker)
        return line, attacker, gk

    @classmethod
    def foul_commentary(cls, fouling_team):
        fouler = cls.random_player_name(fouling_team, "defender")
        return random.choice(cls.FOUL_TEXTS).format(fouler=fouler)

    @classmethod
    def possession_commentary(cls, team):
        return random.choice(cls.POSSESSION_TEXTS).format(team=team.name)


# ── 엔진 ──────────────────────────────────────────────────────────────────────
class SimulatorEngine:
    def __init__(self, log_callback, date_callback=None):
        self.my_team      = None
        self.log          = log_callback
        self.date_callback = date_callback
        self.game_date    = GameDate()
        self.transfer_pool = make_transfer_pool()
        self.opponents    = [
            self._build_cpu_team("Manchester City",  91),
            self._build_cpu_team("Real Madrid",      90),
            self._build_cpu_team("Arsenal",          87),
            self._build_cpu_team("Bayern Munich",    88),
            self._build_cpu_team("Barcelona",        88),
            self._build_cpu_team("PSG",              89),
            self._build_cpu_team("Liverpool",        87),
            self._build_cpu_team("Inter Milan",      86),
        ]

    def _build_cpu_team(self, name, base):
        positions = ['GK','FB','CB','CB','FB','CDM','CM','CM','LW','ST','RW']
        starters  = [
            Player(f"{name[:3].upper()}{i+1}", pos,
                   base+random.randint(-5,5), base+random.randint(-5,5),
                   base+random.randint(-5,5), base+random.randint(-5,5),
                   base+random.randint(-5,5), 50)
            for i, pos in enumerate(positions)
        ]
        return Team(name, 500, starters, [])

    def _notify_date(self):
        if self.date_callback:
            self.date_callback(str(self.game_date))

    # ── 2026 초기 스쿼드 (맨체스터 유나이티드 2026 기준) ─────────────────────
    def setup_new_game(self):
        self.log("2026년, 새로운 감독으로 부임했다.")
        starters = [
            # GK
            Player("Onana",          "GK",  62, 20, 82, 86, 82,  45),
            # FB
            Player("Mazraoui",       "FB",  82, 62, 76, 82, 78,  40),
            Player("Dalot",          "FB",  85, 65, 80, 80, 76,  40),
            # CB
            Player("Lisandro Martinez","CB",78, 48, 76, 88, 84,  55),
            Player("De Ligt",        "CB",  80, 48, 72, 88, 86,  50),
            # CDM
            Player("Ugarte",         "CDM", 80, 68, 82, 86, 86,  55),
            # CM
            Player("Mainoo",         "CM",  80, 74, 86, 78, 74,  50),
            Player("Mount",          "CM",  78, 80, 84, 66, 72,  45),
            # LW / RW
            Player("Rashford",       "LW",  88, 84, 78, 46, 76,  60),
            Player("Garnacho",       "RW",  86, 78, 74, 44, 64,  50),
            # ST
            Player("Hojlund",        "ST",  86, 84, 70, 42, 86,  60),
        ]
        subs = [
            Player("Bayindir",       "GK",  52, 14, 68, 78, 76,  15),
            Player("Wan-Bissaka",    "FB",  84, 42, 66, 86, 76,  25),
            Player("Maguire",        "CB",  56, 50, 66, 84, 88,  25),
            Player("Eriksen",        "CM",  62, 76, 90, 58, 62,  25),
            Player("Amad Diallo",    "RW",  84, 76, 74, 50, 68,  40),
            Player("Zirkzee",        "ST",  78, 82, 78, 44, 80,  55),
            Player("Antony",         "LW",  82, 72, 74, 46, 64,  30),
        ]
        self.my_team = Team("Manchester United", 150, starters, subs)
        self.game_date = GameDate(2026, 8, 8)
        self._notify_date()
        self.save_game()

    # ── 스쿼드 보기 ───────────────────────────────────────────────────────────
    def show_squad_detailed(self):
        t = self.my_team
        self.log(f"\n{'='*65}")
        self.log(f"  [{self.game_date}]  시즌: {self.game_date.season_str()}")
        self.log(f"  팀: {t.name}  |  예산: {t.budget}M  |  승점: {t.points}pt  ({t.wins}승 {t.draws}무 {t.losses}패)  GD:{t.goals_for-t.goals_against:+d}")
        self.log(f"  포메이션: {t.formation}")
        self.log(f"  패스: {t.passing_style}  |  압박: {t.pressing_line}  |  템포: {t.tempo}")
        self.log(f"  폭: {t.width}  |  수비: {t.defend_style}  |  세트피스: {t.set_piece}  |  역습: {t.counter}")
        self.log(f"  전술 보너스 배율: x{t.tactic_power_bonus():.3f}")
        self.log(f"{'='*65}")
        self.log("  [선발]")
        for i, p in enumerate(t.starters):
            cond = f"체력:{p.stamina:3d}  " + (f"부상({p.injured_days}턴)" if p.injured_days > 0 else "정상      ")
            self.log(f"  {i+1:2d}. [{p.position:<3}] {p.name:<18} OVR:{p.rating}  {cond} 지침:{p.instruction}")
        self.log("  [후보]")
        for i, p in enumerate(t.subs):
            cond = f"체력:{p.stamina:3d}  " + (f"부상({p.injured_days}턴)" if p.injured_days > 0 else "정상      ")
            self.log(f"  {i+1:2d}. [{p.position:<3}] {p.name:<18} OVR:{p.rating}  {cond} 지침:{p.instruction}")
        self.log(f"\n  실질 전력: {t.get_match_power():.1f}\n")

    # ── 교체 ──────────────────────────────────────────────────────────────────
    def substitute_player(self, si, bi):
        s, b = self.my_team.starters, self.my_team.subs
        if 0 <= si < len(s) and 0 <= bi < len(b):
            s[si], b[bi] = b[bi], s[si]
            self.log(f"[교체] {b[bi].name} OUT  ↔  {s[si].name} IN")
        else:
            self.log("잘못된 번호다.")

    # ── 기본 전술 ─────────────────────────────────────────────────────────────
    def set_team_tactic(self, formation, passing, pressing):
        ok_f = formation in FORMATIONS
        ok_p = passing   in PASS_STYLES
        ok_d = pressing  in PRESS_LINES
        if ok_f and ok_p and ok_d:
            self.my_team.formation     = formation
            self.my_team.passing_style = passing
            self.my_team.pressing_line = pressing
            self.log(f"[기본 전술] 포메이션: {formation} | 패스: {passing} | 압박: {pressing}")
        else:
            errs = []
            if not ok_f: errs.append(f"포메이션 오류 (선택: {' / '.join(FORMATIONS)})")
            if not ok_p: errs.append(f"패스 오류 (선택: {' / '.join(PASS_STYLES)})")
            if not ok_d: errs.append(f"압박 오류 (선택: {' / '.join(PRESS_LINES)})")
            self.log("  ".join(errs))

    # ── 세부 전술 ─────────────────────────────────────────────────────────────
    def set_detail_tactic(self, tempo, width, defend, set_piece, counter):
        ok = [tempo in TEMPO_OPTIONS, width in WIDTH_OPTIONS,
              defend in DEFEND_OPTIONS, set_piece in SET_PIECE_OPTS,
              counter in COUNTER_OPTS]
        if all(ok):
            t = self.my_team
            t.tempo        = tempo
            t.width        = width
            t.defend_style = defend
            t.set_piece    = set_piece
            t.counter      = counter
            self.log(f"[세부 전술] 템포: {tempo} | 폭: {width} | 수비: {defend} | 세트피스: {set_piece} | 역습: {counter}")
        else:
            self.log("잘못된 전술 값이 있다. 다시 확인하라.")

    # ── 개인 지침 ─────────────────────────────────────────────────────────────
    def set_player_instruction(self, is_starter, idx, instruction):
        lst = self.my_team.starters if is_starter else self.my_team.subs
        if 0 <= idx < len(lst):
            lst[idx].instruction = instruction
            self.log(f"[개인 지침] {lst[idx].name} → '{instruction}'")
        else:
            self.log("잘못된 번호다.")

    # ── 경기 진행 ─────────────────────────────────────────────────────────────
    def play_match(self):
        if len(self.my_team.starters) < 11:
            self.log("선발이 11명이 아니다. 경기 불가.")
            return

        home = self.my_team
        away = random.choice(self.opponents)
        hp   = home.get_match_power()
        ap   = away.get_match_power()
        total = hp + ap if hp + ap > 0 else 1

        self.log("\n" + "=" * 65)
        self.log(f"  📅 {self.game_date}  |  시즌 {self.game_date.season_str()}")
        self.log(f"  ⚽  {home.name}  VS  {away.name}")
        self.log(f"  포메이션: {home.formation}  |  패스: {home.passing_style}  |  압박: {home.pressing_line}")
        self.log(f"  템포: {home.tempo}  |  폭: {home.width}  |  수비: {home.defend_style}  |  역습: {home.counter}")
        self.log(f"  팀 전력  {home.name}: {hp:.1f}  /  {away.name}: {ap:.1f}")
        self.log("=" * 65)

        hg = ag = 0
        scorers = []

        for half in range(1, 3):
            self.log(f"\n─── {'전반' if half==1 else '후반'} 시작 ───")
            offset = 0 if half == 1 else 45
            for t in sorted(random.sample(range(1, 45), k=random.randint(9, 13))):
                minute = offset + t
                if random.random() < hp / total:
                    atk, dfn = home, away
                else:
                    atk, dfn = away, home

                roll = random.random()
                if roll < 0.08:
                    self.log(f"  {minute:2d}' | {MatchCommentator.foul_commentary(dfn)}")
                elif roll < 0.25:
                    self.log(f"  {minute:2d}' | {MatchCommentator.possession_commentary(atk)}")
                else:
                    line, scorer_name, gk_name = MatchCommentator.attack_commentary(atk, dfn)
                    self.log(f"  {minute:2d}' | {line}")
                    shot_chance = 0.55 if atk.get_match_power() >= dfn.get_match_power() else 0.42
                    if random.random() < shot_chance:
                        ap2 = atk.get_match_power()
                        dp2 = dfn.get_match_power()
                        gp  = (ap2 / (ap2 + dp2 + 1)) * 0.46
                        out = random.random()
                        if out < gp:
                            if atk == home: hg += 1
                            else:           ag += 1
                            scorers.append((minute, atk.name, scorer_name))
                            self.log(f"  {minute:2d}' | " + random.choice(MatchCommentator.GOAL_TEXTS).format(
                                scorer=scorer_name, home=home.name, hg=hg, ag=ag, away=away.name))
                        elif out < gp + 0.25:
                            self.log(f"  {minute:2d}' | " + random.choice(MatchCommentator.SHOT_SAVED).format(gk=gk_name))
                        else:
                            self.log(f"  {minute:2d}' | " + random.choice(MatchCommentator.SHOT_MISS))

            if half == 1:
                self.log(f"\n  ─── 전반 종료 ───  {home.name} {hg} : {ag} {away.name}")
                self.log(f"  ─── 후반 시작 ───\n")

        self.log("\n" + "=" * 65)
        self.log(f"  최종  {home.name}  {hg} : {ag}  {away.name}")
        self.log("=" * 65)
        if scorers:
            self.log("  ⚽ 득점 기록")
            for m, team, sc in scorers:
                self.log(f"    {m:2d}'  {sc}  ({team})")

        if hg > ag:
            self.log(f"\n  ✅ 승리!"); home.wins += 1
        elif hg < ag:
            self.log(f"\n  ❌ 패배."); home.losses += 1
        else:
            self.log(f"\n  🤝 무승부."); home.draws += 1
        home.goals_for    += hg
        home.goals_against += ag

        self.log("\n  ── 경기 후 선수 상태 ──")
        injured_any = False
        for p in home.starters:
            drain = random.randint(15, 25)
            if home.pressing_line == "전방 압박": drain += 8
            if home.tempo         == "빠른 템포": drain += 5
            p.stamina = max(0, p.stamina - drain)
            if random.random() < 0.03:
                p.injured_days = random.randint(1, 3)
                self.log(f"  🚨 {p.name} 부상! ({p.injured_days}턴 아웃)")
                injured_any = True
        for p in home.subs:
            p.stamina = min(100, p.stamina + 10)
        if not injured_any:
            self.log("  전원 부상 없이 마쳤다.")

        self.game_date.advance_match()
        self._notify_date()

        for p in home.all_players():
            if p.injured_days > 0:
                p.injured_days -= 1

        if self.game_date.is_transfer_window():
            self.log(f"\n  🏪 이적 시장이 열려 있다! ({self.game_date})")
        self.log("")
        self.save_game()

    # ── 이적 영입 ─────────────────────────────────────────────────────────────
    def transfer_buy(self, pool_idx, to_starter):
        if not self.game_date.is_transfer_window():
            self.log("이적 시장이 닫혀 있다. (1월 / 7~8월만 가능)")
            return
        if pool_idx < 0 or pool_idx >= len(self.transfer_pool):
            self.log("잘못된 번호다.")
            return
        player = self.transfer_pool[pool_idx]
        if self.my_team.budget < player.price:
            self.log(f"예산 부족!  필요: {player.price}M  보유: {self.my_team.budget}M")
            return
        target   = self.my_team.starters if to_starter else self.my_team.subs
        max_size = 11 if to_starter else 10
        if len(target) >= max_size:
            self.log(f"{'선발' if to_starter else '후보'} 인원이 가득 찼다. 먼저 방출하라.")
            return
        self.my_team.budget -= player.price
        target.append(player)
        self.transfer_pool.pop(pool_idx)
        self.log(f"[영입] {player.name} ({player.position}, OVR:{player.rating})  -{player.price}M  잔여: {self.my_team.budget}M")
        self.save_game()

    # ── 이적 방출 ─────────────────────────────────────────────────────────────
    def transfer_sell(self, is_starter, idx):
        if not self.game_date.is_transfer_window():
            self.log("이적 시장이 닫혀 있다.")
            return
        lst = self.my_team.starters if is_starter else self.my_team.subs
        if idx < 0 or idx >= len(lst):
            self.log("잘못된 번호다.")
            return
        player     = lst.pop(idx)
        sell_price = int(player.price * random.uniform(0.6, 0.9))
        self.my_team.budget += sell_price
        self.transfer_pool.append(player)
        self.log(f"[방출] {player.name}  +{sell_price}M  잔여: {self.my_team.budget}M")
        self.save_game()

    # ── 저장/로드 ─────────────────────────────────────────────────────────────
    def save_game(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        try:
            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump({"my_team": self.my_team.to_dict(),
                           "game_date": self.game_date.to_dict()}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.log(f"저장 오류: {e}")

    def load_game(self):
        if not os.path.exists(SAVE_FILE):
            self.setup_new_game()
            return
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            def parse_players(lst):
                return [Player(
                    p["name"], p["position"],
                    p.get("pac",70), p.get("sho",70), p.get("pas",70),
                    p.get("def",70), p.get("phy",70), p.get("price",50),
                    p.get("stamina",100), p.get("injured_days",0), p.get("instruction","기본")
                ) for p in lst]

            td = data["my_team"]
            self.my_team = Team(td["name"], td.get("budget", 150),
                                parse_players(td.get("starters",[])),
                                parse_players(td.get("subs",[])))
            self.my_team.formation    = td.get("formation",    "4-3-3")
            self.my_team.passing_style = td.get("passing_style","혼합")
            self.my_team.pressing_line = td.get("pressing_line","일반")
            self.my_team.tempo        = td.get("tempo",        "보통 템포")
            self.my_team.width        = td.get("width",        "균형")
            self.my_team.defend_style = td.get("defend_style", "지역 수비")
            self.my_team.set_piece    = td.get("set_piece",    "크로스 위주")
            self.my_team.counter      = td.get("counter",      "상황 판단")
            self.my_team.wins         = td.get("wins",  0)
            self.my_team.draws        = td.get("draws", 0)
            self.my_team.losses       = td.get("losses",0)
            self.my_team.goals_for    = td.get("goals_for",    0)
            self.my_team.goals_against= td.get("goals_against",0)

            if "game_date" in data:
                self.game_date = GameDate.from_dict(data["game_date"])

            owned = {p.name for p in self.my_team.all_players()}
            self.transfer_pool = [p for p in self.transfer_pool if p.name not in owned]

            self._notify_date()
            self.log("데이터 로드 완료.")
        except Exception:
            self.setup_new_game()


# ── 전술 설정 창 ──────────────────────────────────────────────────────────────
class TacticWindow(tk.Toplevel):
    def __init__(self, parent, engine: SimulatorEngine):
        super().__init__(parent)
        self.engine = engine
        self.title("전술 설정")
        self.geometry("560x560")
        self.configure(bg="#0d1117")
        self.resizable(False, False)
        self._build()

    def _row(self, parent, label, options, attr):
        f = tk.Frame(parent, bg="#0d1117")
        f.pack(fill=tk.X, pady=4, padx=10)
        tk.Label(f, text=f"{label}", width=14, anchor="w",
                 bg="#0d1117", fg="#8b949e", font=("Consolas",9)).pack(side=tk.LEFT)
        var = tk.StringVar(value=getattr(self.engine.my_team, attr))
        for opt in options:
            rb = tk.Radiobutton(f, text=opt, variable=var, value=opt,
                                bg="#0d1117", fg="#c9d1d9",
                                selectcolor="#1f6feb",
                                activebackground="#0d1117",
                                font=("Consolas",9))
            rb.pack(side=tk.LEFT, padx=4)
        return var

    def _build(self):
        tk.Label(self, text="전술 설정", font=("Consolas",12,"bold"),
                 bg="#0d1117", fg="#58a6ff").pack(pady=10)

        sep = lambda: tk.Frame(self, height=1, bg="#30363d").pack(fill=tk.X, padx=10, pady=2)

        tk.Label(self, text="▶ 기본 전술", bg="#0d1117", fg="#f0c040",
                 font=("Consolas",9,"bold")).pack(anchor="w", padx=14, pady=(8,0))

        # 포메이션
        f0 = tk.Frame(self, bg="#0d1117"); f0.pack(fill=tk.X, pady=4, padx=10)
        tk.Label(f0, text="포메이션", width=14, anchor="w",
                 bg="#0d1117", fg="#8b949e", font=("Consolas",9)).pack(side=tk.LEFT)
        self.v_form = tk.StringVar(value=self.engine.my_team.formation)
        for opt in FORMATIONS:
            tk.Radiobutton(f0, text=opt, variable=self.v_form, value=opt,
                           bg="#0d1117", fg="#c9d1d9", selectcolor="#1f6feb",
                           activebackground="#0d1117",
                           font=("Consolas",9)).pack(side=tk.LEFT, padx=3)

        self.v_pass  = self._row(self, "패스 스타일",   PASS_STYLES,   "passing_style")
        self.v_press = self._row(self, "압박 라인",     PRESS_LINES,   "pressing_line")

        sep()
        tk.Label(self, text="▶ 세부 전술", bg="#0d1117", fg="#f0c040",
                 font=("Consolas",9,"bold")).pack(anchor="w", padx=14, pady=(8,0))

        self.v_tempo  = self._row(self, "경기 템포",     TEMPO_OPTIONS,  "tempo")
        self.v_width  = self._row(self, "공간 활용 폭",  WIDTH_OPTIONS,  "width")
        self.v_defend = self._row(self, "수비 방식",     DEFEND_OPTIONS, "defend_style")
        self.v_set    = self._row(self, "세트피스",      SET_PIECE_OPTS, "set_piece")
        self.v_count  = self._row(self, "역습 방식",     COUNTER_OPTS,   "counter")

        sep()
        bf = tk.Frame(self, bg="#0d1117"); bf.pack(pady=10)
        tk.Button(bf, text="적용", width=14, bg="#1f6feb", fg="white",
                  command=self._apply).pack(side=tk.LEFT, padx=8)
        tk.Button(bf, text="닫기", width=10, bg="#21262d", fg="#c9d1d9",
                  command=self.destroy).pack(side=tk.LEFT, padx=8)

        # 현재 전력 표시
        self.lbl_power = tk.Label(self, text="", bg="#0d1117", fg="#3fb950",
                                  font=("Consolas",9))
        self.lbl_power.pack()
        self._refresh_power()

    def _apply(self):
        self.engine.set_team_tactic(
            self.v_form.get(), self.v_pass.get(), self.v_press.get())
        self.engine.set_detail_tactic(
            self.v_tempo.get(), self.v_width.get(),
            self.v_defend.get(), self.v_set.get(), self.v_count.get())
        self._refresh_power()

    def _refresh_power(self):
        self.lbl_power.config(
            text=f"현재 실질 전력: {self.engine.my_team.get_match_power():.1f}  (전술 배율: x{self.engine.my_team.tactic_power_bonus():.3f})"
        )


# ── 개인 지침 창 ──────────────────────────────────────────────────────────────
class InstructionWindow(tk.Toplevel):
    def __init__(self, parent, engine: SimulatorEngine):
        super().__init__(parent)
        self.engine = engine
        self.title("개인 지침")
        self.geometry("700x500")
        self.configure(bg="#0d1117")
        self._build()

    def _build(self):
        tk.Label(self, text="개인 전술 지침", font=("Consolas",12,"bold"),
                 bg="#0d1117", fg="#58a6ff").pack(pady=8)

        cols = ("구분","번호","이름","포지션","OVR","현재 지침")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=80, anchor="center")
        self.tree.column("이름",    width=160, anchor="w")
        self.tree.column("현재 지침", width=120, anchor="center")
        sb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0), pady=6)
        sb.pack(side=tk.LEFT, fill=tk.Y, pady=6)

        right = tk.Frame(self, bg="#0d1117", width=160)
        right.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=6)
        tk.Label(right, text="지침 선택", bg="#0d1117", fg="#f0c040",
                 font=("Consolas",9,"bold")).pack(pady=(10,4))
        self.v_instr = tk.StringVar(value="기본")
        for ins in INSTRUCTIONS:
            tk.Radiobutton(right, text=ins, variable=self.v_instr, value=ins,
                           bg="#0d1117", fg="#c9d1d9", selectcolor="#1f6feb",
                           activebackground="#0d1117",
                           font=("Consolas",9), anchor="w", width=14).pack(pady=1)
        tk.Button(right, text="적용", bg="#1f6feb", fg="white", width=12,
                  command=self._apply).pack(pady=10)

        self._refresh()

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        eng = self.engine
        for i, p in enumerate(eng.my_team.starters):
            self.tree.insert("","end", iid=f"s{i}",
                             values=("선발", i+1, p.name, p.position, p.rating, p.instruction))
        for i, p in enumerate(eng.my_team.subs):
            self.tree.insert("","end", iid=f"b{i}",
                             values=("후보", i+1, p.name, p.position, p.rating, p.instruction))

    def _apply(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("알림", "선수를 먼저 선택하라.", parent=self)
            return
        iid = sel[0]
        is_starter = iid.startswith("s")
        idx = int(iid[1:])
        self.engine.set_player_instruction(is_starter, idx, self.v_instr.get())
        self._refresh()


# ── 이적 시장 창 ──────────────────────────────────────────────────────────────
class TransferWindow(tk.Toplevel):
    def __init__(self, parent, engine: SimulatorEngine):
        super().__init__(parent)
        self.engine = engine
        self.title("이적 시장")
        self.geometry("860x560")
        self.configure(bg="#0d1117")
        self._build()
        self._refresh()

    def _build(self):
        top = tk.Frame(self, bg="#0d1117"); top.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(top, text="이적 시장", font=("Consolas",13,"bold"),
                 bg="#0d1117", fg="#58a6ff").pack(side=tk.LEFT)
        self.lbl_budget = tk.Label(top, text="", font=("Consolas",10),
                                   bg="#0d1117", fg="#f0c040")
        self.lbl_budget.pack(side=tk.RIGHT)
        self.lbl_window = tk.Label(top, text="", font=("Consolas",9),
                                   bg="#0d1117", fg="#aaa")
        self.lbl_window.pack(side=tk.RIGHT, padx=10)

        nb = ttk.Notebook(self); nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        # 영입 탭
        buy_frame = tk.Frame(nb, bg="#0d1117"); nb.add(buy_frame, text="영입")
        cols = ("번호","이름","포지션","OVR","PAC","SHO","PAS","DEF","PHY","몸값(M)")
        self.buy_tree = ttk.Treeview(buy_frame, columns=cols, show="headings", height=16)
        for c in cols:
            self.buy_tree.heading(c, text=c)
            self.buy_tree.column(c, width=70, anchor="center")
        self.buy_tree.column("이름", width=150, anchor="w")
        sb = ttk.Scrollbar(buy_frame, orient=tk.VERTICAL, command=self.buy_tree.yview)
        self.buy_tree.configure(yscrollcommand=sb.set)
        self.buy_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        bf = tk.Frame(self, bg="#0d1117"); bf.pack(pady=4)
        tk.Button(bf, text="선발로 영입", width=14, bg="#1f6feb", fg="white",
                  command=lambda: self._buy(True)).pack(side=tk.LEFT, padx=6)
        tk.Button(bf, text="후보로 영입", width=14, bg="#238636", fg="white",
                  command=lambda: self._buy(False)).pack(side=tk.LEFT, padx=6)
        tk.Button(bf, text="새로고침", width=10, command=self._refresh).pack(side=tk.LEFT, padx=6)

        # 방출 탭
        sell_frame = tk.Frame(nb, bg="#0d1117"); nb.add(sell_frame, text="방출 (내 스쿼드)")
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
        tk.Button(sf, text="선택 선수 방출", width=16, bg="#da3633", fg="white",
                  command=self._sell).pack(side=tk.LEFT, padx=6)

    def _refresh(self):
        eng = self.engine
        is_open = eng.game_date.is_transfer_window()
        self.lbl_budget.config(text=f"예산: {eng.my_team.budget}M")
        self.lbl_window.config(
            text=f"이적 시장 {'열림 ✅' if is_open else '닫힘 ❌'}  ({eng.game_date})",
            fg="#3fb950" if is_open else "#f85149")

        self.buy_tree.delete(*self.buy_tree.get_children())
        for i, p in enumerate(eng.transfer_pool):
            self.buy_tree.insert("","end", values=(
                i+1, p.name, p.position, p.rating,
                p.pac, p.sho, p.pas, p.def_, p.phy, p.price))

        self.sell_tree.delete(*self.sell_tree.get_children())
        for i, p in enumerate(eng.my_team.starters):
            self.sell_tree.insert("","end", iid=f"s{i}",
                values=("선발", i+1, p.name, p.position, p.rating, p.stamina, f"{int(p.price*0.75)}M"))
        for i, p in enumerate(eng.my_team.subs):
            self.sell_tree.insert("","end", iid=f"b{i}",
                values=("후보", i+1, p.name, p.position, p.rating, p.stamina, f"{int(p.price*0.75)}M"))

    def _buy(self, to_starter):
        sel = self.buy_tree.selection()
        if not sel:
            messagebox.showinfo("알림", "영입할 선수를 선택하라.", parent=self); return
        idx = int(self.buy_tree.item(sel[0])["values"][0]) - 1
        self.engine.transfer_buy(idx, to_starter)
        self._refresh()

    def _sell(self):
        sel = self.sell_tree.selection()
        if not sel:
            messagebox.showinfo("알림", "방출할 선수를 선택하라.", parent=self); return
        iid  = sel[0]
        name = self.sell_tree.item(iid)["values"][2]
        if not messagebox.askyesno("방출 확인", f"{name}을(를) 방출하겠습니까?", parent=self): return
        self.engine.transfer_sell(iid.startswith("s"), int(iid[1:]))
        self._refresh()


# ── 메인 GUI ──────────────────────────────────────────────────────────────────
class FM_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FM 시뮬레이터 2026")
        self.root.geometry("880x700")
        self.root.configure(bg="#0d1117")

        # 상단 상태바
        bar = tk.Frame(self.root, bg="#161b22", pady=5)
        bar.pack(fill=tk.X)
        tk.Label(bar, text="⚽ FM SIMULATOR 2026", font=("Consolas",11,"bold"),
                 bg="#161b22", fg="#58a6ff").pack(side=tk.LEFT, padx=12)
        self.lbl_date = tk.Label(bar, text="", font=("Consolas",10),
                                 bg="#161b22", fg="#f0c040")
        self.lbl_date.pack(side=tk.RIGHT, padx=12)
        self.lbl_hint = tk.Label(bar, text="", font=("Consolas",9),
                                 bg="#161b22", fg="#3fb950")
        self.lbl_hint.pack(side=tk.RIGHT, padx=4)

        # 로그 창
        self.text_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, width=118, height=33,
            font=("Consolas",9), bg="#0d1117", fg="#c9d1d9",
            insertbackground="white", relief=tk.FLAT)
        self.text_area.pack(pady=6, padx=10, fill=tk.BOTH, expand=True)

        # 버튼 행 1
        f1 = tk.Frame(self.root, bg="#0d1117"); f1.pack(pady=3)
        for txt, cmd in [
            ("스쿼드 확인",    lambda: self.engine.show_squad_detailed()),
            ("선수 교체",      self.cmd_substitute),
            ("전술 설정",      self.cmd_tactic),
            ("개인 지침",      self.cmd_instruction),
        ]:
            tk.Button(f1, text=txt, command=cmd, width=13,
                      bg="#21262d", fg="#c9d1d9",
                      activebackground="#30363d",
                      font=("Consolas",9)).pack(side=tk.LEFT, padx=4)

        # 버튼 행 2
        f2 = tk.Frame(self.root, bg="#0d1117"); f2.pack(pady=3)
        tk.Button(f2, text="다음 경기 진행", command=lambda: self.engine.play_match(),
                  width=15, bg="#1f6feb", fg="white",
                  font=("Consolas",9,"bold")).pack(side=tk.LEFT, padx=4)
        tk.Button(f2, text="이적 시장", command=self.cmd_transfer,
                  width=12, bg="#8957e5", fg="white",
                  font=("Consolas",9)).pack(side=tk.LEFT, padx=4)
        tk.Button(f2, text="게임 저장", command=lambda: self.engine.save_game(),
                  width=12, bg="#238636", fg="white",
                  font=("Consolas",9)).pack(side=tk.LEFT, padx=4)
        tk.Button(f2, text="종료", command=self.root.quit,
                  width=10, bg="#da3633", fg="white",
                  font=("Consolas",9)).pack(side=tk.LEFT, padx=4)

        self.engine = SimulatorEngine(self.write_log, self.update_date_label)
        self.engine.load_game()

    def update_date_label(self, date_str):
        self.lbl_date.config(text=f"📅 {date_str}")
        is_open = self.engine.game_date.is_transfer_window()
        self.lbl_hint.config(text="🏪 이적 시장 오픈" if is_open else "")

    def write_log(self, text):
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)

    def cmd_substitute(self):
        si = simpledialog.askinteger("교체 OUT", "뺄 선발 선수 번호 (1~11):", parent=self.root)
        if si is None: return
        bi = simpledialog.askinteger("교체 IN",  "투입할 후보 번호 (1~7):",   parent=self.root)
        if bi is None: return
        self.engine.substitute_player(si-1, bi-1)

    def cmd_tactic(self):
        TacticWindow(self.root, self.engine)

    def cmd_instruction(self):
        InstructionWindow(self.root, self.engine)

    def cmd_transfer(self):
        TransferWindow(self.root, self.engine)


if __name__ == "__main__":
    if not is_admin():
        try: ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        except: pass
        sys.exit()
    root = tk.Tk()
    app = FM_GUI(root)
    root.mainloop()
