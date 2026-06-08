import os
import sys
import json
import random
import ctypes
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, ttk

SAVE_DIR = r"C:\MANAGER_SIMULATOR"
SAVE_FILE = os.path.join(SAVE_DIR, "save_data_v5.json")

# 이적시장 열리는 월 (하계: 7~8월, 동계: 1월)
TRANSFER_MONTHS = {1, 7, 8}

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ── 날짜 시스템 ──────────────────────────────────────────────────────────────
class GameDate:
    MONTH_NAMES = ["", "1월", "2월", "3월", "4월", "5월", "6월",
                   "7월", "8월", "9월", "10월", "11월", "12월"]

    def __init__(self, year=2024, month=8, day=1):
        self.year = year
        self.month = month
        self.day = day

    def advance_match(self):
        """경기 1회 진행 = 7일 경과"""
        self.day += 7
        if self.day > 28:
            self.day = self.day - 28
            self.month += 1
            if self.month > 12:
                self.month = 1
                self.year += 1

    def is_transfer_window(self):
        return self.month in TRANSFER_MONTHS

    def season_str(self):
        if self.month >= 8:
            return f"{self.year}/{self.year+1}"
        else:
            return f"{self.year-1}/{self.year}"

    def __str__(self):
        return f"{self.year}년 {self.MONTH_NAMES[self.month]} {self.day}일"

    def to_dict(self):
        return {"year": self.year, "month": self.month, "day": self.day}

    @classmethod
    def from_dict(cls, d):
        return cls(d.get("year", 2024), d.get("month", 8), d.get("day", 1))


# ── 이적시장 선수 풀 ─────────────────────────────────────────────────────────
TRANSFER_POOL_DATA = [
    # name, pos, pac, sho, pas, def, phy, price(백만)
    ("Kane",       "ST",  75, 91, 83, 40, 80, 100),
    ("Mbappe",     "LW",  97, 89, 80, 40, 80, 180),
    ("Bellingham", "CAM", 80, 85, 88, 70, 82, 150),
    ("Salah",      "RW",  90, 88, 78, 45, 75, 120),
    ("Vinicius",   "LW",  95, 84, 78, 38, 75, 140),
    ("De Bruyne",  "CM",  76, 85, 93, 62, 78, 130),
    ("Rodri",      "CDM", 72, 68, 88, 88, 84,  90),
    ("Alisson",    "GK",  61, 15, 72, 91, 80,  75),
    ("Ter Stegen", "GK",  58, 12, 78, 89, 78,  70),
    ("Van Dijk",   "CB",  82, 55, 73, 90, 88,  85),
    ("Rudiger",    "CB",  80, 58, 68, 88, 90,  60),
    ("Alexander-Arnold", "FB", 85, 72, 90, 76, 75, 80),
    ("Theo Hernandez", "FB", 90, 65, 78, 79, 84, 75),
    ("Pedri",      "CM",  80, 75, 90, 72, 72,  95),
    ("Gavi",       "CM",  78, 72, 87, 75, 75,  80),
    ("Osimhen",    "ST",  91, 85, 70, 38, 86,  90),
    ("Leao",       "LW",  94, 82, 76, 42, 78,  95),
    ("Diaz",       "LW",  88, 78, 75, 50, 76,  65),
    ("Nunez",      "ST",  89, 82, 68, 42, 85,  70),
    ("Saka",       "RW",  87, 82, 83, 58, 72,  90),
    ("Odegaard",   "CAM", 80, 82, 90, 60, 70,  95),
    ("Rice",       "CDM", 78, 68, 82, 84, 85,  90),
    ("Caicedo",    "CDM", 82, 65, 78, 85, 84,  75),
    ("Kimmich",    "CM",  75, 70, 88, 84, 76,  80),
    ("Wirtz",      "CAM", 82, 83, 88, 60, 72, 100),
    ("Musiala",    "CAM", 84, 80, 85, 58, 72,  95),
    ("Griezmann",  "CAM", 80, 85, 82, 62, 74,  70),
    ("Yamal",      "RW",  90, 82, 80, 40, 66,  90),
    ("Guiu",       "ST",  80, 78, 68, 40, 76,  40),
    ("Maignan",    "GK",  62, 12, 68, 87, 80,  65),
]

