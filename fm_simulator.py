import os
import sys
import json
import random
import ctypes
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, ttk

SAVE_DIR = r"C:\MANAGER_SIMULATOR"
SAVE_FILE = os.path.join(SAVE_DIR, "fm_ultimate_v14.json")
TRANSFER_MONTHS = {1, 7, 8}

INSTRUCTIONS = ["기본", "공격 가담", "수비 대기", "오버래핑", "인버티드 런", "딥 라잉",
                "박스 투 박스", "전진 플레이메이커", "타깃맨", "압박 선봉"]

# 시즌 일정 순서: pl=프리미어리그, fa=FA컵, lc=리그컵, ucl=챔피언스리그
SEASON_SCHEDULE = [
    # 8월
    "pl","pl","lc",
    # 9월
    "pl","ucl","pl","pl",
    # 10월
    "pl","ucl","lc","pl","pl",
    # 11월
    "pl","ucl","pl","pl","pl",
    # 12월
    "pl","pl","lc","pl","pl","pl",
    # 1월 (이적 시장 오픈)
    "pl","fa","ucl","pl","pl","pl",
    # 2월
    "pl","fa","ucl","pl","pl",
    # 3월
    "pl","fa","ucl","pl","pl",
    # 4월
    "pl","fa","ucl","pl","pl",
    # 5월
    "pl","pl","fa","pl","pl","pl","pl",
]

COMP_LABEL = {
    "pl":  "🏴󠁧󠁢󠁥󠁮󠁧󠁿 프리미어 리그",
    "fa":  "🏆 FA컵",
    "lc":  "🥈 리그컵",
    "ucl": "⭐ UEFA 챔피언스리그",
}

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

# ══════════════════════════════════════════════════════════════════════════════
# 1. 날짜
# ══════════════════════════════════════════════════════════════════════════════
class GameDate:
    MONTH_NAMES = ["","1월","2월","3월","4월","5월","6월",
                   "7월","8월","9월","10월","11월","12월"]
    def __init__(self, year=2026, month=8, day=1):
        self.year=year; self.month=month; self.day=day
    def advance_match(self, team=None, pool=None):
        self.day+=7
        if self.day>28:
            self.day-=28; self.month+=1
            if self.month>12:
                self.month=1; self.year+=1
                if team:
                    for p in team.all_players(): p.age+=1
                if pool:
                    for p in pool: p.age+=1
    def is_transfer_window(self): return self.month in TRANSFER_MONTHS
    def __str__(self): return f"{self.year}년 {self.MONTH_NAMES[self.month]} {self.day}일"
    def to_dict(self): return {"year":self.year,"month":self.month,"day":self.day}
    @classmethod
    def from_dict(cls,d): return cls(d.get("year",2026),d.get("month",8),d.get("day",1))

# ══════════════════════════════════════════════════════════════════════════════
# 2. Player & Team
# ══════════════════════════════════════════════════════════════════════════════
class Player:
    def __init__(self, name, pos, age, base_pac, base_sho, base_pas, base_def, base_phy,
                 price, stamina=100, inj=0, instr="기본", loaded_stats=None):
        self.name=name; self.position=pos; self.age=age; self.price=price
        self.stamina=stamina; self.injured_days=inj; self.instruction=instr
        if loaded_stats:
            for k,v in loaded_stats.items(): setattr(self,k,v)
        else:
            def r(b,lo=-5,hi=5): return max(30,min(99,b+random.randint(lo,hi)))
            self.spd=r(base_pac); self.acc=r(base_pac)
            self.fin=r(base_sho); self.pow=r(base_sho,-3,6)
            self.spa=r(base_pas,-4,6); self.vis=r(base_pas,-6,6)
            self.tak=r(base_def); self.mrk=r(base_def)
            self.str=r(base_phy,-4,6); self.jum=r(base_phy,-6,6)

    @property
    def rating(self):
        if self.position in ['ST','LW','RW']:
            return int(self.fin*0.3+self.spd*0.2+self.acc*0.2+self.pow*0.1+self.str*0.1+self.spa*0.1)
        elif self.position in ['CM','CAM','CDM']:
            return int(self.spa*0.3+self.vis*0.3+self.tak*0.1+self.str*0.1+self.pow*0.1+self.spd*0.1)
        elif self.position in ['CB','FB']:
            return int(self.tak*0.3+self.mrk*0.3+self.str*0.2+self.spd*0.1+self.jum*0.1)
        elif self.position=='GK':
            return int(self.tak*0.5+self.jum*0.3+self.str*0.2)
        return int((self.spd+self.fin+self.spa+self.tak+self.str)/5)

    def to_dict(self):
        return {"name":self.name,"position":self.position,"age":self.age,"price":self.price,
                "stamina":self.stamina,"injured_days":self.injured_days,"instruction":self.instruction,
                "detailed":{"spd":self.spd,"acc":self.acc,"fin":self.fin,"pow":self.pow,
                            "spa":self.spa,"vis":self.vis,"tak":self.tak,"mrk":self.mrk,
                            "str":self.str,"jum":self.jum}}

class Team:
    def __init__(self, name, budget, starters=None, subs=None):
        self.name=name; self.budget=budget
        self.starters=starters or []; self.subs=subs or []
        self.formation="4-3-3"
        self.mentality=50; self.pass_dir=50; self.tempo=50
        self.width=50;     self.press=50;    self.d_line=50
        self.wins=self.draws=self.losses=0

    @property
    def points(self): return self.wins*3+self.draws
    def all_players(self): return self.starters+self.subs
    def get_midfielders(self): return [p for p in self.starters if p.position in ['CM','CDM','CAM']]
    def get_attackers(self):   return [p for p in self.starters if p.position in ['ST','LW','RW']]
    def get_defenders(self):   return [p for p in self.starters if p.position in ['CB','FB']]
    def get_gk(self):          return next((p for p in self.starters if p.position=='GK'),None)

    def to_dict(self):
        return {"name":self.name,"budget":self.budget,"formation":self.formation,
                "mentality":self.mentality,"pass_dir":self.pass_dir,"tempo":self.tempo,
                "width":self.width,"press":self.press,"d_line":self.d_line,
                "wins":self.wins,"draws":self.draws,"losses":self.losses,
                "starters":[p.to_dict() for p in self.starters],
                "subs":[p.to_dict() for p in self.subs]}

# ══════════════════════════════════════════════════════════════════════════════
# 3. 대회 시스템
# ══════════════════════════════════════════════════════════════════════════════
class LeagueEntry:
    def __init__(self, name):
        self.name=name; self.w=self.d=self.l=self.gf=self.ga=0
    @property
    def pts(self): return self.w*3+self.d
    @property
    def gd(self):  return self.gf-self.ga
    @property
    def mp(self):  return self.w+self.d+self.l
    def to_dict(self):
        return {"name":self.name,"w":self.w,"d":self.d,"l":self.l,"gf":self.gf,"ga":self.ga}
    @classmethod
    def from_dict(cls,d):
        e=cls(d["name"]); e.w=d["w"]; e.d=d["d"]; e.l=d["l"]
        e.gf=d["gf"]; e.ga=d["ga"]; return e

class Competition:
    def __init__(self, name):
        self.name=name
    def to_dict(self): return {"type":self.__class__.__name__,"name":self.name}

