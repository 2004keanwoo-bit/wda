import os
import sys
import json
import random
import ctypes
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox

SAVE_DIR = r"C:\MANAGER_SIMULATOR"
SAVE_FILE = os.path.join(SAVE_DIR, "save_data_v4.json")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class Player:
    def __init__(self, name, position, pac, sho, pas, def_, phy, price, stamina=100, injured_days=0, instruction="기본"):
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
            "price": self.price, "stamina": self.stamina, "injured_days": self.injured_days,
            "instruction": self.instruction
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

    def get_match_power(self):
        if len(self.starters) < 11:
            return 0
        power = sum(p.get_effective_rating() for p in self.starters) / 11
        if self.passing_style == "짧은 패스": power *= 1.03
        if self.pressing_line == "전방 압박": power *= 1.03
        return power

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
            "formation": self.formation, "passing_style": self.passing_style, "pressing_line": self.pressing_line,
            "starters": [p.to_dict() for p in self.starters],
            "subs": [p.to_dict() for p in self.subs]
        }

# ── 경기 텍스트 중계 생성기 ─────────────────────────────────────────────────────
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
        "슈팅이 골대 왼쪽 구석으로... {gk}가 뻗어서 코너 처리!",
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
        "골!!!!! {scorer}의 강렬한 슈팅이 골키퍼의 손을 뚫고 들어간다! {home} {hg}:{ag} {away}",
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
    def random_player_name(team: Team, role="any"):
        pool = []
        if role == "attacker":
            pool = team.get_attackers() or team.starters
        elif role == "midfielder":
            pool = team.get_midfielders() or team.starters
        elif role == "defender":
            pool = team.get_defenders() or team.starters
        elif role == "gk":
            gk = team.get_gk()
            return gk.name if gk else "골키퍼"
        else:
            pool = team.starters
        return random.choice(pool).name if pool else "선수"

    @classmethod
    def attack_commentary(cls, attacking: Team, defending: Team):
        attacker = cls.random_player_name(attacking, "attacker")
        gk = cls.random_player_name(defending, "gk")
        line = random.choice(cls.ATTACK_EVENTS).format(attacker=attacker)
        return line, attacker, gk

    @classmethod
    def foul_commentary(cls, fouling_team: Team):
        fouler = cls.random_player_name(fouling_team, "defender")
        return random.choice(cls.FOUL_TEXTS).format(fouler=fouler)

    @classmethod
    def possession_commentary(cls, team: Team):
        return random.choice(cls.POSSESSION_TEXTS).format(team=team.name)