def make_transfer_pool():
    pool = []
    for row in TRANSFER_POOL_DATA:
        name, pos, pac, sho, pas, def_, phy, price = row
        pool.append(Player(name, pos, pac, sho, pas, def_, phy, price))
    return pool


# ── Player / Team ────────────────────────────────────────────────────────────
class Player:
    def __init__(self, name, position, pac, sho, pas, def_, phy, price,
                 stamina=100, injured_days=0, instruction="기본"):
        self.name = name
        self.position = position
        self.pac = pac
        self.sho = sho
        self.pas = pas
        self.def_ = def_
        self.phy = phy
        self.price = price
        self.stamina = stamina
        self.injured_days = injured_days
        self.instruction = instruction

    @property
    def rating(self):
        if self.position in ['ST', 'LW', 'RW']:
            val = (self.sho * 0.4) + (self.pac * 0.3) + (self.pas * 0.1) + (self.phy * 0.2)
        elif self.position in ['CM', 'CAM', 'CDM']:
            val = (self.pas * 0.4) + (self.def_ * 0.2) + (self.sho * 0.2) + (self.phy * 0.2)
        elif self.position in ['CB', 'FB']:
            val = (self.def_ * 0.4) + (self.phy * 0.3) + (self.pac * 0.2) + (self.pas * 0.1)
        elif self.position == 'GK':
            val = (self.def_ * 0.6) + (self.phy * 0.4)
        else:
            val = (self.pac + self.sho + self.pas + self.def_ + self.phy) / 5
        return int(val)

    def get_effective_rating(self):
        if self.injured_days > 0: return 0
        stamina_pen = max(0.4, self.stamina / 100.0)
        tactical_bonus = 1.0
        if self.instruction == "공격 가담" and self.position in ['CM', 'FB']: tactical_bonus = 1.05
        elif self.instruction == "수비 대기" and self.position in ['CM', 'FB']: tactical_bonus = 1.05
        return self.rating * stamina_pen * tactical_bonus

    def to_dict(self):
        return {
            "name": self.name, "position": self.position,
            "pac": self.pac, "sho": self.sho, "pas": self.pas, "def": self.def_, "phy": self.phy,
            "price": self.price, "stamina": self.stamina,
            "injured_days": self.injured_days, "instruction": self.instruction
        }


class Team:
    def __init__(self, name, budget, starters=None, subs=None):
        self.name = name
        self.budget = budget
        self.starters = starters if starters else []
        self.subs = subs if subs else []
        self.formation = "4-3-3"
        self.passing_style = "혼합"
        self.pressing_line = "일반"
        # 시즌 통계
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.goals_for = 0
        self.goals_against = 0

    @property
    def points(self):
        return self.wins * 3 + self.draws

    def get_match_power(self):
        if len(self.starters) < 11:
            return 0
        power = sum(p.get_effective_rating() for p in self.starters) / 11
        if self.passing_style == "짧은 패스": power *= 1.03
        if self.pressing_line == "전방 압박": power *= 1.03
        return power

    def all_players(self):
        return self.starters + self.subs

    def get_attackers(self):
        return [p for p in self.starters if p.position in ['ST', 'LW', 'RW', 'CAM']]

    def get_midfielders(self):
        return [p for p in self.starters if p.position in ['CM', 'CDM', 'CAM']]

    def get_defenders(self):
        return [p for p in self.starters if p.position in ['CB', 'FB']]

    def get_gk(self):
        gks = [p for p in self.starters if p.position == 'GK']
        return gks[0] if gks else None

    def to_dict(self):
        return {
            "name": self.name, "budget": self.budget,
            "formation": self.formation,
            "passing_style": self.passing_style,
            "pressing_line": self.pressing_line,
            "wins": self.wins, "draws": self.draws, "losses": self.losses,
            "goals_for": self.goals_for, "goals_against": self.goals_against,
            "starters": [p.to_dict() for p in self.starters],
            "subs": [p.to_dict() for p in self.subs],
        }