class League(Competition):
    TEAMS = ["Manchester United","Manchester City","Arsenal","Liverpool",
             "Chelsea","Tottenham","Newcastle","Aston Villa",
             "Brighton","West Ham","Everton","Fulham",
             "Wolves","Brentford","Crystal Palace","Nottm Forest",
             "Bournemouth","Burnley","Sheffield Utd","Luton"]
    BASE_STATS = {
        "Manchester City":90,"Arsenal":87,"Liverpool":87,"Chelsea":83,
        "Tottenham":82,"Newcastle":82,"Aston Villa":81,"Brighton":79,
        "West Ham":78,"Everton":75,"Fulham":75,"Wolves":74,
        "Brentford":74,"Crystal Palace":73,"Nottm Forest":73,
        "Bournemouth":72,"Burnley":70,"Sheffield Utd":69,"Luton":68,
    }

    def __init__(self, my_team_name="Manchester United"):
        super().__init__("프리미어 리그")
        self.my_team_name=my_team_name
        self.table={n:LeagueEntry(n) for n in self.TEAMS}
        if my_team_name not in self.table:
            self.table[my_team_name]=LeagueEntry(my_team_name)
        names=list(self.table.keys())
        self.fixtures=[]
        for i,h in enumerate(names):
            for j,a in enumerate(names):
                if i!=j: self.fixtures.append((h,a))
        random.shuffle(self.fixtures)
        self.fixture_idx=0

    def next_my_fixture(self):
        mn=self.my_team_name
        while self.fixture_idx<len(self.fixtures):
            h,a=self.fixtures[self.fixture_idx]
            if h==mn or a==mn:
                return (h==mn),(a if h==mn else h)
            self._sim_cpu(h,a)
            self.fixture_idx+=1
        return None,None

    def _sim_cpu(self,home_name,away_name):
        bs_h=self.BASE_STATS.get(home_name,75)+random.randint(-5,5)
        bs_a=self.BASE_STATS.get(away_name,75)+random.randint(-5,5)
        hg=max(0,int(random.gauss(bs_h/30,1.0)))
        ag=max(0,int(random.gauss(bs_a/30,1.0)))
        self._record(home_name,away_name,hg,ag)
        self.fixture_idx+=1

    def _record(self,hn,an,hg,ag):
        h=self.table.get(hn); a=self.table.get(an)
        if not h or not a: return
        h.gf+=hg;h.ga+=ag;a.gf+=ag;a.ga+=hg
        if hg>ag: h.w+=1;a.l+=1
        elif hg<ag: a.w+=1;h.l+=1
        else: h.d+=1;a.d+=1

    def record_my_result(self,is_home,opp_name,my_g,opp_g):
        mn=self.my_team_name
        if is_home: self._record(mn,opp_name,my_g,opp_g)
        else:       self._record(opp_name,mn,opp_g,my_g)
        self.fixture_idx+=1

    def sorted_table(self):
        return sorted(self.table.values(),key=lambda e:(-e.pts,-e.gd,-e.gf,e.name))

    @property
    def is_finished(self): return self.fixture_idx>=len(self.fixtures)

    def to_dict(self):
        d=super().to_dict()
        d.update({"my_team_name":self.my_team_name,
                  "table":{k:v.to_dict() for k,v in self.table.items()},
                  "fixtures":self.fixtures,"fixture_idx":self.fixture_idx})
        return d

    @classmethod
    def from_dict(cls,d):
        obj=cls.__new__(cls); Competition.__init__(obj,d["name"])
        obj.my_team_name=d["my_team_name"]
        obj.table={k:LeagueEntry.from_dict(v) for k,v in d["table"].items()}
        obj.fixtures=[tuple(f) for f in d["fixtures"]]
        obj.fixture_idx=d["fixture_idx"]
        return obj

class KnockoutCup(Competition):
    def __init__(self, name, teams, my_team_name):
        super().__init__(name)
        self.my_team_name=my_team_name
        self.rounds_left=self._build_bracket(teams)
        self.eliminated=False; self.champion=None

    def _build_bracket(self,teams):
        t=list(teams); random.shuffle(t)
        n=1
        while n<len(t): n*=2
        t+=["BYE"]*(n-len(t))
        return [t]

    @property
    def current_round_teams(self):
        return self.rounds_left[0] if self.rounds_left else []

    def my_opponent(self):
        teams=self.current_round_teams
        if self.eliminated or self.champion or not teams: return None
        if self.my_team_name not in teams: return None
        idx=teams.index(self.my_team_name)
        opp=teams[idx^1]
        return opp if opp!="BYE" else None

    def advance_cpu_matches(self):
        teams=self.current_round_teams
        winners=[]; mn=self.my_team_name; i=0
        while i<len(teams):
            h,a=teams[i],teams[i+1]
            if mn in (h,a): winners.append(mn); i+=2; continue
            if h=="BYE": winners.append(a); i+=2; continue
            if a=="BYE": winners.append(h); i+=2; continue
            winners.append(random.choice([h,a])); i+=2
        self.rounds_left[0]=winners

    def record_my_result(self,won):
        teams=self.current_round_teams; mn=self.my_team_name
        if not won:
            self.eliminated=True
            idx=teams.index(mn); teams[idx]=teams[idx^1]
        self.advance_cpu_matches()
        if len(self.rounds_left[0])==1:
            self.champion=self.rounds_left[0][0]; self.rounds_left=[]
        elif len(self.rounds_left[0])>1:
            self.rounds_left=[self.rounds_left[0]]

    def round_name(self):
        n=len(self.current_round_teams)
        names={64:"64강",32:"32강",16:"16강",8:"8강",4:"4강",2:"결승"}
        return names.get(n,f"{n}강")

    def to_dict(self):
        d=super().to_dict()
        d.update({"my_team_name":self.my_team_name,"rounds_left":self.rounds_left,
                  "eliminated":self.eliminated,"champion":self.champion})
        return d

    @classmethod
    def from_dict(cls,d):
        obj=cls.__new__(cls); Competition.__init__(obj,d["name"])
        obj.my_team_name=d["my_team_name"]; obj.rounds_left=d["rounds_left"]
        obj.eliminated=d["eliminated"]; obj.champion=d["champion"]
        return obj

class UCL(Competition):
    GROUP_TEAMS={
        "A":["Manchester United","Real Madrid","PSG","Galatasaray"],
        "B":["Manchester City","Bayern","Napoli","Copenhagen"],
        "C":["Arsenal","Inter","Sporting","FC Porto"],
        "D":["Liverpool","Barcelona","Shakhtar","Lens"],
    }
    def __init__(self,my_team_name="Manchester United"):
        super().__init__("UEFA 챔피언스 리그")
        self.my_team_name=my_team_name
        self.my_group=None
        for g,teams in self.GROUP_TEAMS.items():
            if my_team_name in teams: self.my_group=g; break
        if not self.my_group:
            self.my_group="A"; self.GROUP_TEAMS["A"][3]=my_team_name
        self.group_table={g:{n:LeagueEntry(n) for n in teams} for g,teams in self.GROUP_TEAMS.items()}
        self.group_fixtures={g:[] for g in self.GROUP_TEAMS}
        for g,teams in self.GROUP_TEAMS.items():
            for i,h in enumerate(teams):
                for j,a in enumerate(teams):
                    if i!=j: self.group_fixtures[g].append((h,a))
            random.shuffle(self.group_fixtures[g])
        self.group_fixture_idx={g:0 for g in self.GROUP_TEAMS}
        self.phase="group"; self.ko=None

    @property
    def group_done(self):
        return self.group_fixture_idx[self.my_group]>=len(self.group_fixtures[self.my_group])

    @property
    def is_active(self):
        if self.phase=="group": return not self.group_done
        if self.phase=="knockout" and self.ko:
            return not self.ko.eliminated and not self.ko.champion
        return False

    def next_group_fixture(self):
        g=self.my_group; mn=self.my_team_name
        fixtures=self.group_fixtures[g]; idx=self.group_fixture_idx[g]
        while idx<len(fixtures):
            h,a=fixtures[idx]
            if h==mn or a==mn: return (h==mn),(a if h==mn else h)
            self._sim_group_cpu(g,h,a); idx+=1
        return None,None

    def _sim_group_cpu(self,g,h,a):
        hg=max(0,int(random.gauss(1.2,0.8))); ag=max(0,int(random.gauss(1.0,0.8)))
        self._record_group(g,h,a,hg,ag); self.group_fixture_idx[g]+=1

    def _record_group(self,g,hn,an,hg,ag):
        h=self.group_table[g].get(hn); a=self.group_table[g].get(an)
        if not h or not a: return
        h.gf+=hg;h.ga+=ag;a.gf+=ag;a.ga+=hg
        if hg>ag: h.w+=1;a.l+=1
        elif hg<ag: a.w+=1;h.l+=1
        else: h.d+=1;a.d+=1

    def record_my_group_result(self,is_home,opp,mg,og):
        g=self.my_group; mn=self.my_team_name
        if is_home: self._record_group(g,mn,opp,mg,og)
        else:       self._record_group(g,opp,mn,og,mg)
        self.group_fixture_idx[g]+=1
        for gg in self.GROUP_TEAMS:
            if gg==g: continue
            while self.group_fixture_idx[gg]<len(self.group_fixtures[gg]):
                hh,aa=self.group_fixtures[gg][self.group_fixture_idx[gg]]
                self._sim_group_cpu(gg,hh,aa)

    def init_knockout(self):
        qualifiers=[]
        for g in sorted(self.GROUP_TEAMS.keys()):
            sorted_t=sorted(self.group_table[g].values(),key=lambda e:(-e.pts,-e.gd,-e.gf))
            qualifiers+=[t.name for t in sorted_t[:2]]
        self.ko=KnockoutCup("UCL 토너먼트",qualifiers,self.my_team_name)
        self.phase="knockout"

    def sorted_group(self,g):
        return sorted(self.group_table[g].values(),key=lambda e:(-e.pts,-e.gd,-e.gf,e.name))

    def to_dict(self):
        d=super().to_dict()
        d.update({"my_team_name":self.my_team_name,"my_group":self.my_group,
                  "group_table":{g:{n:e.to_dict() for n,e in t.items()} for g,t in self.group_table.items()},
                  "group_fixtures":self.group_fixtures,"group_fixture_idx":self.group_fixture_idx,
                  "phase":self.phase,"ko":self.ko.to_dict() if self.ko else None})
        return d

    @classmethod
    def from_dict(cls,d):
        obj=cls.__new__(cls); Competition.__init__(obj,d["name"])
        obj.my_team_name=d["my_team_name"]; obj.my_group=d["my_group"]
        obj.group_table={g:{n:LeagueEntry.from_dict(e) for n,e in t.items()} for g,t in d["group_table"].items()}
        obj.group_fixtures={g:[tuple(f) for f in fx] for g,fx in d["group_fixtures"].items()}
        obj.group_fixture_idx=d["group_fixture_idx"]; obj.phase=d["phase"]
        obj.ko=KnockoutCup.from_dict(d["ko"]) if d.get("ko") else None
        return obj