class SimulatorEngine:
    def __init__(self, log_callback):
        self.my_team = None
        self.log = log_callback

        self.opponents = [
            self._build_cpu_team("Manchester City", 90),
            self._build_cpu_team("Real Madrid", 88),
            self._build_cpu_team("Arsenal", 85)
        ]

    def _build_cpu_team(self, name, base_stat):
        starters = []
        positions = ['GK', 'FB', 'CB', 'CB', 'FB', 'CDM', 'CM', 'CM', 'LW', 'ST', 'RW']
        for i, pos in enumerate(positions):
            starters.append(Player(
                f"{name[:3].upper()}{i+1}", pos,
                base_stat + random.randint(-5, 5), base_stat + random.randint(-5, 5),
                base_stat + random.randint(-5, 5), base_stat + random.randint(-5, 5),
                base_stat + random.randint(-5, 5), 50
            ))
        return Team(name, 500, starters, [])

    def setup_new_game(self):
        self.log("새로운 감독으로 부임했다. 선발 11명과 후보 7명을 지급한다.")
        starters = [
            Player("Rashford", "LW", 88, 85, 78, 45, 75, 60), Player("Hojlund", "ST", 85, 82, 70, 40, 85, 50),
            Player("Garnacho", "RW", 86, 75, 72, 40, 60, 45), Player("Bruno", "CM", 75, 85, 90, 65, 75, 80),
            Player("Mainoo", "CM", 78, 70, 82, 75, 70, 40), Player("Casemiro", "CM", 65, 75, 80, 85, 88, 30),
            Player("Shaw", "FB", 80, 65, 80, 82, 80, 35), Player("Martinez", "CB", 75, 50, 80, 86, 82, 55),
            Player("Varane", "CB", 78, 45, 65, 88, 85, 40), Player("Dalot", "FB", 84, 65, 78, 78, 75, 35),
            Player("Onana", "GK", 60, 20, 85, 85, 80, 45)
        ]
        subs = [
            Player("Antony", "RW", 82, 70, 75, 45, 65, 40), Player("Eriksen", "CM", 60, 75, 88, 55, 60, 30),
            Player("Mount", "CAM", 75, 78, 82, 60, 70, 45), Player("Maguire", "CB", 55, 50, 65, 84, 88, 30),
            Player("Lindelof", "CB", 65, 45, 70, 80, 78, 25), Player("Wan-Bissaka", "FB", 82, 40, 65, 85, 75, 30),
            Player("Bayindir", "GK", 50, 15, 70, 78, 75, 15)
        ]
        self.my_team = Team("My Club", 200, starters, subs)
        self.save_game()

    def show_squad_detailed(self):
        self.log(f"\n--- [선발 명단] 전술: {self.my_team.formation} | 패스: {self.my_team.passing_style} | 압박: {self.my_team.pressing_line} ---")
        for i, p in enumerate(self.my_team.starters):
            cond = f"체력:{p.stamina} " + (f"부상({p.injured_days}턴)" if p.injured_days > 0 else "정상")
            self.log(f"선발 {i+1}. [{p.position}] {p.name:<12} | OVR:{p.rating} | 지침: {p.instruction} | {cond}")
        self.log("\n--- [후보 명단] ---")
        for i, p in enumerate(self.my_team.subs):
            cond = f"체력:{p.stamina} " + (f"부상({p.injured_days}턴)" if p.injured_days > 0 else "정상")
            self.log(f"후보 {i+1}. [{p.position}] {p.name:<12} | OVR:{p.rating} | 지침: {p.instruction} | {cond}")
        self.log(f"\n현재 선발 실질 전력: {self.my_team.get_match_power():.1f}\n")

    def substitute_player(self, starter_idx, sub_idx):
        if 0 <= starter_idx < len(self.my_team.starters) and 0 <= sub_idx < len(self.my_team.subs):
            starter = self.my_team.starters[starter_idx]
            sub = self.my_team.subs[sub_idx]
            self.my_team.starters[starter_idx] = sub
            self.my_team.subs[sub_idx] = starter
            self.log(f"[교체 완료] {starter.name} OUT <-> {sub.name} IN")
        else:
            self.log("잘못된 인덱스다. 교체에 실패했다.")

    def set_team_tactic(self, passing, pressing):
        valid_passing = ["짧은 패스", "다이렉트", "혼합"]
        valid_pressing = ["전방 압박", "일반", "내려앉기"]
        if passing in valid_passing and pressing in valid_pressing:
            self.my_team.passing_style = passing
            self.my_team.pressing_line = pressing
            self.log(f"[팀 전술 변경] 패스: {passing} | 수비 라인: {pressing}")
        else:
            self.log("지원하지 않는 전술 설정이다.")

    def set_player_instruction(self, is_starter, p_idx, instruction):
        target_list = self.my_team.starters if is_starter else self.my_team.subs
        if 0 <= p_idx < len(target_list):
            target_list[p_idx].instruction = instruction
            self.log(f"[개인 지침 변경] {target_list[p_idx].name}의 지침이 '{instruction}'(으)로 설정되었다.")
        else:
            self.log("잘못된 선수 번호다.")

    # ── 경기 시뮬레이션 (이벤트 중계) ───────────────────────────────────────────
    def play_match(self):
        if len(self.my_team.starters) < 11:
            self.log("선발 명단이 11명이 아니다. 경기를 진행할 수 없다.")
            return

        home = self.my_team
        away = random.choice(self.opponents)
        home_power = home.get_match_power()
        away_power = away.get_match_power()
        total_power = home_power + away_power if (home_power + away_power) > 0 else 1

        self.log("=" * 60)
        self.log(f"  ⚽  {home.name}  VS  {away.name}")
        self.log(f"  전술: {home.formation} | 패스: {home.passing_style} | 압박: {home.pressing_line}")
        self.log(f"  팀 전력  {home.name}: {home_power:.1f}  |  {away.name}: {away_power:.1f}")
        self.log("=" * 60)

        home_goals = 0
        away_goals = 0
        scorers = []  # (분, 팀명, 득점자)

        # 전반 / 후반 각 45분을 이벤트 블록으로 나눠 진행
        for half in range(1, 3):
            half_label = "전반" if half == 1 else "후반"
            self.log(f"\n─── {half_label} 시작 ───")
            minute_offset = 0 if half == 1 else 45

            # 각 하프에서 발생할 이벤트 타이밍 생성 (8~12개)
            event_times = sorted(random.sample(range(1, 45), k=random.randint(8, 12)))

            for t in event_times:
                minute = minute_offset + t
                # 공격 팀을 전력 비율로 랜덤 결정
                if random.random() < home_power / total_power:
                    attacking, defending = home, away
                    is_my_attack = True
                else:
                    attacking, defending = away, home
                    is_my_attack = False

                event_roll = random.random()

                if event_roll < 0.10:
                    # 파울
                    self.log(f"  {minute}' | {MatchCommentator.foul_commentary(defending)}")

                elif event_roll < 0.30:
                    # 점유/패스 장면
                    self.log(f"  {minute}' | {MatchCommentator.possession_commentary(attacking)}")

                else:
                    # 공격 전개
                    attack_line, attacker_name, gk_name = MatchCommentator.attack_commentary(attacking, defending)
                    self.log(f"  {minute}' | {attack_line}")

                    shot_roll = random.random()
                    # 슈팅 확률: 공격팀 전력이 높을수록 슈팅 장면 많이 발생
                    shot_chance = 0.55 if attacking.get_match_power() >= defending.get_match_power() else 0.40

                    if shot_roll < shot_chance:
                        # 슈팅 발생 → 득점/세이브/빗나감 판정
                        att_p = attacking.get_match_power()
                        def_p = defending.get_match_power()
                        goal_prob = (att_p / (att_p + def_p + 1)) * 0.45  # 기본 결정력

                        outcome = random.random()
                        if outcome < goal_prob:
                            # 골!
                            if attacking == home:
                                home_goals += 1
                                scorer = attacker_name
                                scorers.append((minute, home.name, scorer))
                                self.log(f"  {minute}' | " + random.choice(MatchCommentator.GOAL_TEXTS).format(
                                    scorer=scorer, home=home.name, hg=home_goals, ag=away_goals, away=away.name))
                            else:
                                away_goals += 1
                                scorer = attacker_name
                                scorers.append((minute, away.name, scorer))
                                self.log(f"  {minute}' | " + random.choice(MatchCommentator.GOAL_TEXTS).format(
                                    scorer=scorer, home=home.name, hg=home_goals, ag=away_goals, away=away.name))
                        elif outcome < goal_prob + 0.25:
                            self.log(f"  {minute}' | " + random.choice(MatchCommentator.SHOT_SAVED).format(gk=gk_name))
                        else:
                            self.log(f"  {minute}' | " + random.choice(MatchCommentator.SHOT_MISS))

            # 하프타임 요약
            if half == 1:
                self.log(f"\n  ─── 전반 종료 ─── {home.name} {home_goals} : {away_goals} {away.name}")
                self.log(f"  ─── 후반 시작 전 ─── 감독 교체 가능\n")

        # ── 최종 결과 ──────────────────────────────────────────────────────────
        self.log("\n" + "=" * 60)
        self.log(f"  최종 결과:  {home.name}  {home_goals} : {away_goals}  {away.name}")
        self.log("=" * 60)

        if scorers:
            self.log("\n  ⚽ 득점 기록")
            for minute, team, scorer in scorers:
                self.log(f"    {minute}' {scorer} ({team})")

        # 경기 결과 판정
        if home_goals > away_goals:
            self.log(f"\n  ✅ 승리! {home.name}이 {away.name}을 꺾었다.")
        elif home_goals < away_goals:
            self.log(f"\n  ❌ 패배. {away.name}에게 졌다.")
        else:
            self.log(f"\n  🤝 무승부. 양 팀이 승점 1점씩 나눠 가졌다.")

        # ── 선수 체력/부상 처리 ────────────────────────────────────────────────
        self.log("\n  ── 경기 후 선수 상태 ──")
        for p in home.starters:
            drain = random.randint(15, 25)
            if home.pressing_line == "전방 압박":
                drain += 10
            p.stamina = max(0, p.stamina - drain)
            if random.random() < 0.03:
                p.injured_days = random.randint(1, 3)
                self.log(f"  🚨 {p.name} 부상! ({p.injured_days}턴 아웃)")

        for p in home.subs:
            p.stamina = min(100, p.stamina + 10)

        self.log("")

    def save_game(self):
        if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR, exist_ok=True)
        try:
            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump({"my_team": self.my_team.to_dict()}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.log(f"저장 오류: {e}")

    def load_game(self):
        if not os.path.exists(SAVE_FILE):
            self.setup_new_game()
            return
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)["my_team"]

                def parse_players(p_list):
                    return [Player(
                        p["name"], p["position"],
                        p.get("pac", 70), p.get("sho", 70), p.get("pas", 70),
                        p.get("def", 70), p.get("phy", 70), p.get("price", 50),
                        p.get("stamina", 100), p.get("injured_days", 0), p.get("instruction", "기본")
                    ) for p in p_list]

                starters = parse_players(data.get("starters", []))
                subs = parse_players(data.get("subs", []))
                self.my_team = Team(data["name"], data.get("budget", 200), starters, subs)
                self.my_team.formation = data.get("formation", "4-3-3")
                self.my_team.passing_style = data.get("passing_style", "혼합")
                self.my_team.pressing_line = data.get("pressing_line", "일반")
            self.log("데이터 로드 완료.")
        except Exception:
            self.setup_new_game()