# ── 경기 중계 ────────────────────────────────────────────────────────────────
class MatchCommentator:
    ATTACK_EVENTS = [
        "{attacker}가 왼쪽 측면 드리블로 수비를 제치고 올라간다!",
        "{attacker}가 중원에서 전방으로 날카로운 스루 패스!",
        "{attacker}가 박스 근처에서 기회를 잡았다!",
        "{attacker}가 오른쪽 사이드를 빠르게 파고든다!",
        "{attacker}가 헤더 경합에서 이기며 공을 이어받는다!",
        "코너킥 상황! {attacker}가 공을 올린다...",
        "{attacker}가 프리킥 자리를 잡는다. 위협적인 위치다!",
        "{attacker}가 원투패스로 수비 뒤 공간을 노린다!",
        "{attacker}가 돌아서며 중거리 슛 자리를 잡는다!",
        "{attacker}가 박스 안으로 파고들며 결정적인 기회를 만든다!",
    ]
    SHOT_SAVED = [
        "슈팅! {gk}가 몸을 던져 막아낸다! 아깝다!",
        "강한 슈팅이지만 {gk}가 정면으로 잡아낸다!",
        "{gk}의 신들린 반응 세이브! 구석을 노렸지만 막혔다!",
        "슈팅이 골대 구석으로... {gk}가 뻗어서 코너 처리!",
        "{gk}가 원핸드 세이브로 실점을 막아낸다! 훌륭하다!",
    ]
    SHOT_MISS = [
        "슈팅은 크게 빗나가 골대 밖으로!",
        "슈팅이 크로스바를 강타하며 튕겨 나온다!",
        "너무 급하게 찼다. 슈팅이 하늘로 솟구쳐 버린다!",
        "결정적인 기회였지만 슈팅이 골포스트를 강타!",
        "마지막 수비수에게 걷혀 나간다. 아쉬운 장면!",
    ]
    GOAL_TEXTS = [
        "골!!!!! {scorer}의 환상적인 마무리! {home} {hg}:{ag} {away}",
        "골!!!!! {scorer}가 해냈다! 골망이 흔들린다! {home} {hg}:{ag} {away}",
        "골!!!!! 완벽한 위치 선정, {scorer}가 차갑게 마무리! {home} {hg}:{ag} {away}",
        "골!!!!! {scorer}의 강렬한 슈팅이 골키퍼 손을 뚫고 들어간다! {home} {hg}:{ag} {away}",
        "골!!!!! {scorer}! 기가 막힌 골이다! {home} {hg}:{ag} {away}",
    ]
    FOUL_TEXTS = [
        "{fouler}의 거친 태클! 파울 선언.",
        "{fouler}가 뒤에서 잡아당겼다. 프리킥 허용.",
        "반칙! {fouler}가 경고를 받는다. 옐로카드!",
        "{fouler}의 슬라이딩 태클이 늦게 들어갔다. 파울.",
    ]
    POSSESSION_TEXTS = [
        "양 팀이 중원에서 볼 경합을 펼치고 있다.",
        "{team}이 점유율을 끌어올리며 경기를 지배하려 한다.",
        "{team}의 짧은 패스 연결이 이어지고 있다.",
        "{team} 수비진이 안정적으로 빌드업 중이다.",
        "상대 진영에서 {team}이 공을 오래 돌린다.",
    ]

    @staticmethod
    def random_player_name(team, role="any"):
        if role == "attacker":   pool = team.get_attackers() or team.starters
        elif role == "defender": pool = team.get_defenders() or team.starters
        elif role == "gk":
            gk = team.get_gk()
            return gk.name if gk else "골키퍼"
        else: pool = team.starters
        return random.choice(pool).name if pool else "선수"

    @classmethod
    def attack_commentary(cls, attacking, defending):
        attacker = cls.random_player_name(attacking, "attacker")
        gk = cls.random_player_name(defending, "gk")
        return random.choice(cls.ATTACK_EVENTS).format(attacker=attacker), attacker, gk

    @classmethod
    def foul_commentary(cls, fouling_team):
        fouler = cls.random_player_name(fouling_team, "defender")
        return random.choice(cls.FOUL_TEXTS).format(fouler=fouler)

    @classmethod
    def possession_commentary(cls, team):
        return random.choice(cls.POSSESSION_TEXTS).format(team=team.name)