# ══════════════════════════════════════════════════════════════════════════════
# 4. 이적 풀
# ══════════════════════════════════════════════════════════════════════════════
TRANSFER_POOL_DATA = [
    # ══ ST ══
    ("Haaland","ST",25,88,94,65,40,90,200),("Mbappe","ST",27,96,91,80,38,82,190),
    ("Kane","ST",32,72,93,86,42,82,85),("Osimhen","ST",27,90,86,70,38,86,110),
    ("Gyokeres","ST",28,84,89,72,44,88,110),("Isak","ST",26,88,85,75,40,78,95),
    ("Endrick","ST",20,88,84,70,42,82,95),("L. Martinez","ST",28,82,88,75,45,84,105),
    ("Zirkzee","ST",25,78,83,78,44,80,70),("Watkins","ST",30,84,84,76,46,78,65),
    ("Nunez","ST",26,90,82,68,42,85,75),("Sesko","ST",23,88,82,70,44,82,85),
    ("Openda","ST",25,90,82,72,42,80,80),("Vlahovic","ST",26,78,86,70,44,84,75),
    ("Fullkrug","ST",33,70,84,72,50,86,40),("Benzema","ST",38,68,84,80,42,74,20),
    ("Depay","ST",32,86,82,78,44,76,25),("Firmino","ST",34,76,80,82,50,74,15),
    ("Mitrovic","ST",31,72,88,62,48,86,45),("Calvert-Lewin","ST",29,80,82,68,46,80,45),
    ("Havertz","ST",27,80,82,84,58,78,80),("Joelinton","ST",29,82,76,76,62,86,50),
    ("Pavlidis","ST",28,78,84,68,42,82,50),("Giroud","ST",40,64,80,74,50,82,10),
    # ══ LW/RW ══
    ("Vinicius Jr","LW",25,96,86,80,40,78,170),("Yamal","RW",19,93,85,82,42,68,165),
    ("Saka","RW",24,88,84,84,60,74,115),("Kvaratskhelia","LW",25,88,82,80,48,76,125),
    ("Leao","LW",27,92,80,76,42,78,115),("Rodrygo","RW",25,88,82,80,42,70,95),
    ("Salah","RW",34,86,88,82,46,74,50),("Diaz","LW",29,88,80,76,52,78,80),
    ("Raphinha","RW",29,90,84,78,50,76,90),("Foden","LW",26,88,85,86,52,68,120),
    ("Son Heung-min","LW",34,88,88,80,42,72,55),("Pulisic","RW",28,86,80,80,52,72,55),
    ("Lookman","LW",28,88,82,76,50,74,75),("Antony","RW",26,86,76,74,46,68,30),
    ("Doku","LW",23,96,76,74,44,76,90),("Coman","LW",30,92,78,76,52,76,50),
    ("Gnabry","RW",31,88,80,78,52,76,45),("Mane","LW",35,86,82,76,46,78,20),
    ("Sancho","RW",26,86,78,80,50,70,35),("Sterling","LW",32,86,78,78,50,72,25),
    ("Neto","RW",25,88,78,76,48,72,60),("Chukwueze","RW",28,86,78,74,50,72,50),
    ("Garnacho","RW",22,86,78,74,44,64,55),("Madueke","RW",24,86,78,76,48,70,55),
    ("Mudryk","LW",25,88,76,74,48,72,45),("Savinho","RW",22,90,76,76,46,72,75),
    ("Conceicao","RW",23,90,78,74,46,70,70),("Rashford","LW",28,88,84,78,46,76,55),
    ("Greenwood","RW",24,84,80,76,54,76,45),
    # ══ CAM ══
    ("Bellingham","CAM",23,82,87,88,72,84,165),("Wirtz","CAM",23,84,86,90,62,74,160),
    ("Musiala","CAM",23,86,83,87,60,74,145),("Odegaard","CAM",27,80,83,92,62,72,105),
    ("Guler","CAM",21,80,78,85,52,62,75),("Olise","CAM",24,84,82,82,54,70,90),
    ("Szoboszlai","CAM",25,82,78,84,64,80,80),("Griezmann","CAM",35,78,84,82,62,72,45),
    ("Mount","CAM",27,78,80,84,66,72,50),("Havertz K.","CAM",27,80,82,84,58,78,80),
    ("Almada","CAM",25,82,78,84,56,72,60),
    # ══ CM ══
    ("Pedri","CM",23,82,78,91,74,70,110),("Gavi","CM",22,82,74,88,78,76,95),
    ("Valverde","CM",28,88,82,86,80,84,105),("Barella","CM",28,80,78,86,82,84,90),
    ("Camavinga","CM",23,84,75,84,82,80,95),("Mac Allister","CM",27,76,80,86,78,78,85),
    ("Kimmich","CM",31,76,72,90,86,78,75),("Alexander-Arnold","CM",27,80,76,90,78,74,85),
    ("De Bruyne","CM",35,74,85,94,60,72,55),("Eriksen","CM",34,64,78,90,58,64,20),
    ("Kroos","CM",36,64,78,92,72,66,15),("Goretzka","CM",31,80,76,84,78,84,50),
    ("Thuram M.","CM",28,82,74,84,76,82,80),("Neves R.","CM",29,76,74,86,80,78,65),
    ("Gallagher","CM",26,82,72,78,78,84,55),("Ruiz F.","CM",24,78,74,86,70,74,65),
    ("Zaire-Emery","CM",21,82,72,86,80,80,95),("Fernandez B.","CM",25,76,74,86,78,76,80),
    # ══ CDM ══
    ("Rodri","CDM",30,76,78,90,88,86,115),("Rice","CDM",27,80,70,84,86,86,105),
    ("Caicedo","CDM",24,78,68,80,86,86,90),("Tchouameni","CDM",26,78,70,82,86,85,90),
    ("Ugarte","CDM",26,80,66,82,86,86,60),("Partey","CDM",33,78,68,76,82,82,30),
    ("Guendouzi","CDM",26,78,68,78,80,78,45),("Douglas Luiz","CDM",28,76,70,80,82,80,60),
    ("Andre","CDM",24,76,64,80,82,82,60),("Joao Neves","CDM",21,78,66,82,82,78,90),
    ("Bissouma","CDM",29,78,64,76,82,82,45),("Mainoo K.","CM",21,80,74,86,78,74,55),
    # ══ CB ══
    ("Van Dijk","CB",35,82,56,74,90,88,65),("Saliba","CB",25,78,40,72,88,86,95),
    ("Bastoni","CB",27,76,45,78,88,82,90),("Araujo","CB",27,82,46,66,88,86,85),
    ("Dias","CB",29,72,40,70,88,88,80),("Gvardiol","CB",24,80,56,78,86,84,98),
    ("Kim Min-jae","CB",29,84,40,70,86,88,75),("Romero","CB",28,76,50,72,86,85,75),
    ("Yoro","CB",20,80,40,70,82,80,80),("Branthwaite","CB",24,74,46,68,84,86,70),
    ("Upamecano","CB",27,82,48,74,87,88,65),("Tah","CB",30,78,52,76,88,86,55),
    ("Timber","CB",24,82,52,76,84,82,80),("Dean Huijsen","CB",21,78,44,72,82,82,70),
    ("Pavard","CB",29,80,50,74,84,80,60),("Akanji","CB",31,80,46,72,86,84,55),
    ("Skriniar","CB",31,74,44,68,86,86,40),("Maguire","CB",33,72,54,70,84,86,25),
    ("Laporte","CB",32,74,50,76,86,84,30),("Kounde","FB",28,84,58,76,84,80,70),
    ("Todibo","CB",26,78,44,70,84,82,55),("Lacroix","CB",25,78,44,70,84,82,55),
    # ══ FB ══
    ("Hakimi","FB",27,93,75,82,78,80,95),("Davies","FB",25,92,66,78,80,82,80),
    ("Theo Hernandez","FB",28,90,72,78,80,82,75),
    ("Alexander-Arnold T.","FB",27,80,76,92,78,76,85),
    ("Frimpong","FB",25,93,75,80,74,70,85),("Udogie","FB",23,88,68,76,78,80,70),
    ("White","FB",28,78,60,80,84,80,65),("Dimarco","FB",28,84,78,86,76,74,70),
    ("Wan-Bissaka","FB",28,84,42,66,86,76,30),("Dalot","FB",27,85,65,80,80,76,45),
    ("Mazraoui","FB",28,82,62,76,82,78,40),("Cancelo","FB",32,84,68,82,78,76,30),
    ("Shaw","FB",29,78,62,80,82,80,30),("Robertson","FB",33,82,64,82,80,78,30),
    ("Balde","FB",22,88,66,76,78,80,65),("Dumfries","FB",30,86,70,76,78,78,40),
    # ══ GK ══
    ("Alisson","GK",33,62,15,74,91,80,70),("Donnarumma","GK",27,60,15,68,89,85,80),
    ("Courtois","GK",34,55,15,70,90,82,55),("Ederson","GK",32,64,20,86,88,78,60),
    ("Maignan","GK",31,65,18,76,88,82,65),("Vicario","GK",29,60,15,72,86,78,55),
    ("Kobel","GK",28,58,15,70,86,80,60),("Raya","GK",30,58,15,74,86,78,50),
    ("Ter Stegen","GK",34,56,12,80,87,76,50),("Oblak","GK",33,50,12,70,89,80,50),
    ("Pope","GK",34,50,12,68,86,80,30),("Nubel","GK",29,54,15,68,84,78,40),
    ("Kepa","GK",31,54,12,70,84,74,20),("de Gea","GK",35,48,12,66,84,72,5),
]