class FM_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FM 시뮬레이터 - 전술/교체 마스터판")
        self.root.geometry("820x640")

        self.text_area = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, width=110, height=32,
            font=("Consolas", 9), bg="#1a1a2e", fg="#e0e0e0",
            insertbackground="white"
        )
        self.text_area.pack(pady=10, padx=10)

        # 태그 색상 설정 (골, 경고 등 강조)
        self.text_area.tag_config("goal", foreground="#FFD700")
        self.text_area.tag_config("injury", foreground="#FF6B6B")
        self.text_area.tag_config("header", foreground="#87CEEB")

        f1 = tk.Frame(root)
        f1.pack(pady=5)
        tk.Button(f1, text="스쿼드 확인", command=lambda: self.engine.show_squad_detailed(), width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="선수 교체", command=self.cmd_substitute, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="팀 전술 설정", command=self.cmd_team_tactic, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="개인 전술 설정", command=self.cmd_player_tactic, width=12).pack(side=tk.LEFT, padx=5)

        f2 = tk.Frame(root)
        f2.pack(pady=5)
        tk.Button(f2, text="다음 경기 진행", command=lambda: self.engine.play_match(), width=15,
                  bg="#2d5a27", fg="white", activebackground="#3d7a37").pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="게임 저장", command=lambda: self.engine.save_game(), width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="종료", command=self.root.quit, width=12).pack(side=tk.LEFT, padx=5)

        self.engine = SimulatorEngine(self.write_log)
        self.engine.load_game()

    def write_log(self, text):
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)

    def cmd_substitute(self):
        starter_idx = simpledialog.askinteger("교체 OUT", "뺄 선발 선수의 번호 (1~11):", parent=self.root)
        if starter_idx is None: return
        sub_idx = simpledialog.askinteger("교체 IN", "투입할 후보 선수의 번호 (1~7):", parent=self.root)
        if sub_idx is None: return
        self.engine.substitute_player(starter_idx - 1, sub_idx - 1)

    def cmd_team_tactic(self):
        passing = simpledialog.askstring("팀 전술", "패스 스타일 입력 (짧은 패스, 다이렉트, 혼합):", parent=self.root)
        if not passing: return
        pressing = simpledialog.askstring("팀 전술", "압박 라인 입력 (전방 압박, 일반, 내려앉기):", parent=self.root)
        if not pressing: return
        self.engine.set_team_tactic(passing, pressing)

    def cmd_player_tactic(self):
        target_group = simpledialog.askstring("대상 선택", "선발(1) 또는 후보(2) 입력:", parent=self.root)
        if target_group not in ['1', '2']: return
        is_starter = (target_group == '1')
        p_idx = simpledialog.askinteger("선수 선택", "개인 전술을 지시할 선수의 번호 입력:", parent=self.root)
        if p_idx is None: return
        instruction = simpledialog.askstring("개인 지침", "지침 입력 (예: 공격 가담, 수비 대기, 자유 역할, 기본):", parent=self.root)
        if instruction:
            self.engine.set_player_instruction(is_starter, p_idx - 1, instruction)


if __name__ == "__main__":
    if not is_admin():
        try: ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        except: pass
        sys.exit()
    root = tk.Tk()
    app = FM_GUI(root)
    root.mainloop()