# ── 엔진 ─────────────────────────────────────────────────────────────────────
class SimulatorEngine:
    def __init__(self, log_callback, date_callback=None):
        self.my_team = None
        self.log = log_callback
        self.date_callback = date_callback  # 날짜 UI 갱신용
        self.game_date = GameDate()
        self.transfer_pool = make_transfer_pool()

        self.opponents = [
            self._build_cpu_team("Manchester City", 90),
            self._build_cpu_team("Real Madrid",     88),
            self._build_cpu_team("Arsenal",         85),
            self._build_cpu_team("Bayern Munich",   87),
            self._build_cpu_team("Barcelona",       86),
        ]

    def _build_cpu_team(self, name, base):
        positions = ['GK','FB','CB','CB','FB','CDM','CM','CM','LW','ST','RW']
        starters = [
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

    # ── 초기 세팅 ─────────────────────────────────────────────────────────────
    def setup_new_game(self):
        self.log("새로운 감독으로 부임했다. 선발 11명과 후보 7명을 지급한다.")
        starters = [
            Player("Rashford",  "LW",  88, 85, 78, 45, 75, 60),
            Player("Hojlund",   "ST",  85, 82, 70, 40, 85, 50),
            Player("Garnacho",  "RW",  86, 75, 72, 40, 60, 45),
            Player("Bruno",     "CM",  75, 85, 90, 65, 75, 80),
            Player("Mainoo",    "CM",  78, 70, 82, 75, 70, 40),
            Player("Casemiro",  "CDM", 65, 75, 80, 85, 88, 30),
            Player("Shaw",      "FB",  80, 65, 80, 82, 80, 35),
            Player("Martinez",  "CB",  75, 50, 80, 86, 82, 55),
            Player("Varane",    "CB",  78, 45, 65, 88, 85, 40),
            Player("Dalot",     "FB",  84, 65, 78, 78, 75, 35),
            Player("Onana",     "GK",  60, 20, 85, 85, 80, 45),
        ]
        subs = [
            Player("Antony",       "RW",  82, 70, 75, 45, 65, 40),
            Player("Eriksen",      "CM",  60, 75, 88, 55, 60, 30),
            Player("Mount",        "CAM", 75, 78, 82, 60, 70, 45),
            Player("Maguire",      "CB",  55, 50, 65, 84, 88, 30),
            Player("Lindelof",     "CB",  65, 45, 70, 80, 78, 25),
            Player("Wan-Bissaka",  "FB",  82, 40, 65, 85, 75, 30),
            Player("Bayindir",     "GK",  50, 15, 70, 78, 75, 15),
        ]
        self.my_team = Team("My Club", 200, starters, subs)
        self.game_date = GameDate(2024, 8, 10)
        self._notify_date()
        self.save_game()

    # ── 스쿼드 보기 ───────────────────────────────────────────────────────────
    def show_squad_detailed(self):
        t = self.my_team
        self.log(f"\n{'='*60}")
        self.log(f"  [{str(self.game_date)}]  시즌: {self.game_date.season_str()}")
        self.log(f"  팀: {t.name}  |  예산: {t.budget}M  |  승점: {t.points}pt  ({t.wins}승 {t.draws}무 {t.losses}패)")
        self.log(f"  전술: {t.formation} | 패스: {t.passing_style} | 압박: {t.pressing_line}")
        self.log(f"{'='*60}")
        self.log("  [선발]")
        for i, p in enumerate(t.starters):
            cond = f"체력:{p.stamina:3d} " + (f"부상({p.injured_days}턴)" if p.injured_days > 0 else "정상  ")
            self.log(f"  {i+1:2d}. [{p.position:<3}] {p.name:<16} OVR:{p.rating}  {cond}  지침:{p.instruction}")
        self.log("  [후보]")
        for i, p in enumerate(t.subs):
            cond = f"체력:{p.stamina:3d} " + (f"부상({p.injured_days}턴)" if p.injured_days > 0 else "정상  ")
            self.log(f"  {i+1:2d}. [{p.position:<3}] {p.name:<16} OVR:{p.rating}  {cond}  지침:{p.instruction}")
        self.log(f"\n  실질 전력: {t.get_match_power():.1f}\n")

    # ── 선수 교체 ─────────────────────────────────────────────────────────────
    def substitute_player(self, si, bi):
        s, b = self.my_team.starters, self.my_team.subs
        if 0 <= si < len(s) and 0 <= bi < len(b):
            s[si], b[bi] = b[bi], s[si]
            self.log(f"[교체] {b[bi].name} OUT  ↔  {s[si].name} IN")
        else:
            self.log("잘못된 번호다.")

    # ── 전술 ──────────────────────────────────────────────────────────────────
    def set_team_tactic(self, passing, pressing):
        vp = ["짧은 패스", "다이렉트", "혼합"]
        vd = ["전방 압박", "일반", "내려앉기"]
        if passing in vp and pressing in vd:
            self.my_team.passing_style = passing
            self.my_team.pressing_line = pressing
            self.log(f"[전술 변경] 패스: {passing} | 압박: {pressing}")
        else:
            self.log("지원하지 않는 전술 설정이다.")

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
        hp = home.get_match_power()
        ap = away.get_match_power()
        total = hp + ap if hp + ap > 0 else 1

        self.log("\n" + "=" * 60)
        self.log(f"  📅 {self.game_date}  |  시즌 {self.game_date.season_str()}")
        self.log(f"  ⚽  {home.name}  VS  {away.name}")
        self.log(f"  전술: {home.formation} | 패스: {home.passing_style} | 압박: {home.pressing_line}")
        self.log(f"  팀 전력  {home.name}: {hp:.1f}  /  {away.name}: {ap:.1f}")
        self.log("=" * 60)

        hg = ag = 0
        scorers = []

        for half in range(1, 3):
            self.log(f"\n─── {'전반' if half==1 else '후반'} 시작 ───")
            offset = 0 if half == 1 else 45
            for t in sorted(random.sample(range(1, 45), k=random.randint(8, 12))):
                minute = offset + t
                if random.random() < hp / total:
                    atk, dfn = home, away
                else:
                    atk, dfn = away, home

                roll = random.random()
                if roll < 0.10:
                    self.log(f"  {minute:2d}' | {MatchCommentator.foul_commentary(dfn)}")
                elif roll < 0.30:
                    self.log(f"  {minute:2d}' | {MatchCommentator.possession_commentary(atk)}")
                else:
                    line, scorer_name, gk_name = MatchCommentator.attack_commentary(atk, dfn)
                    self.log(f"  {minute:2d}' | {line}")
                    shot_chance = 0.55 if atk.get_match_power() >= dfn.get_match_power() else 0.40
                    if random.random() < shot_chance:
                        gp = (atk.get_match_power() / (atk.get_match_power() + dfn.get_match_power() + 1)) * 0.45
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

        # 결과 집계
        self.log("\n" + "=" * 60)
        self.log(f"  최종  {home.name}  {hg} : {ag}  {away.name}")
        self.log("=" * 60)
        if scorers:
            self.log("  ⚽ 득점 기록")
            for m, team, sc in scorers:
                self.log(f"    {m}' {sc} ({team})")

        if hg > ag:
            self.log(f"\n  ✅ 승리!"); home.wins += 1
        elif hg < ag:
            self.log(f"\n  ❌ 패배."); home.losses += 1
        else:
            self.log(f"\n  🤝 무승부."); home.draws += 1
        home.goals_for += hg
        home.goals_against += ag

        # 체력/부상
        self.log("\n  ── 경기 후 선수 상태 ──")
        injured_any = False
        for p in home.starters:
            drain = random.randint(15, 25) + (10 if home.pressing_line == "전방 압박" else 0)
            p.stamina = max(0, p.stamina - drain)
            if random.random() < 0.03:
                p.injured_days = random.randint(1, 3)
                self.log(f"  🚨 {p.name} 부상! ({p.injured_days}턴 아웃)")
                injured_any = True
        for p in home.subs:
            p.stamina = min(100, p.stamina + 10)
        if not injured_any:
            self.log("  전원 부상 없이 마쳤다.")

        # 날짜 전진
        self.game_date.advance_match()
        self._notify_date()

        # 부상 턴 차감
        for p in home.all_players():
            if p.injured_days > 0:
                p.injured_days -= 1

        if self.game_date.is_transfer_window():
            self.log(f"\n  🏪 이적 시장이 열려 있다! ({self.game_date})")

        self.log("")
        self.save_game()

    # ── 이적시장: 영입 ────────────────────────────────────────────────────────
    def transfer_buy(self, pool_idx, to_starter):
        """pool_idx: transfer_pool 인덱스, to_starter: True=선발, False=후보"""
        if not self.game_date.is_transfer_window():
            self.log("이적 시장이 열려 있지 않다. (1월 / 7~8월만 가능)")
            return

        if pool_idx < 0 or pool_idx >= len(self.transfer_pool):
            self.log("잘못된 선수 번호다.")
            return

        player = self.transfer_pool[pool_idx]
        if self.my_team.budget < player.price:
            self.log(f"예산 부족! 필요: {player.price}M / 보유: {self.my_team.budget}M")
            return

        target = self.my_team.starters if to_starter else self.my_team.subs
        max_size = 11 if to_starter else 10
        if len(target) >= max_size:
            self.log(f"{'선발' if to_starter else '후보'} 인원이 가득 찼다. 먼저 방출하라.")
            return

        self.my_team.budget -= player.price
        target.append(player)
        self.transfer_pool.pop(pool_idx)
        self.log(f"[영입 완료] {player.name} ({player.position}, OVR:{player.rating})  -{player.price}M  잔여 예산: {self.my_team.budget}M")
        self.save_game()

    # ── 이적시장: 방출 ────────────────────────────────────────────────────────
    def transfer_sell(self, is_starter, idx):
        if not self.game_date.is_transfer_window():
            self.log("이적 시장이 열려 있지 않다.")
            return
        lst = self.my_team.starters if is_starter else self.my_team.subs
        if idx < 0 or idx >= len(lst):
            self.log("잘못된 번호다.")
            return
        player = lst.pop(idx)
        sell_price = int(player.price * random.uniform(0.6, 0.9))
        self.my_team.budget += sell_price
        self.transfer_pool.append(player)
        self.log(f"[방출 완료] {player.name}  +{sell_price}M  잔여 예산: {self.my_team.budget}M")
        self.save_game()

    # ── 저장/로드 ─────────────────────────────────────────────────────────────
    def save_game(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        try:
            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "my_team": self.my_team.to_dict(),
                    "game_date": self.game_date.to_dict(),
                }, f, ensure_ascii=False, indent=4)
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
            self.my_team = Team(
                td["name"], td.get("budget", 200),
                parse_players(td.get("starters", [])),
                parse_players(td.get("subs", []))
            )
            self.my_team.formation    = td.get("formation", "4-3-3")
            self.my_team.passing_style = td.get("passing_style", "혼합")
            self.my_team.pressing_line = td.get("pressing_line", "일반")
            self.my_team.wins         = td.get("wins", 0)
            self.my_team.draws        = td.get("draws", 0)
            self.my_team.losses       = td.get("losses", 0)
            self.my_team.goals_for    = td.get("goals_for", 0)
            self.my_team.goals_against= td.get("goals_against", 0)

            if "game_date" in data:
                self.game_date = GameDate.from_dict(data["game_date"])

            # 이미 영입된 선수는 풀에서 제거
            owned = {p.name for p in self.my_team.all_players()}
            self.transfer_pool = [p for p in self.transfer_pool if p.name not in owned]

            self._notify_date()
            self.log("데이터 로드 완료.")
        except Exception:
            self.setup_new_game()