def make_transfer_pool():
    seen=set(); pool=[]
    for row in TRANSFER_POOL_DATA:
        if row[0] in seen: continue
        seen.add(row[0]); pool.append(Player(*row))
    return pool

# ══════════════════════════════════════════════════════════════════════════════
# 5. 매치 엔진
# ══════════════════════════════════════════════════════════════════════════════
FA_CUP_TEAMS = [
    "Manchester United","Manchester City","Arsenal","Liverpool",
    "Chelsea","Tottenham","Newcastle","Aston Villa",
    "Brighton","West Ham","Everton","Fulham",
    "Wolves","Brentford","Crystal Palace","Nottm Forest",
    "Bournemouth","Burnley","Sheffield Utd","Luton",
    "QPR","Millwall","Sunderland","Middlesbrough",
    "Swansea","Reading","Derby","Coventry",
    "Plymouth","Watford","Stoke","Blackburn",
]
LEAGUE_CUP_TEAMS = FA_CUP_TEAMS[:16]

class SimulatorEngine:
    def __init__(self, root, log_cb, date_cb=None):
        self.root=root; self.log=log_cb; self.date_callback=date_cb
        self.game_date=GameDate()
        self.transfer_pool=make_transfer_pool()
        self.my_team=None
        self.league=None; self.fa_cup=None; self.league_cup=None; self.ucl=None
        self.schedule_idx=0
        self._cpu_pool={}

    # ── CPU 팀 생성 ──────────────────────────────────────────────────────────
    def _get_cpu(self,name):
        if name not in self._cpu_pool:
            base_stats={
                "Manchester City":90,"Arsenal":87,"Liverpool":87,"Chelsea":83,
                "Tottenham":82,"Newcastle":82,"Aston Villa":81,"Brighton":79,
                "West Ham":78,"Everton":75,"Fulham":75,"Wolves":74,
                "Brentford":74,"Crystal Palace":73,"Nottm Forest":73,
                "Bournemouth":72,"Burnley":70,"Sheffield Utd":69,"Luton":68,
                "Real Madrid":90,"PSG":88,"Bayern":88,"Barcelona":87,
                "Inter":86,"Napoli":83,"Galatasaray":76,"Sporting":78,
                "FC Porto":78,"Shakhtar":74,"Copenhagen":72,"Lens":73,
            }
            base=base_stats.get(name,72)+random.randint(-3,3)
            pos_list=['GK','FB','CB','CB','FB','CDM','CM','CM','LW','ST','RW']
            starters=[Player(f"{name[:3]}{i+1}",pos,random.randint(22,32),
                             base,base,base,base,base,50)
                      for i,pos in enumerate(pos_list)]
            t=Team(name,500,starters,[])
            t.mentality=random.randint(35,75); t.press=random.randint(35,75)
            self._cpu_pool[name]=t
        return self._cpu_pool[name]

    def _notify_date(self):
        if self.date_callback: self.date_callback(str(self.game_date))

    # ── 신규 게임 ─────────────────────────────────────────────────────────────
    def setup_new_game(self):
        self.log("2026년, 맨체스터 유나이티드의 새 감독으로 부임했다.")
        starters=[
            Player("Onana","GK",30,62,20,82,86,82,45),
            Player("Dalot","FB",27,85,65,80,80,76,40),
            Player("L. Martinez","CB",28,78,48,76,88,84,55),
            Player("De Ligt","CB",26,80,48,72,88,86,50),
            Player("Mazraoui","FB",28,82,62,76,82,78,40),
            Player("Ugarte","CDM",25,80,68,82,86,86,55),
            Player("Mainoo","CM",21,80,74,86,78,74,50),
            Player("Bruno","CAM",31,75,85,90,65,75,80),
            Player("Rashford","LW",28,88,84,78,46,76,60),
            Player("Garnacho","RW",22,86,78,74,44,64,50),
            Player("Hojlund","ST",23,86,84,70,42,86,60),
        ]
        subs=[
            Player("Amad","RW",24,84,76,74,50,68,40),
            Player("Zirkzee","ST",25,78,82,78,44,80,55),
            Player("Eriksen","CM",34,62,76,90,58,62,25),
            Player("Bayindir","GK",27,55,14,66,82,76,12),
            Player("Lindelof","CB",31,76,44,72,84,80,18),
            Player("Maguire","CB",34,70,52,70,82,84,20),
            Player("Shaw","FB",30,78,60,78,80,78,28),
            Player("Casemiro","CDM",35,72,68,78,84,86,15),
            Player("Hannibal","CM",23,78,72,80,68,72,20),
            Player("Pellistri","RW",23,88,72,70,46,70,18),
        ]
        self.my_team=Team("Manchester United",250,starters,subs)
        self.game_date=GameDate(2026,8,8)
        self.schedule_idx=0
        self._init_competitions()
        self._notify_date(); self.save_game()

    def _init_competitions(self):
        mn=self.my_team.name
        self.league=League(mn)
        self.fa_cup=KnockoutCup("FA컵",FA_CUP_TEAMS,mn)
        self.league_cup=KnockoutCup("리그컵",LEAGUE_CUP_TEAMS,mn)
        self.ucl=UCL(mn)

    # ── 다음 경기 (일정 기반) ─────────────────────────────────────────────────
    def peek_next_match(self):
        """다음 경기 대회명 미리보기 (진행하지 않음)"""
        idx=self.schedule_idx
        while idx<len(SEASON_SCHEDULE):
            comp=SEASON_SCHEDULE[idx]
            if self._comp_available(comp): return COMP_LABEL[comp]
            idx+=1
        return None

    def _comp_available(self,comp):
        if comp=="pl":  return not self.league.is_finished
        if comp=="fa":  return not self.fa_cup.eliminated and not self.fa_cup.champion
        if comp=="lc":  return not self.league_cup.eliminated and not self.league_cup.champion
        if comp=="ucl": return self.ucl.is_active
        return False

    def next_match(self):
        """일정에 따라 다음 경기 자동 실행"""
        while self.schedule_idx<len(SEASON_SCHEDULE):
            comp=SEASON_SCHEDULE[self.schedule_idx]
            self.schedule_idx+=1
            if not self._comp_available(comp):
                continue
            # 어떤 대회인지 예고
            self.log(f"\n  ▶▶  다음 경기: {COMP_LABEL[comp]}")
            if self.game_date.is_transfer_window():
                self.log(f"  💰 이적 시장이 열려 있습니다! ({self.game_date})")
            if comp=="pl":   self._play_league(); return
            if comp=="fa":   self._play_cup(self.fa_cup,  "FA컵"); return
            if comp=="lc":   self._play_cup(self.league_cup,"리그컵"); return
            if comp=="ucl":  self._play_ucl(); return

        self.log("\n🏁 이번 시즌 모든 일정이 완료되었다!")
        self._show_league_table()

    # ── 경기 핵심 로직 ────────────────────────────────────────────────────────
    def _sim_match(self,home,away_team_obj):
        hm=home; am=away_team_obj; hg=ag=0
        for half in range(1,3):
            offset=0 if half==1 else 45
            ec=random.randint(12,16)+int(hm.tempo/25)
            for t in sorted(random.sample(range(1,45),k=ec)):
                minute=offset+t
                hm_mid=sum(p.vis+p.spa for p in (hm.get_midfielders() or hm.starters))*(hm.mentality/50.0)
                am_mid=sum(p.vis+p.spa for p in (am.get_midfielders() or am.starters))*(am.mentality/50.0)
                atk=hm if random.random()<(hm_mid/(hm_mid+am_mid+1)) else am
                dfn=am if atk==hm else hm
                attacker=random.choice(atk.get_attackers() or atk.starters)
                passer=random.choice(atk.get_midfielders() or atk.starters)
                defender=random.choice(dfn.get_defenders() or dfn.starters)
                gk=dfn.get_gk()
                event_roll=random.random()
                if atk==hm and random.randint(1,100)<hm.pass_dir:
                    if attacker.spd+attacker.str+random.randint(-15,20)>defender.jum+(100-dfn.d_line):
                        self.log(f"  {minute:2d}' | 🚀 롱볼! {attacker.name}이(가) 공중볼을 따냅니다!")
                        if attacker.fin+attacker.pow+random.randint(-10,20)>(gk.tak+gk.jum if gk else 140):
                            self.log(f"  {minute:2d}' | ⚽ GOAL! {attacker.name}의 득점!"); hg+=1
                        else:
                            self.log(f"  {minute:2d}' | 💥 슛이 약했습니다. 골키퍼 캐치.")
                    else:
                        self.log(f"  {minute:2d}' | 🛡️ 롱볼 실패. {defender.name}이(가) 헤더로 걷어냅니다.")
                elif event_roll<0.40:
                    pb=dfn.press/5.0 if dfn==hm else 10.0
                    if passer.vis+passer.spa+random.randint(-20,20)>defender.mrk+defender.tak+pb:
                        self.log(f"  {minute:2d}' | 🎯 {passer.name}의 패스! (시야 {passer.vis})")
                        if attacker.fin+random.randint(-15,20)>(gk.tak if gk else 70):
                            self.log(f"  {minute:2d}' | ⚽ GOAL! {attacker.name}의 슛!")
                            if atk==hm: hg+=1
                            else: ag+=1
                        else:
                            self.log(f"  {minute:2d}' | 🥅 {attacker.name}의 슈팅! 빗나갑니다.")
                    else:
                        self.log(f"  {minute:2d}' | 🧱 {defender.name}이(가) 패스 길목을 차단!")
                else:
                    self.log(f"  {minute:2d}' | {atk.name} 볼 점유 중...")
            if half==1:
                self.log(f"\n  ─── 전반 종료 ───  {hm.name} {hg}:{ag} {am.name}\n  ─── 후반 시작 ───\n")
        return hg,ag

    def _post_match_stamina(self):
        hm=self.my_team
        for p in hm.starters:
            drain=10+int(hm.tempo/10)+int(hm.press/10)+random.randint(0,5)
            p.stamina=max(0,p.stamina-drain)
            risk=(0.05 if p.age>=33 else 0.02)+(0.04 if p.stamina<30 else 0)
            if random.random()<risk:
                p.injured_days=random.randint(1,4)
                self.log(f"  🚨 {p.name} 부상! ({p.injured_days}주 아웃)")
        for p in hm.subs:
            p.stamina=min(100,p.stamina+(15 if p.age<33 else 10))
        self.game_date.advance_match(hm,self.transfer_pool)
        self._notify_date()
        for p in hm.all_players():
            if p.injured_days>0: p.injured_days-=1

    def _match_header(self,comp_name,home_name,away_name,is_home):
        hm=self.my_team
        self.log(f"\n{'='*70}")
        self.log(f"  📅 {self.game_date}  |  {comp_name}")
        if is_home:
            self.log(f"  ⚽  {home_name}  (홈)  VS  {away_name}  (원정)")
        else:
            self.log(f"  ⚽  {away_name}  (원정)  VS  {home_name}  (홈)")
        self.log(f"  전술: {hm.formation} | 성향: {hm.mentality} | 압박: {hm.press} | 템포: {hm.tempo}")
        self.log(f"{'='*70}")

    # ── 프리미어 리그 ─────────────────────────────────────────────────────────
    def _play_league(self):
        if self.league.is_finished:
            self.log("이번 시즌 리그 일정이 모두 끝났다."); return
        is_home,opp_name=self.league.next_my_fixture()
        if opp_name is None:
            self.log("리그 시즌 종료!"); self._show_league_table(); return
        opp=self._get_cpu(opp_name)
        self._match_header("🏴󠁧󠁢󠁥󠁮󠁧󠁿 프리미어 리그",self.my_team.name,opp_name,is_home)
        if is_home: hg,ag=self._sim_match(self.my_team,opp)
        else:
            ag,hg=self._sim_match(self.my_team,opp); hg,ag=ag,hg
        self.log(f"\n  최종: {self.my_team.name} {hg}:{ag} {opp_name}")
        if hg>ag:   self.my_team.wins+=1;   self.log("  ✅ 승리!")
        elif hg<ag: self.my_team.losses+=1; self.log("  ❌ 패배.")
        else:       self.my_team.draws+=1;  self.log("  🤝 무승부.")
        self.league.record_my_result(is_home,opp_name,hg,ag)
        self._post_match_stamina()
        if self.league.is_finished: self._show_league_table()
        self.save_game()

    def _show_league_table(self):
        self.log(f"\n{'─'*65}")
        self.log(f"  🏆 프리미어 리그 순위표")
        self.log(f"  {'순위':<4}{'팀':<22}{'경기':>4}{'승':>4}{'무':>4}{'패':>4}{'득':>4}{'실':>4}{'GD':>5}{'승점':>5}")
        self.log(f"  {'─'*62}")
        for i,e in enumerate(self.league.sorted_table(),1):
            marker=" ◀" if e.name==self.my_team.name else ""
            self.log(f"  {i:<4}{e.name:<22}{e.mp:>4}{e.w:>4}{e.d:>4}{e.l:>4}"
                     f"{e.gf:>4}{e.ga:>4}{e.gd:>+5}{e.pts:>5}{marker}")
        self.log(f"  {'─'*62}\n")

    # ── 컵 대회 ───────────────────────────────────────────────────────────────
    def _play_cup(self,cup,cup_name):
        if cup.eliminated:
            self.log(f"이미 {cup_name}에서 탈락했다."); return
        if cup.champion:
            self.log(f"{cup_name} 우승: {cup.champion}"); return
        opp_name=cup.my_opponent()
        if opp_name is None:
            cup.advance_cpu_matches()
            self.log(f"  🎉 {cup_name} {cup.round_name()} 부전승! 다음 라운드 진출.")
            cup.record_my_result(True)
            if cup.champion: self.log(f"  🏆 {cup_name} 우승!!")
            self.save_game(); return
        self._match_header(f"{'🏆' if '리그컵' not in cup_name else '🥈'} {cup_name} {cup.round_name()}",
                           self.my_team.name,opp_name,True)
        opp=self._get_cpu(opp_name)
        hg,ag=self._sim_match(self.my_team,opp)
        if hg==ag:
            self.log("  ⏱️  연장전 돌입!")
            eg=random.randint(0,1); eag=random.randint(0,1)
            hg+=eg; ag+=eag
            if hg==ag:
                self.log("  🎯 승부차기!")
                if random.random()<0.5: hg+=1
                else: ag+=1
        self.log(f"\n  최종: {self.my_team.name} {hg}:{ag} {opp_name}")
        won=hg>ag
        if won: self.my_team.wins+=1;   self.log(f"  ✅ {cup_name} {cup.round_name()} 통과!")
        else:   self.my_team.losses+=1; self.log(f"  ❌ {cup_name} 탈락.")
        cup.record_my_result(won)
        if cup.champion: self.log(f"  🏆🏆🏆  {cup_name} 우승!!!  🏆🏆🏆")
        self._post_match_stamina(); self.save_game()

    # ── 챔피언스 리그 ─────────────────────────────────────────────────────────
    def _play_ucl(self):
        ucl=self.ucl
        if ucl.phase=="group":
            if ucl.group_done:
                self.log("UCL 조별리그가 끝났다. 토너먼트 단계로 진행한다.")
                ucl.init_knockout(); self._show_ucl_groups(); self.save_game(); return
            is_home,opp_name=ucl.next_group_fixture()
            if opp_name is None:
                self.log("UCL 조별리그 완료!"); ucl.init_knockout()
                self._show_ucl_groups(); self.save_game(); return
            self._match_header(f"⭐ UCL 조별리그 (조 {ucl.my_group})",self.my_team.name,opp_name,is_home)
            opp=self._get_cpu(opp_name)
            if is_home: hg,ag=self._sim_match(self.my_team,opp)
            else: ag,hg=self._sim_match(self.my_team,opp); hg,ag=ag,hg
            self.log(f"\n  최종: {self.my_team.name} {hg}:{ag} {opp_name}")
            if hg>ag:   self.my_team.wins+=1;   self.log("  ✅ 승리!")
            elif hg<ag: self.my_team.losses+=1; self.log("  ❌ 패배.")
            else:       self.my_team.draws+=1;  self.log("  🤝 무승부.")
            ucl.record_my_group_result(is_home,opp_name,hg,ag)
        else:
            self._play_cup(ucl.ko,"UCL 토너먼트")
        self._post_match_stamina(); self.save_game()

    def _show_ucl_groups(self):
        for g in sorted(self.ucl.GROUP_TEAMS.keys()):
            self.log(f"\n  ── UCL 조 {g} ──")
            self.log(f"  {'팀':<24}{'경기':>4}{'승':>4}{'무':>4}{'패':>4}{'득':>4}{'실':>4}{'승점':>5}")
            for e in self.ucl.sorted_group(g):
                m=e.w+e.d+e.l
                self.log(f"  {e.name:<24}{m:>4}{e.w:>4}{e.d:>4}{e.l:>4}{e.gf:>4}{e.ga:>4}{e.pts:>5}")

    # ── 순위표 보기 ────────────────────────────────────────────────────────────
    def show_standings(self):
        self._show_league_table()
        self._show_ucl_groups()
        for cup in [self.fa_cup,self.league_cup]:
            if cup.champion:   self.log(f"  🏆 {cup.name} 우승: {cup.champion}")
            elif cup.eliminated: self.log(f"  ❌ {cup.name}: 탈락")
            else: self.log(f"  🔵 {cup.name}: {cup.round_name()} 진행 중")
        nxt=self.peek_next_match()
        if nxt:
            self.log(f"\n  ▶ 다음 예정 경기: {nxt}")
        else:
            self.log("\n  🏁 시즌 일정이 모두 완료되었습니다.")

    # ── 스쿼드 ────────────────────────────────────────────────────────────────
    def show_squad_detailed(self):
        win=tk.Toplevel(self.root)
        win.title("스쿼드 상세 (10-스탯)"); win.geometry("1100x600"); win.configure(bg="#0d1117")
        cols=("구분","이름","나이","포지션","OVR","속력","가속","골결","슛파워","짧패","시야","태클","대인방어","몸싸움","점프","체력")
        tree=ttk.Treeview(win,columns=cols,show="headings",height=22)
        for c in cols:
            tree.heading(c,text=c)
            tree.column(c,width=55 if c not in ["이름","구분","포지션"] else (120 if c=="이름" else 60),anchor="center")
        tree.column("이름",anchor="w"); tree.pack(fill=tk.BOTH,expand=True,padx=10,pady=10)
        for p in self.my_team.starters:
            tree.insert("","end",values=("선발",p.name,p.age,p.position,p.rating,
                                         p.spd,p.acc,p.fin,p.pow,p.spa,p.vis,p.tak,p.mrk,p.str,p.jum,p.stamina))
        for p in self.my_team.subs:
            tree.insert("","end",values=("후보",p.name,p.age,p.position,p.rating,
                                         p.spd,p.acc,p.fin,p.pow,p.spa,p.vis,p.tak,p.mrk,p.str,p.jum,p.stamina))
        t=self.my_team
        self.log(f"\n{'='*75}\n  [{self.game_date}] {t.name} | 예산:{t.budget}M | 리그 승점:{t.points}pt\n{'='*75}")

    def substitute_player(self,si,bi):
        s,b=self.my_team.starters,self.my_team.subs
        if 0<=si<len(s) and 0<=bi<len(b):
            s[si],b[bi]=b[bi],s[si]
            self.log(f"[교체] {b[bi].name} OUT ↔ {s[si].name} IN")
        else: self.log("잘못된 번호다.")

    def set_player_instruction(self,is_starter,idx,instr):
        lst=self.my_team.starters if is_starter else self.my_team.subs
        if 0<=idx<len(lst):
            lst[idx].instruction=instr
            self.log(f"[개인 지침] {lst[idx].name} → '{instr}'")

    # ── 이적 ──────────────────────────────────────────────────────────────────
    def transfer_buy(self,pool_idx,to_starter):
        if not self.game_date.is_transfer_window(): self.log("이적 시장이 닫혀 있다."); return
        if pool_idx<0 or pool_idx>=len(self.transfer_pool): return
        p=self.transfer_pool[pool_idx]
        if self.my_team.budget<p.price: self.log(f"예산 부족! {p.price}M 필요."); return
        target=self.my_team.starters if to_starter else self.my_team.subs
        if len(target)>=(11 if to_starter else 12): self.log("명단이 가득 찼다."); return
        self.my_team.budget-=p.price; target.append(p); self.transfer_pool.pop(pool_idx)
        self.log(f"[영입] {p.name} ({p.age}세, OVR:{p.rating}) -{p.price}M  잔여:{self.my_team.budget}M")
        self.save_game()

    def transfer_sell(self,is_starter,idx):
        if not self.game_date.is_transfer_window(): self.log("이적 시장이 닫혀 있다."); return
        lst=self.my_team.starters if is_starter else self.my_team.subs
        if idx<0 or idx>=len(lst): return
        p=lst.pop(idx); sp=int(p.price*random.uniform(0.6,0.9))
        self.my_team.budget+=sp; self.transfer_pool.append(p)
        self.log(f"[방출] {p.name} +{sp}M  잔여:{self.my_team.budget}M"); self.save_game()

    # ── 저장 / 로드 ───────────────────────────────────────────────────────────
    def save_game(self):
        os.makedirs(SAVE_DIR,exist_ok=True)
        try:
            with open(SAVE_FILE,'w',encoding='utf-8') as f:
                json.dump({
                    "my_team":self.my_team.to_dict(),
                    "game_date":self.game_date.to_dict(),
                    "schedule_idx":self.schedule_idx,
                    "league":self.league.to_dict() if self.league else None,
                    "fa_cup":self.fa_cup.to_dict() if self.fa_cup else None,
                    "league_cup":self.league_cup.to_dict() if self.league_cup else None,
                    "ucl":self.ucl.to_dict() if self.ucl else None,
                },f,ensure_ascii=False,indent=2)
        except Exception as e: self.log(f"저장 오류: {e}")

    def load_game(self):
        if not os.path.exists(SAVE_FILE): self.setup_new_game(); return
        try:
            with open(SAVE_FILE,'r',encoding='utf-8') as f: data=json.load(f)
            def parse_players(lst):
                res=[]
                for p in lst:
                    det=p.get("detailed")
                    res.append(Player(p["name"],p["position"],p.get("age",25),0,0,0,0,0,
                                      p.get("price",50),p.get("stamina",100),
                                      p.get("injured_days",0),p.get("instruction","기본"),
                                      loaded_stats=det))
                return res
            td=data["my_team"]
            self.my_team=Team(td["name"],td.get("budget",150),
                              parse_players(td.get("starters",[])),
                              parse_players(td.get("subs",[])))
            for attr,default in [("formation","4-3-3"),("mentality",50),("pass_dir",50),
                                   ("tempo",50),("width",50),("press",50),("d_line",50),
                                   ("wins",0),("draws",0),("losses",0)]:
                setattr(self.my_team,attr,td.get(attr,default))
            if "game_date" in data: self.game_date=GameDate.from_dict(data["game_date"])
            self.schedule_idx=data.get("schedule_idx",0)
            if data.get("league"):      self.league=League.from_dict(data["league"])
            else:                        self.league=League(self.my_team.name)
            if data.get("fa_cup"):      self.fa_cup=KnockoutCup.from_dict(data["fa_cup"])
            else:                        self.fa_cup=KnockoutCup("FA컵",FA_CUP_TEAMS,self.my_team.name)
            if data.get("league_cup"):  self.league_cup=KnockoutCup.from_dict(data["league_cup"])
            else:                        self.league_cup=KnockoutCup("리그컵",LEAGUE_CUP_TEAMS,self.my_team.name)
            if data.get("ucl"):         self.ucl=UCL.from_dict(data["ucl"])
            else:                        self.ucl=UCL(self.my_team.name)
            owned={p.name for p in self.my_team.all_players()}
            self.transfer_pool=[p for p in self.transfer_pool if p.name not in owned]
            self._notify_date()
            nxt=self.peek_next_match()
            self.log(f"데이터 로드 완료.  ▶ 다음 예정 경기: {nxt if nxt else '시즌 종료'}")
        except Exception as e:
            self.log(f"로드 실패({e}), 새 게임 시작.")
            self.setup_new_game()

# ══════════════════════════════════════════════════════════════════════════════
# 6. GUI
# ══════════════════════════════════════════════════════════════════════════════
class TacticWindow(tk.Toplevel):
    def __init__(self,parent,engine):
        super().__init__(parent); self.engine=engine
        self.title("전술 보드 (1~100)"); self.geometry("500x600"); self.configure(bg="#0d1117"); self._build()
    def _slider(self,parent,label,attr,lo,hi):
        f=tk.Frame(parent,bg="#0d1117"); f.pack(fill=tk.X,pady=8,padx=15)
        tk.Label(f,text=label,bg="#0d1117",fg="#58a6ff",font=("Consolas",10,"bold")).pack(anchor="w")
        var=tk.IntVar(value=getattr(self.engine.my_team,attr))
        tk.Scale(f,from_=1,to=100,orient=tk.HORIZONTAL,variable=var,
                 bg="#0d1117",fg="white",highlightthickness=0,
                 troughcolor="#21262d",activebackground="#1f6feb").pack(fill=tk.X)
        df=tk.Frame(f,bg="#0d1117"); df.pack(fill=tk.X)
        tk.Label(df,text=lo,bg="#0d1117",fg="#8b949e",font=("Consolas",8)).pack(side=tk.LEFT)
        tk.Label(df,text=hi,bg="#0d1117",fg="#8b949e",font=("Consolas",8)).pack(side=tk.RIGHT)
        return var
    def _build(self):
        tk.Label(self,text="팀 세부 전술 (1~100)",font=("Consolas",13,"bold"),
                 bg="#0d1117",fg="#f0c040").pack(pady=10)
        f0=tk.Frame(self,bg="#0d1117"); f0.pack(fill=tk.X,pady=8,padx=15)
        tk.Label(f0,text="포메이션:",bg="#0d1117",fg="#c9d1d9",font=("Consolas",10)).pack(side=tk.LEFT)
        self.v_form=tk.StringVar(value=self.engine.my_team.formation)
        tk.Entry(f0,textvariable=self.v_form,bg="#21262d",fg="white",font=("Consolas",10),width=12).pack(side=tk.LEFT,padx=8)
        self.v_mentality=self._slider(self,"팀 성향 (Mentality)","mentality","텐백 우주방어","초공격적")
        self.v_pass_dir=self._slider(self,"패스 방향 (Pass Directness)","pass_dir","티키타카","다이렉트 롱볼")
        self.v_tempo=self._slider(self,"템포 (Tempo)","tempo","느리게","게겐프레싱")
        self.v_width=self._slider(self,"공격 폭 (Width)","width","중앙 밀집","터치라인")
        self.v_press=self._slider(self,"압박 (Pressing)","press","내려앉기","전방위 압박")
        self.v_dline=self._slider(self,"수비 라인 높이 (D-Line)","d_line","자기 골대","하프라인")
        tk.Button(self,text="저장 적용",width=18,bg="#1f6feb",fg="white",
                  font=("Consolas",10,"bold"),command=self._apply).pack(pady=12)
    def _apply(self):
        t=self.engine.my_team; t.formation=self.v_form.get()
        t.mentality=self.v_mentality.get(); t.pass_dir=self.v_pass_dir.get()
        t.tempo=self.v_tempo.get(); t.width=self.v_width.get()
        t.press=self.v_press.get(); t.d_line=self.v_dline.get()
        messagebox.showinfo("전술 적용",f"포메이션 [{t.formation}] 전술이 적용되었습니다.",parent=self)