# ── 이적시장 창 ───────────────────────────────────────────────────────────────
class TransferWindow(tk.Toplevel):
    def __init__(self, parent, engine: SimulatorEngine):
        super().__init__(parent)
        self.engine = engine
        self.title("이적 시장")
        self.geometry("820x560")
        self.configure(bg="#0d1117")
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        top = tk.Frame(self, bg="#0d1117")
        top.pack(fill=tk.X, padx=10, pady=6)

        tk.Label(top, text="이적 시장", font=("Consolas", 13, "bold"),
                 bg="#0d1117", fg="#58a6ff").pack(side=tk.LEFT)
        self.lbl_budget = tk.Label(top, text="", font=("Consolas", 10),
                                   bg="#0d1117", fg="#f0c040")
        self.lbl_budget.pack(side=tk.RIGHT)
        self.lbl_window = tk.Label(top, text="", font=("Consolas", 10),
                                   bg="#0d1117", fg="#aaa")
        self.lbl_window.pack(side=tk.RIGHT, padx=10)

        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        # ── 탭1: 선수 영입 ─────────────────────────────────────────────────
        buy_frame = tk.Frame(nb, bg="#0d1117")
        nb.add(buy_frame, text="영입 (이적 시장 선수)")

        cols = ("번호","이름","포지션","OVR","PAC","SHO","PAS","DEF","PHY","몸값(M)")
        self.buy_tree = ttk.Treeview(buy_frame, columns=cols, show="headings", height=16)
        for c in cols:
            self.buy_tree.heading(c, text=c)
            self.buy_tree.column(c, width=72, anchor="center")
        self.buy_tree.column("이름", width=130, anchor="w")
        sb = ttk.Scrollbar(buy_frame, orient=tk.VERTICAL, command=self.buy_tree.yview)
        self.buy_tree.configure(yscrollcommand=sb.set)
        self.buy_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame_buy = tk.Frame(self, bg="#0d1117")
        btn_frame_buy.pack(pady=4)
        tk.Button(btn_frame_buy, text="선발로 영입", width=14,
                  bg="#1f6feb", fg="white",
                  command=lambda: self._buy(True)).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame_buy, text="후보로 영입", width=14,
                  bg="#238636", fg="white",
                  command=lambda: self._buy(False)).pack(side=tk.LEFT, padx=6)

        # ── 탭2: 선수 방출 ─────────────────────────────────────────────────
        sell_frame = tk.Frame(nb, bg="#0d1117")
        nb.add(sell_frame, text="방출 (내 스쿼드)")

        cols2 = ("구분","번호","이름","포지션","OVR","체력","예상 이적료")
        self.sell_tree = ttk.Treeview(sell_frame, columns=cols2, show="headings", height=16)
        for c in cols2:
            self.sell_tree.heading(c, text=c)
            self.sell_tree.column(c, width=90, anchor="center")
        self.sell_tree.column("이름", width=140, anchor="w")
        sb2 = ttk.Scrollbar(sell_frame, orient=tk.VERTICAL, command=self.sell_tree.yview)
        self.sell_tree.configure(yscrollcommand=sb2.set)
        self.sell_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame_sell = tk.Frame(self, bg="#0d1117")
        btn_frame_sell.pack(pady=4)
        tk.Button(btn_frame_sell, text="선택 선수 방출", width=16,
                  bg="#da3633", fg="white",
                  command=self._sell).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame_sell, text="새로고침", width=12,
                  command=self._refresh).pack(side=tk.LEFT, padx=6)

        self.nb = nb

    def _refresh(self):
        eng = self.engine
        budget = eng.my_team.budget
        is_open = eng.game_date.is_transfer_window()
        window_txt = f"이적 시장 {'열림 ✅' if is_open else '닫힘 ❌'}  ({eng.game_date})"
        self.lbl_budget.config(text=f"예산: {budget}M")
        self.lbl_window.config(text=window_txt, fg="#3fb950" if is_open else "#f85149")

        # 영입 탭
        self.buy_tree.delete(*self.buy_tree.get_children())
        for i, p in enumerate(eng.transfer_pool):
            self.buy_tree.insert("", "end", values=(
                i+1, p.name, p.position, p.rating,
                p.pac, p.sho, p.pas, p.def_, p.phy, p.price
            ))

        # 방출 탭
        self.sell_tree.delete(*self.sell_tree.get_children())
        for i, p in enumerate(eng.my_team.starters):
            est = int(p.price * 0.75)
            self.sell_tree.insert("", "end", iid=f"s{i}", values=(
                "선발", i+1, p.name, p.position, p.rating, p.stamina, f"{est}M"
            ))
        for i, p in enumerate(eng.my_team.subs):
            est = int(p.price * 0.75)
            self.sell_tree.insert("", "end", iid=f"b{i}", values=(
                "후보", i+1, p.name, p.position, p.rating, p.stamina, f"{est}M"
            ))

    def _buy(self, to_starter):
        sel = self.buy_tree.selection()
        if not sel:
            messagebox.showinfo("알림", "영입할 선수를 선택하라.", parent=self)
            return
        idx = int(self.buy_tree.item(sel[0])["values"][0]) - 1
        self.engine.transfer_buy(idx, to_starter)
        self._refresh()

    def _sell(self):
        sel = self.sell_tree.selection()
        if not sel:
            messagebox.showinfo("알림", "방출할 선수를 선택하라.", parent=self)
            return
        iid = sel[0]
        is_starter = iid.startswith("s")
        idx = int(iid[1:])
        name = self.sell_tree.item(iid)["values"][2]
        if not messagebox.askyesno("방출 확인", f"{name}을(를) 방출하겠습니까?", parent=self):
            return
        self.engine.transfer_sell(is_starter, idx)
        self._refresh()