class InstructionWindow(tk.Toplevel):
    def __init__(self,parent,engine):
        super().__init__(parent); self.engine=engine
        self.title("개인 지침"); self.geometry("740x500"); self.configure(bg="#0d1117"); self._build()
    def _build(self):
        cols=("구분","번호","이름","포지션","현재 지침")
        self.tree=ttk.Treeview(self,columns=cols,show="headings",height=18)
        for c in cols: self.tree.heading(c,text=c); self.tree.column(c,width=80,anchor="center")
        self.tree.column("이름",width=140,anchor="w"); self.tree.column("현재 지침",width=120)
        self.tree.pack(side=tk.LEFT,fill=tk.BOTH,expand=True,padx=(10,0),pady=6)
        right=tk.Frame(self,bg="#0d1117",width=160); right.pack(side=tk.LEFT,fill=tk.Y,padx=10,pady=6)
        self.v_i=tk.StringVar(value="기본")
        for ins in INSTRUCTIONS:
            tk.Radiobutton(right,text=ins,variable=self.v_i,value=ins,
                           bg="#0d1117",fg="#c9d1d9",selectcolor="#1f6feb",
                           font=("Consolas",9),anchor="w",width=14).pack(pady=1)
        tk.Button(right,text="적용",bg="#1f6feb",fg="white",width=12,command=self._apply).pack(pady=10)
        self._refresh()
    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i,p in enumerate(self.engine.my_team.starters):
            self.tree.insert("","end",iid=f"s{i}",values=("선발",i+1,p.name,p.position,p.instruction))
        for i,p in enumerate(self.engine.my_team.subs):
            self.tree.insert("","end",iid=f"b{i}",values=("후보",i+1,p.name,p.position,p.instruction))
    def _apply(self):
        sel=self.tree.selection()
        if not sel: return
        iid=sel[0]; self.engine.set_player_instruction(iid.startswith("s"),int(iid[1:]),self.v_i.get()); self._refresh()

class TransferWindow(tk.Toplevel):
    def __init__(self,parent,engine):
        super().__init__(parent); self.engine=engine
        self.title("이적 시장"); self.geometry("940x610"); self.configure(bg="#0d1117")
        self._build(); self._refresh()
    def _build(self):
        top=tk.Frame(self,bg="#0d1117"); top.pack(fill=tk.X,padx=10,pady=6)
        self.lbl_b=tk.Label(top,text="",font=("Consolas",10),bg="#0d1117",fg="#f0c040"); self.lbl_b.pack(side=tk.RIGHT)
        self.lbl_w=tk.Label(top,text="",font=("Consolas",9),bg="#0d1117",fg="#aaa"); self.lbl_w.pack(side=tk.RIGHT,padx=10)
        nb=ttk.Notebook(self); nb.pack(fill=tk.BOTH,expand=True,padx=10,pady=4)
        bf=tk.Frame(nb,bg="#0d1117"); nb.add(bf,text="영입")
        ff=tk.Frame(bf,bg="#0d1117"); ff.pack(fill=tk.X,padx=6,pady=4)
        tk.Label(ff,text="포지션:",bg="#0d1117",fg="#c9d1d9",font=("Consolas",9)).pack(side=tk.LEFT,padx=4)
        self.v_f=tk.StringVar(value="전체")
        for pos in ["전체","GK","CB","FB","CDM","CM","CAM","LW","RW","ST"]:
            tk.Radiobutton(ff,text=pos,variable=self.v_f,value=pos,command=self._refresh,
                           bg="#0d1117",fg="#c9d1d9",selectcolor="#1f6feb",font=("Consolas",8)).pack(side=tk.LEFT,padx=2)
        cols=("번호","이름","나이","포지션","OVR","속력","골결","시야","태클","몸값")
        self.bt=ttk.Treeview(bf,columns=cols,show="headings",height=16)
        for c in cols: self.bt.heading(c,text=c); self.bt.column(c,width=65,anchor="center")
        self.bt.column("이름",width=145,anchor="w")
        sb=ttk.Scrollbar(bf,orient=tk.VERTICAL,command=self.bt.yview); self.bt.configure(yscrollcommand=sb.set)
        self.bt.pack(side=tk.LEFT,fill=tk.BOTH,expand=True); sb.pack(side=tk.RIGHT,fill=tk.Y)
        bbf=tk.Frame(self,bg="#0d1117"); bbf.pack(pady=4)
        tk.Button(bbf,text="선발로 영입",width=14,bg="#1f6feb",fg="white",command=lambda:self._buy(True)).pack(side=tk.LEFT,padx=6)
        tk.Button(bbf,text="후보로 영입",width=14,bg="#238636",fg="white",command=lambda:self._buy(False)).pack(side=tk.LEFT,padx=6)
        tk.Button(bbf,text="새로고침",width=10,command=self._refresh).pack(side=tk.LEFT,padx=6)
        sf=tk.Frame(nb,bg="#0d1117"); nb.add(sf,text="방출")
        cols2=("구분","번호","이름","포지션","OVR","체력","예상료")
        self.st=ttk.Treeview(sf,columns=cols2,show="headings",height=16)
        for c in cols2: self.st.heading(c,text=c); self.st.column(c,width=90,anchor="center")
        self.st.column("이름",width=150,anchor="w")
        sb2=ttk.Scrollbar(sf,orient=tk.VERTICAL,command=self.st.yview); self.st.configure(yscrollcommand=sb2.set)
        self.st.pack(side=tk.LEFT,fill=tk.BOTH,expand=True); sb2.pack(side=tk.RIGHT,fill=tk.Y)
        sff=tk.Frame(self,bg="#0d1117"); sff.pack(pady=4)
        tk.Button(sff,text="선수 매각",width=16,bg="#da3633",fg="white",command=self._sell).pack()
    def _refresh(self):
        eng=self.engine; is_open=eng.game_date.is_transfer_window()
        self.lbl_b.config(text=f"예산: {eng.my_team.budget}M")
        self.lbl_w.config(text=f"이적시장 {'열림 ✅' if is_open else '닫힘 ❌'}  ({eng.game_date})",
                          fg="#3fb950" if is_open else "#f85149")
        pf=self.v_f.get(); self.bt.delete(*self.bt.get_children())
        di=0
        for i,p in enumerate(eng.transfer_pool):
            if pf!="전체" and p.position!=pf: continue
            di+=1; self.bt.insert("","end",iid=str(i),values=(di,p.name,p.age,p.position,p.rating,p.spd,p.fin,p.vis,p.tak,p.price))
        self.st.delete(*self.st.get_children())
        for i,p in enumerate(eng.my_team.starters):
            self.st.insert("","end",iid=f"s{i}",values=("선발",i+1,p.name,p.position,p.rating,p.stamina,f"{int(p.price*0.75)}M"))
        for i,p in enumerate(eng.my_team.subs):
            self.st.insert("","end",iid=f"b{i}",values=("후보",i+1,p.name,p.position,p.rating,p.stamina,f"{int(p.price*0.75)}M"))
    def _buy(self,to_starter):
        sel=self.bt.selection()
        if not sel: messagebox.showinfo("알림","선수를 선택하라.",parent=self); return
        self.engine.transfer_buy(int(sel[0]),to_starter); self._refresh()
    def _sell(self):
        sel=self.st.selection()
        if not sel: messagebox.showinfo("알림","선수를 선택하라.",parent=self); return
        iid=sel[0]; name=self.st.item(iid)["values"][2]
        if not messagebox.askyesno("방출",f"{name}을(를) 방출?",parent=self): return
        self.engine.transfer_sell(iid.startswith("s"),int(iid[1:])); self._refresh()