# ── GUI ───────────────────────────────────────────────────────────────────────
class FM_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FM 시뮬레이터")
        self.root.geometry("860x680")
        self.root.configure(bg="#0d1117")

        # 상단 상태바
        status_bar = tk.Frame(self.root, bg="#161b22", pady=4)
        status_bar.pack(fill=tk.X, padx=0)
        tk.Label(status_bar, text="FM SIMULATOR", font=("Consolas", 11, "bold"),
                 bg="#161b22", fg="#58a6ff").pack(side=tk.LEFT, padx=12)
        self.lbl_date = tk.Label(status_bar, text="", font=("Consolas", 10),
                                 bg="#161b22", fg="#f0c040")
        self.lbl_date.pack(side=tk.RIGHT, padx=12)
        self.lbl_window_hint = tk.Label(status_bar, text="", font=("Consolas", 9),
                                        bg="#161b22", fg="#3fb950")
        self.lbl_window_hint.pack(side=tk.RIGHT, padx=6)

        # 로그 창
        self.text_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, width=115, height=32,
            font=("Consolas", 9), bg="#0d1117", fg="#c9d1d9",
            insertbackground="white", relief=tk.FLAT
        )
        self.text_area.pack(pady=6, padx=10, fill=tk.BOTH, expand=True)

        # 버튼 행 1
        f1 = tk.Frame(self.root, bg="#0d1117")
        f1.pack(pady=3)
        for txt, cmd in [
            ("스쿼드 확인",    lambda: self.engine.show_squad_detailed()),
            ("선수 교체",      self.cmd_substitute),
            ("팀 전술 설정",   self.cmd_team_tactic),
            ("개인 전술 설정", self.cmd_player_tactic),
        ]:
            tk.Button(f1, text=txt, command=cmd, width=13,
                      bg="#21262d", fg="#c9d1d9",
                      activebackground="#30363d").pack(side=tk.LEFT, padx=4)

        # 버튼 행 2
        f2 = tk.Frame(self.root, bg="#0d1117")
        f2.pack(pady=3)
        tk.Button(f2, text="다음 경기 진행", command=lambda: self.engine.play_match(),
                  width=15, bg="#1f6feb", fg="white",
                  activebackground="#388bfd").pack(side=tk.LEFT, padx=4)
        tk.Button(f2, text="이적 시장", command=self.cmd_transfer,
                  width=12, bg="#8957e5", fg="white",
                  activebackground="#a371f7").pack(side=tk.LEFT, padx=4)
        tk.Button(f2, text="게임 저장", command=lambda: self.engine.save_game(),
                  width=12, bg="#238636", fg="white").pack(side=tk.LEFT, padx=4)
        tk.Button(f2, text="종료", command=self.root.quit,
                  width=10, bg="#da3633", fg="white").pack(side=tk.LEFT, padx=4)

        self.engine = SimulatorEngine(self.write_log, self.update_date_label)
        self.engine.load_game()

    def update_date_label(self, date_str):
        self.lbl_date.config(text=f"📅 {date_str}")
        is_open = self.engine.game_date.is_transfer_window()
        self.lbl_window_hint.config(
            text="🏪 이적 시장 오픈" if is_open else "",
            fg="#3fb950"
        )

    def write_log(self, text):
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)

    def cmd_substitute(self):
        si = simpledialog.askinteger("교체 OUT", "뺄 선발 선수 번호 (1~11):", parent=self.root)
        if si is None: return
        bi = simpledialog.askinteger("교체 IN", "투입할 후보 번호 (1~7):", parent=self.root)
        if bi is None: return
        self.engine.substitute_player(si - 1, bi - 1)

    def cmd_team_tactic(self):
        p = simpledialog.askstring("패스 스타일", "짧은 패스 / 다이렉트 / 혼합:", parent=self.root)
        if not p: return
        d = simpledialog.askstring("압박 라인", "전방 압박 / 일반 / 내려앉기:", parent=self.root)
        if not d: return
        self.engine.set_team_tactic(p, d)

    def cmd_player_tactic(self):
        g = simpledialog.askstring("대상", "선발(1) / 후보(2):", parent=self.root)
        if g not in ('1', '2'): return
        n = simpledialog.askinteger("선수 번호", "번호 입력:", parent=self.root)
        if n is None: return
        ins = simpledialog.askstring("개인 지침", "공격 가담 / 수비 대기 / 자유 역할 / 기본:", parent=self.root)
        if ins:
            self.engine.set_player_instruction(g == '1', n - 1, ins)

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