class FM_GUI:
    def __init__(self,root):
        self.root=root; self.root.title("FM 2026 PRO")
        self.root.geometry("900x740"); self.root.configure(bg="#0d1117")

        # 상단 바
        bar=tk.Frame(self.root,bg="#161b22",pady=5); bar.pack(fill=tk.X)
        tk.Label(bar,text="⚽ FM 2026 PRO",font=("Consolas",11,"bold"),
                 bg="#161b22",fg="#58a6ff").pack(side=tk.LEFT,padx=12)
        self.lbl_date=tk.Label(bar,text="",font=("Consolas",10),
                                bg="#161b22",fg="#f0c040"); self.lbl_date.pack(side=tk.RIGHT,padx=12)

        # 다음 경기 예고 배너
        self.lbl_next=tk.Label(self.root,text="",font=("Consolas",10,"bold"),
                                bg="#161b22",fg="#3fb950",pady=4)
        self.lbl_next.pack(fill=tk.X,padx=0)

        # 로그창
        self.text_area=scrolledtext.ScrolledText(self.root,wrap=tk.WORD,width=120,height=28,
                                                 font=("Consolas",9),bg="#0d1117",fg="#c9d1d9")
        self.text_area.pack(pady=4,padx=10,fill=tk.BOTH,expand=True)

        # 행 1 — 관리 버튼
        f1=tk.Frame(self.root,bg="#0d1117"); f1.pack(pady=2)
        for txt,cmd in [
            ("스쿼드",    lambda:self.engine.show_squad_detailed()),
            ("전술 설정", lambda:TacticWindow(self.root,self.engine)),
            ("개인 지침", lambda:InstructionWindow(self.root,self.engine)),
            ("선수 교체", self.cmd_sub),
            ("이적 시장", lambda:TransferWindow(self.root,self.engine)),
            ("순위표",    lambda:self.engine.show_standings()),
        ]:
            tk.Button(f1,text=txt,command=cmd,bg="#21262d",fg="#c9d1d9",
                      font=("Consolas",9),padx=6,pady=3).pack(side=tk.LEFT,padx=3)

        # 행 2 — 다음 경기 (메인 버튼)
        f2=tk.Frame(self.root,bg="#0d1117"); f2.pack(pady=5)
        tk.Button(f2,text="▶  다음 경기 진행",
                  command=self.cmd_next_match,
                  bg="#1f6feb",fg="white",
                  font=("Consolas",12,"bold"),
                  padx=20,pady=6,relief=tk.FLAT).pack(side=tk.LEFT,padx=8)
        tk.Button(f2,text="다음 경기 확인",
                  command=self.cmd_peek,
                  bg="#21262d",fg="#c9d1d9",
                  font=("Consolas",9),
                  padx=8,pady=6).pack(side=tk.LEFT,padx=4)

        # 행 3 — 기타
        f3=tk.Frame(self.root,bg="#0d1117"); f3.pack(pady=2)
        tk.Button(f3,text="게임 저장",command=lambda:self.engine.save_game(),
                  width=12,bg="#238636",fg="white",font=("Consolas",9)).pack(side=tk.LEFT,padx=4)
        tk.Button(f3,text="종료",command=self.root.quit,
                  width=10,bg="#da3633",fg="white",font=("Consolas",9)).pack(side=tk.LEFT,padx=4)

        self.engine=SimulatorEngine(self.root,self.write_log,self.update_date)
        self.engine.load_game()
        self._update_next_banner()

    def update_date(self,s):
        self.lbl_date.config(text=f"📅 {s}")
        self._update_next_banner()

    def _update_next_banner(self):
        nxt=self.engine.peek_next_match() if self.engine.my_team else None
        if nxt:
            self.lbl_next.config(text=f"  ▶ 다음 예정 경기:  {nxt}")
        else:
            self.lbl_next.config(text="  🏁 이번 시즌 일정 완료")

    def write_log(self,t):
        self.text_area.insert(tk.END,t+"\n"); self.text_area.see(tk.END)

    def cmd_next_match(self):
        self.engine.next_match()
        self._update_next_banner()

    def cmd_peek(self):
        nxt=self.engine.peek_next_match()
        if nxt:
            self.write_log(f"\n  ▶ 다음 예정 경기: {nxt}")
        else:
            self.write_log("\n  🏁 이번 시즌 모든 일정이 완료되었다.")

    def cmd_sub(self):
        si=simpledialog.askinteger("OUT","뺄 선발 번호 (1~11):",parent=self.root)
        if si:
            bi=simpledialog.askinteger("IN","투입할 후보 번호:",parent=self.root)
            if bi: self.engine.substitute_player(si-1,bi-1)

if __name__=="__main__":
    if not is_admin():
        try: ctypes.windll.shell32.ShellExecuteW(None,"runas",sys.executable," ".join(sys.argv),None,1)
        except: pass
        sys.exit()
    root=tk.Tk()
    FM_GUI(root)
    root.mainloop()
