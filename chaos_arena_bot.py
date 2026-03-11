#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║              🎪 CHAOS ARENA - 10 PLAYFUL GROUP GAMES 🎪          ║
║                  All games + Leaderboard in ONE file             ║
╚══════════════════════════════════════════════════════════════════╝
Games included:
  1. 🐸 Chaos King         - Vote who caused most chaos
  2. 💀 Roast Battle Arena - Submit & vote on roasts
  3. 🎯 Daily Dare Club    - Complete dares, earn points
  4. 🦆 Duck Hunt Social   - Find the hidden duck fastest
  5. 🧠 Dumb Questions     - Who asks the dumbest question
  6. 🎪 Spin & Win Chaos   - Random daily challenge + points
  7. 😴 Excuse Olympics    - Best excuse, crowd votes winner
  8. 🌶️ Hot Takes Stadium  - Spicy opinions, group votes
  9. 🤡 Clown of the Week  - Daily silly votes, weekly crown
 10. 🎵 Worst Singer       - Submit voice notes, vote unhinged

Run: python chaos_arena.py
"""

import random
import time
import os
import json
import datetime

# ─────────────────────────────────────────────
#  COLORS & STYLES (ANSI)
# ─────────────────────────────────────────────
R  = "\033[91m"   # Red
G  = "\033[92m"   # Green
Y  = "\033[93m"   # Yellow
B  = "\033[94m"   # Blue
M  = "\033[95m"   # Magenta
C  = "\033[96m"   # Cyan
W  = "\033[97m"   # White
BLD= "\033[1m"    # Bold
DIM= "\033[2m"    # Dim
RST= "\033[0m"    # Reset
BG = "\033[45m"   # BG Magenta

def clr(): os.system("cls" if os.name == "nt" else "clear")

def banner(text, color=M):
    w = 60
    print(f"\n{color}{BLD}{'═'*w}{RST}")
    print(f"{color}{BLD}{text.center(w)}{RST}")
    print(f"{color}{BLD}{'═'*w}{RST}\n")

def box(text, color=C):
    lines = text.split("\n")
    w = max(len(l) for l in lines) + 4
    print(f"{color}┌{'─'*(w-2)}┐{RST}")
    for l in lines:
        print(f"{color}│ {l.ljust(w-4)} │{RST}")
    print(f"{color}└{'─'*(w-2)}┘{RST}")

def slow_print(text, delay=0.03):
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()

def input_prompt(msg):
    return input(f"{Y}{BLD}  ▶ {msg}: {RST}").strip()

def press_enter():
    input(f"\n{DIM}  [Press ENTER to continue...]{RST}")

def divider(color=DIM):
    print(f"{color}{'─'*60}{RST}")

# ─────────────────────────────────────────────
#  DATA STORE  (in-memory JSON-backed)
# ─────────────────────────────────────────────
DATA_FILE = "chaos_arena_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {
        "players": {},        # name -> {points, titles, crowns, streak, last_play}
        "roasts": [],         # {author, text, votes}
        "dares": [],          # {player, dare, completed, votes}
        "excuses": [],        # {author, excuse, votes}
        "hot_takes": [],      # {author, take, agree, disagree}
        "clown_votes": {},    # name -> count today
        "chaos_votes": {},    # name -> count today
        "dumb_qs": [],        # {author, question, votes}
        "singers": [],        # {author, description, votes}
        "spin_log": [],       # {player, challenge, done}
        "duck_scores": [],    # {player, time_sec}
        "history": []         # log of events
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def ensure_player(data, name):
    if name not in data["players"]:
        data["players"][name] = {
            "points": 0,
            "titles": [],
            "crowns": 0,
            "streak": 0,
            "last_play": ""
        }
    return data["players"][name]

def add_points(data, name, pts, reason=""):
    p = ensure_player(data, name)
    p["points"] += pts
    today = str(datetime.date.today())
    if p["last_play"] != today:
        p["streak"] += 1
        p["last_play"] = today
    if reason:
        data["history"].append(f"{today} | {name} +{pts}pts | {reason}")
    save_data(data)
    print(f"\n  {G}{BLD}+{pts} points added to {name}! 🎉{RST}")

def get_players(data):
    return list(data["players"].keys())

def pick_player(data, prompt="Choose a player"):
    players = get_players(data)
    if not players:
        print(f"  {R}No players registered yet! Add players first.{RST}")
        return None
    print(f"\n{C}  Players:{RST}")
    for i, p in enumerate(players, 1):
        pts = data["players"][p]["points"]
        print(f"  {Y}{i}.{RST} {p} {DIM}({pts} pts){RST}")
    try:
        idx = int(input_prompt(prompt + " (number)")) - 1
        if 0 <= idx < len(players):
            return players[idx]
    except:
        pass
    print(f"  {R}Invalid choice.{RST}")
    return None

def multi_vote(options, label="option"):
    """Simple voting: each person enters their pick"""
    votes = {}
    print(f"\n  {C}How many voters?{RST}")
    try:
        n = int(input_prompt("Number of voters"))
    except:
        n = 1
    for i in range(n):
        print(f"\n  {Y}Voter {i+1}:{RST}")
        for j, o in enumerate(options, 1):
            print(f"    {j}. {o}")
        try:
            pick = int(input_prompt(f"Vote for {label} (number)")) - 1
            if 0 <= pick < len(options):
                votes[options[pick]] = votes.get(options[pick], 0) + 1
        except:
            pass
    return votes

# ─────────────────────────────────────────────
#  LEADERBOARD
# ─────────────────────────────────────────────
def show_leaderboard(data):
    clr()
    banner("🏆  CHAOS ARENA LEADERBOARD  🏆", Y)
    players = data["players"]
    if not players:
        print(f"  {R}No players yet! Register in any game.{RST}")
        press_enter()
        return
    sorted_p = sorted(players.items(), key=lambda x: x[1]["points"], reverse=True)
    medals = ["🥇","🥈","🥉"] + ["🎖️"]*(len(sorted_p)-3)
    print(f"  {BLD}{'Rank':<6}{'Player':<20}{'Points':>8}{'Crowns':>8}{'Streak':>8}  Titles{RST}")
    divider(Y)
    for i, (name, info) in enumerate(sorted_p):
        medal = medals[i] if i < len(medals) else "  "
        titles = ", ".join(info["titles"][-2:]) if info["titles"] else "—"
        streak = f"🔥{info['streak']}" if info["streak"] > 1 else str(info["streak"])
        print(f"  {medal} {str(i+1)+'.':<4}{name:<20}{info['points']:>8}{info['crowns']:>8}{streak:>8}  {DIM}{titles}{RST}")
    divider(Y)
    if sorted_p:
        leader = sorted_p[0][0]
        print(f"\n  {BG}{BLD}  👑 CURRENT CHAOS KING: {leader.upper()}  {RST}")

    if data["history"]:
        print(f"\n  {C}{BLD}Recent Events:{RST}")
        for h in data["history"][-5:]:
            print(f"  {DIM}• {h}{RST}")
    press_enter()

# ─────────────────────────────────────────────
#  GAME 1: 🐸 CHAOS KING
# ─────────────────────────────────────────────
def game_chaos_king(data):
    clr()
    banner("🐸  CHAOS KING  🐸", G)
    box("Vote for who caused the most CHAOS today!\nWinner gets the 👑 Chaos Crown + 50 pts")
    players = get_players(data)
    if len(players) < 2:
        print(f"  {R}Need at least 2 players! Register more.{RST}")
        press_enter()
        return
    print(f"\n  {C}Voting begins! Each person casts their vote.{RST}")
    votes = multi_vote(players, "chaos king")
    if not votes:
        press_enter()
        return
    winner = max(votes, key=votes.get)
    clr()
    banner(f"👑 CHAOS KING: {winner.upper()} 👑", Y)
    slow_print(f"  {Y}With {votes[winner]} vote(s), {winner} is today's CHAOS KING! 🎉{RST}")
    add_points(data, winner, 50, "Chaos King crown")
    data["players"][winner]["crowns"] = data["players"][winner].get("crowns", 0) + 1
    if "👑 Chaos King" not in data["players"][winner]["titles"]:
        data["players"][winner]["titles"].append("👑 Chaos King")
    data["chaos_votes"] = votes
    save_data(data)
    print(f"\n  {DIM}Vote tally:{RST}")
    for p, v in sorted(votes.items(), key=lambda x: -x[1]):
        bar = "█" * v
        print(f"  {p:<20} {G}{bar}{RST} {v}")
    press_enter()

# ─────────────────────────────────────────────
#  GAME 2: 💀 ROAST BATTLE ARENA
# ─────────────────────────────────────────────
def game_roast_battle(data):
    clr()
    banner("💀  ROAST BATTLE ARENA  💀", R)
    box("Submit your best (kind) roast!\nGroup votes → top roaster wins 40 pts")
    print(f"\n  {C}Options:{RST}")
    print(f"  {Y}1.{RST} Submit a roast")
    print(f"  {Y}2.{RST} Vote on roasts")
    print(f"  {Y}3.{RST} See all roasts")
    choice = input_prompt("Pick option")
    if choice == "1":
        author = input_prompt("Your name")
        ensure_player(data, author)
        target = input_prompt("Who are you roasting")
        roast = input_prompt(f"Your roast of {target}")
        data["roasts"].append({"author": author, "target": target, "text": roast, "votes": 0})
        save_data(data)
        print(f"\n  {G}Roast submitted! 🔥{RST}")
        slow_print(f'  "{roast}"')
    elif choice == "2":
        if not data["roasts"]:
            print(f"  {R}No roasts yet!{RST}")
        else:
            print(f"\n  {C}Current Roasts:{RST}")
            for i, r in enumerate(data["roasts"], 1):
                print(f"  {Y}{i}.{RST} [{r['author']} → {r['target']}]: {r['text']}")
            try:
                idx = int(input_prompt("Vote for roast number")) - 1
                if 0 <= idx < len(data["roasts"]):
                    data["roasts"][idx]["votes"] += 1
                    author = data["roasts"][idx]["author"]
                    add_points(data, author, 10, "Roast vote received")
                    save_data(data)
                    print(f"  {G}Vote counted! 🗳️{RST}")
                    best = max(data["roasts"], key=lambda x: x["votes"])
                    print(f"\n  {Y}🏆 Current top roaster: {best['author']} ({best['votes']} votes){RST}")
            except:
                print(f"  {R}Invalid.{RST}")
    elif choice == "3":
        if not data["roasts"]:
            print(f"  {R}No roasts yet!{RST}")
        else:
            sorted_r = sorted(data["roasts"], key=lambda x: -x["votes"])
            for i, r in enumerate(sorted_r, 1):
                medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "  "
                print(f"\n  {medal} {Y}{r['author']}{RST} → {r['target']}")
                print(f"     {DIM}\"{r['text']}\"{RST}")
                print(f"     {G}❤️  {r['votes']} votes{RST}")
    press_enter()

# ─────────────────────────────────────────────
#  GAME 3: 🎯 DAILY DARE CLUB
# ─────────────────────────────────────────────
DARE_LIST = [
    "Do your best robot dance for 10 seconds 🤖",
    "Text someone 'I know what you did' with no context 😈",
    "Speak only in questions for the next 5 minutes ❓",
    "Send a voice note saying 'moo' to someone 🐄",
    "Do 10 jumping jacks right now 💪",
    "Change your profile pic to a potato for 1 hour 🥔",
    "Say everything in slow motion for 2 minutes 🐢",
    "Narrate your life in a dramatic movie trailer voice 🎬",
    "Post a selfie with the most unhinged caption 📸",
    "Call someone and only speak in emojis 🗣️",
    "Pretend to be a news anchor for 30 seconds 📺",
    "Walk like a penguin for the next minute 🐧",
]

def game_dare_club(data):
    clr()
    banner("🎯  DAILY DARE CLUB  🎯", B)
    box("Get a random dare! Complete it for 30 pts.\nGroup verifies = bonus 20 pts!")
    print(f"\n  {C}Options:{RST}")
    print(f"  {Y}1.{RST} Get my daily dare")
    print(f"  {Y}2.{RST} Mark dare as completed")
    print(f"  {Y}3.{RST} See dare leaderboard")
    choice = input_prompt("Pick option")
    if choice == "1":
        name = input_prompt("Your name")
        ensure_player(data, name)
        dare = random.choice(DARE_LIST)
        data["dares"].append({"player": name, "dare": dare, "completed": False, "votes": 0})
        save_data(data)
        print(f"\n  {Y}{BLD}🎯 YOUR DARE:{RST}")
        slow_print(f"\n  {W}{dare}{RST}", 0.04)
        print(f"\n  {DIM}Come back after completing it to claim your points!{RST}")
    elif choice == "2":
        my_dares = [(i, d) for i, d in enumerate(data["dares"]) if not d["completed"]]
        if not my_dares:
            print(f"  {R}No pending dares!{RST}")
        else:
            for i, (idx, d) in enumerate(my_dares, 1):
                print(f"  {Y}{i}.{RST} {d['player']}: {d['dare']}")
            try:
                pick = int(input_prompt("Which dare completed (number)")) - 1
                if 0 <= pick < len(my_dares):
                    real_idx = my_dares[pick][0]
                    data["dares"][real_idx]["completed"] = True
                    player = data["dares"][real_idx]["player"]
                    add_points(data, player, 30, "Dare completed")
                    save_data(data)
                    print(f"\n  {G}💪 Dare complete! 30 pts awarded to {player}!{RST}")
                    verify = input_prompt("Did the group verify? (y/n)")
                    if verify.lower() == "y":
                        add_points(data, player, 20, "Dare verified by group")
            except:
                print(f"  {R}Invalid.{RST}")
    elif choice == "3":
        completed = [d for d in data["dares"] if d["completed"]]
        counts = {}
        for d in completed:
            counts[d["player"]] = counts.get(d["player"], 0) + 1
        if not counts:
            print(f"  {R}Nobody completed a dare yet!{RST}")
        else:
            print(f"\n  {C}{BLD}Dare Champions:{RST}")
            for p, c in sorted(counts.items(), key=lambda x: -x[1]):
                bar = "🎯" * c
                print(f"  {Y}{p:<20}{RST} {bar} {c} dares")
    press_enter()

# ─────────────────────────────────────────────
#  GAME 4: 🦆 DUCK HUNT SOCIAL
# ─────────────────────────────────────────────
def game_duck_hunt(data):
    clr()
    banner("🦆  DUCK HUNT SOCIAL  🦆", Y)
    box("Find the hidden duck in the grid!\nFastest finder gets 60 pts!")
    name = input_prompt("Your name")
    ensure_player(data, name)
    size = 8
    grid = [["🌊" for _ in range(size)] for _ in range(size)]
    dr, dc = random.randint(0,size-1), random.randint(0,size-1)
    decoys = [(random.randint(0,size-1), random.randint(0,size-1)) for _ in range(5)]
    fakes = ["🐟","🐠","🦑","🐙","🦞"]
    for i,(fr,fc) in enumerate(decoys):
        if (fr,fc) != (dr,dc):
            grid[fr][fc] = fakes[i % len(fakes)]
    hint_row = "ABCDEFGH"
    def print_grid(reveal=False):
        print(f"\n     " + "  ".join(str(i+1) for i in range(size)))
        for r in range(size):
            row_str = f"  {hint_row[r]}  "
            for c in range(size):
                if reveal and r==dr and c==dc:
                    row_str += "🦆  "
                else:
                    row_str += grid[r][c] + "  "
            print(row_str)
    print(f"\n  {C}The 🦆 duck is hiding somewhere in the grid!{RST}")
    print(f"  {DIM}Watch out for decoy fish — only ONE is the duck!{RST}")
    print_grid()
    start = time.time()
    attempts = 0
    found = False
    while not found:
        print(f"\n  {Y}Guess (e.g. B4) or 'hint' or 'quit':{RST}")
        guess = input_prompt("Your guess").upper().strip()
        if guess == "QUIT":
            break
        if guess == "HINT":
            hints = ["It's in the top half 🔼" if dr < 4 else "It's in the bottom half 🔽",
                     "It's on the left side ◀️" if dc < 4 else "It's on the right side ▶️"]
            print(f"  {C}Hint: {random.choice(hints)}{RST}")
            continue
        if len(guess) >= 2 and guess[0] in hint_row and guess[1:].isdigit():
            r = hint_row.index(guess[0])
            c = int(guess[1:]) - 1
            attempts += 1
            if r == dr and c == dc:
                elapsed = round(time.time() - start, 2)
                found = True
                clr()
                banner(f"🦆 FOUND IT! {name} wins! 🦆", G)
                print_grid(reveal=True)
                slow_print(f"\n  ⏱️  Time: {elapsed}s in {attempts} attempts!", 0.04)
                pts = max(60 - attempts*5, 10)
                add_points(data, name, pts, f"Duck found in {elapsed}s")
                data["duck_scores"].append({"player": name, "time": elapsed, "attempts": attempts})
                save_data(data)
                best = min(data["duck_scores"], key=lambda x: x["time"])
                print(f"\n  {Y}🏆 Best time ever: {best['player']} in {best['time']}s{RST}")
            else:
                cell = grid[r][c]
                if cell != "🌊":
                    print(f"  {R}That's a {cell} decoy! Try again. ({attempts} attempts){RST}")
                else:
                    dist = abs(r-dr) + abs(c-dc)
                    temp = "🔥 HOT!" if dist <= 2 else "🌡️ Warm" if dist <= 4 else "🧊 Cold"
                    print(f"  {C}{temp} — {attempts} attempts{RST}")
        else:
            print(f"  {R}Invalid format. Use like: B4{RST}")
    if not found:
        print_grid(reveal=True)
        print(f"  {DIM}The duck was at {hint_row[dr]}{dc+1}!{RST}")
    press_enter()

# ─────────────────────────────────────────────
#  GAME 5: 🧠 DUMB QUESTIONS BATTLE
# ─────────────────────────────────────────────
SAMPLE_DUMB_QS = [
    "If I eat myself, would I become twice as big or disappear completely?",
    "Why does the sun go to sleep when I need a tan?",
    "If water is wet, is a fish always drowning?",
    "Do blind people see their dreams?",
    "Can you cry underwater?",
    "Why is there a 'd' in 'fridge' but not in 'refrigerator'?",
    "If you drop soap on the floor, is the floor clean or is soap dirty?",
]

def game_dumb_questions(data):
    clr()
    banner("🧠  DUMB QUESTIONS BATTLE  🧠", M)
    box("Submit the dumbest question you can think of!\nMost votes = 35 pts + 🤪 title")
    print(f"\n  {C}Options:{RST}")
    print(f"  {Y}1.{RST} Submit my dumb question")
    print(f"  {Y}2.{RST} Vote on questions")
    print(f"  {Y}3.{RST} See all questions")
    print(f"  {Y}4.{RST} Get a sample dumb question (inspiration)")
    choice = input_prompt("Pick option")
    if choice == "1":
        author = input_prompt("Your name")
        ensure_player(data, author)
        q = input_prompt("Your dumb question")
        data["dumb_qs"].append({"author": author, "question": q, "votes": 0})
        save_data(data)
        print(f"\n  {G}Question submitted! 🤪{RST}")
        slow_print(f'  "{q}"', 0.04)
    elif choice == "2":
        if not data["dumb_qs"]:
            print(f"  {R}No questions yet!{RST}")
        else:
            print(f"\n  {C}Vote for the DUMBEST question:{RST}")
            for i, q in enumerate(data["dumb_qs"], 1):
                print(f"  {Y}{i}.{RST} [{q['author']}]: {q['question']} {DIM}({q['votes']} votes){RST}")
            try:
                idx = int(input_prompt("Vote number")) - 1
                if 0 <= idx < len(data["dumb_qs"]):
                    data["dumb_qs"][idx]["votes"] += 1
                    author = data["dumb_qs"][idx]["author"]
                    add_points(data, author, 10, "Dumb Q vote")
                    save_data(data)
                    print(f"  {G}Voted! 🗳️{RST}")
                    best = max(data["dumb_qs"], key=lambda x: x["votes"])
                    if best["votes"] >= 3 and "🤪 Question Master" not in data["players"][best["author"]]["titles"]:
                        data["players"][best["author"]]["titles"].append("🤪 Question Master")
                        save_data(data)
                        print(f"  {Y}🏆 {best['author']} earned the '🤪 Question Master' title!{RST}")
            except:
                print(f"  {R}Invalid.{RST}")
    elif choice == "3":
        all_q = sorted(data["dumb_qs"], key=lambda x: -x["votes"])
        if not all_q:
            print(f"  {R}No questions yet!{RST}")
        else:
            for i, q in enumerate(all_q, 1):
                print(f"\n  {Y}{i}. {q['author']}{RST}: {q['question']}")
                print(f"     {G}👍 {q['votes']} votes{RST}")
    elif choice == "4":
        print(f"\n  {C}Sample dumb question for inspiration:{RST}")
        slow_print(f"\n  {W}{random.choice(SAMPLE_DUMB_QS)}{RST}", 0.04)
    press_enter()

# ─────────────────────────────────────────────
#  GAME 6: 🎪 SPIN & WIN CHAOS
# ─────────────────────────────────────────────
CHALLENGES = [
    ("🤸 Do 5 cartwheels (real or imaginary)", 20),
    ("📸 Post the most unhinged selfie right now", 25),
    ("🎤 Sing the first song that comes to mind", 30),
    ("🧘 Hold a plank for 30 seconds", 25),
    ("📞 Call someone and say 'I need to confess something' then say nothing", 40),
    ("🥶 Drink a glass of cold water in one go", 15),
    ("🎭 Do a 1-minute stand-up comedy routine", 35),
    ("🐔 Walk like a chicken for 1 full minute", 20),
    ("📝 Write a haiku about your left shoe", 25),
    ("🤝 Shake hands with an imaginary president", 15),
    ("🌮 Describe tacos as if you've never seen food before", 30),
    ("🎪 Invent a new dance move and name it", 35),
    ("👻 Tell a 'scary' story about office supplies", 30),
    ("🦁 Roar like a lion, then immediately meow like a cat", 20),
    ("💌 Write a love letter to your WiFi router", 35),
]

def spin_animation():
    frames = ["🎪","🌀","🎯","⚡","🎲","🎰","🎪"]
    for _ in range(20):
        print(f"\r  {random.choice(frames)} Spinning... ", end="", flush=True)
        time.sleep(0.08)
    print()

def game_spin_win(data):
    clr()
    banner("🎪  SPIN & WIN CHAOS  🎪", C)
    box("Spin the wheel!\nComplete the challenge = earn points!")
    name = input_prompt("Your name")
    ensure_player(data, name)
    print(f"\n  {Y}Press ENTER to SPIN!{RST}")
    input()
    spin_animation()
    challenge, pts = random.choice(CHALLENGES)
    clr()
    banner("🎯 YOUR CHALLENGE! 🎯", M)
    slow_print(f"\n  {W}{BLD}{challenge}{RST}", 0.05)
    print(f"\n  {G}Complete this for {pts} pts!{RST}")
    print(f"\n  {C}Options:{RST}")
    print(f"  {Y}1.{RST} I completed it! ✅")
    print(f"  {Y}2.{RST} Skip (coward mode 🐔 -5 pts)")
    print(f"  {Y}3.{RST} Spin again (costs 10 pts)")
    choice = input_prompt("Choice")
    if choice == "1":
        verify = input_prompt("Did someone witness it? (y/n)")
        bonus = 10 if verify.lower() == "y" else 0
        add_points(data, name, pts + bonus, f"Spin challenge: {challenge[:30]}")
        data["spin_log"].append({"player": name, "challenge": challenge, "done": True})
        save_data(data)
        print(f"\n  {G}🎉 {pts+bonus} pts earned!{RST}")
    elif choice == "2":
        add_points(data, name, -5, "Skipped challenge (coward)")
        data["spin_log"].append({"player": name, "challenge": challenge, "done": False})
        save_data(data)
        print(f"\n  {R}🐔 -5 pts for being a coward!{RST}")
    elif choice == "3":
        if data["players"][name]["points"] >= 10:
            add_points(data, name, -10, "Re-spin cost")
            print(f"  {Y}Spinning again...{RST}")
            press_enter()
            game_spin_win(data)
            return
        else:
            print(f"  {R}Not enough points to re-spin!{RST}")
    press_enter()

# ─────────────────────────────────────────────
#  GAME 7: 😴 EXCUSE OLYMPICS
# ─────────────────────────────────────────────
EXCUSE_PROMPTS = [
    "Why you were late to the meeting",
    "Why you didn't do your homework",
    "Why you ate the last slice of pizza",
    "Why you haven't replied to messages in 3 days",
    "Why you're still in bed at 2pm",
    "Why you forgot someone's birthday",
    "Why you spent the whole day watching Netflix",
]

def game_excuse_olympics(data):
    clr()
    banner("😴  EXCUSE OLYMPICS  😴", Y)
    prompt = random.choice(EXCUSE_PROMPTS)
    box(f"Today's scenario:\n'{prompt}'\nBest excuse wins 45 pts + 🎭 Oscar title!")
    print(f"\n  {C}Options:{RST}")
    print(f"  {Y}1.{RST} Submit my excuse")
    print(f"  {Y}2.{RST} Vote on excuses")
    print(f"  {Y}3.{RST} See all excuses")
    choice = input_prompt("Pick option")
    if choice == "1":
        author = input_prompt("Your name")
        ensure_player(data, author)
        excuse = input_prompt(f"Your excuse for: '{prompt}'")
        data["excuses"].append({"author": author, "prompt": prompt, "excuse": excuse, "votes": 0})
        save_data(data)
        print(f"\n  {G}Excuse submitted! Oscar-worthy? 🏆{RST}")
        slow_print(f'  "{excuse}"', 0.04)
    elif choice == "2":
        same = [e for e in data["excuses"] if e["prompt"] == prompt]
        if not same:
            all_e = data["excuses"]
        else:
            all_e = same
        if not all_e:
            print(f"  {R}No excuses submitted yet!{RST}")
        else:
            print(f"\n  {C}Vote for the BEST excuse:{RST}")
            for i, e in enumerate(all_e, 1):
                print(f"  {Y}{i}.{RST} [{e['author']}]: {e['excuse']} {DIM}({e['votes']} votes){RST}")
            try:
                idx = int(input_prompt("Vote number")) - 1
                if 0 <= idx < len(all_e):
                    all_e[idx]["votes"] += 1
                    author = all_e[idx]["author"]
                    add_points(data, author, 15, "Excuse vote received")
                    save_data(data)
                    best = max(all_e, key=lambda x: x["votes"])
                    if best["votes"] >= 3:
                        add_points(data, best["author"], 30, "Excuse Olympics champion bonus")
                        if "🎭 Oscar Winner" not in data["players"][best["author"]]["titles"]:
                            data["players"][best["author"]]["titles"].append("🎭 Oscar Winner")
                            save_data(data)
                            print(f"  {Y}🏆 {best['author']} earned '🎭 Oscar Winner'!{RST}")
            except:
                pass
    elif choice == "3":
        if not data["excuses"]:
            print(f"  {R}No excuses yet!{RST}")
        else:
            for e in sorted(data["excuses"], key=lambda x: -x["votes"]):
                print(f"\n  {Y}{e['author']}{RST}: {e['excuse']}")
                print(f"  {DIM}For: {e['prompt']}{RST}")
                print(f"  {G}👍 {e['votes']} votes{RST}")
    press_enter()

# ─────────────────────────────────────────────
#  GAME 8: 🌶️ HOT TAKES STADIUM
# ─────────────────────────────────────────────
def game_hot_takes(data):
    clr()
    banner("🌶️  HOT TAKES STADIUM  🌶️", R)
    box("Post your spiciest opinion!\nMost controversial = 50 pts + 🌶️ Spicy title")
    print(f"\n  {C}Options:{RST}")
    print(f"  {Y}1.{RST} Submit hot take")
    print(f"  {Y}2.{RST} React to takes (agree/disagree)")
    print(f"  {Y}3.{RST} Controversy leaderboard")
    choice = input_prompt("Pick option")
    if choice == "1":
        author = input_prompt("Your name")
        ensure_player(data, author)
        take = input_prompt("Your spicy hot take 🌶️")
        data["hot_takes"].append({"author": author, "take": take, "agree": 0, "disagree": 0})
        save_data(data)
        print(f"\n  {G}HOT TAKE DROPPED! 🔥{RST}")
        slow_print(f'  "{take}"', 0.04)
    elif choice == "2":
        if not data["hot_takes"]:
            print(f"  {R}No hot takes yet!{RST}")
        else:
            print(f"\n  {C}React to these hot takes:{RST}")
            for i, t in enumerate(data["hot_takes"], 1):
                controversy = t["agree"] + t["disagree"]
                print(f"\n  {Y}{i}. {t['author']}{RST}: {t['take']}")
                print(f"     {G}✅ {t['agree']} agree{RST}  {R}❌ {t['disagree']} disagree{RST}  {DIM}({controversy} reactions){RST}")
            try:
                idx = int(input_prompt("React to take number")) - 1
                if 0 <= idx < len(data["hot_takes"]):
                    react = input_prompt("agree or disagree")
                    if react.lower() in ["agree","a","yes","y"]:
                        data["hot_takes"][idx]["agree"] += 1
                        print(f"  {G}✅ You agreed!{RST}")
                    else:
                        data["hot_takes"][idx]["disagree"] += 1
                        print(f"  {R}❌ You disagreed!{RST}")
                    author = data["hot_takes"][idx]["author"]
                    add_points(data, author, 5, "Hot take reaction")
                    save_data(data)
            except:
                pass
    elif choice == "3":
        if not data["hot_takes"]:
            print(f"  {R}No hot takes yet!{RST}")
        else:
            def controversy_score(t): return abs(t["agree"] - t["disagree"]) * -1 + (t["agree"]+t["disagree"])
            sorted_t = sorted(data["hot_takes"], key=controversy_score, reverse=True)
            print(f"\n  {C}{BLD}Most Controversial Hot Takes:{RST}")
            for i, t in enumerate(sorted_t[:5], 1):
                total = t["agree"] + t["disagree"]
                pct = int(t["agree"]/total*100) if total > 0 else 0
                bar_a = "█" * (pct // 5)
                bar_d = "█" * ((100-pct) // 5)
                print(f"\n  {Y}{i}. {t['author']}{RST}: {t['take']}")
                print(f"     {G}{bar_a}{RST}{R}{bar_d}{RST} {pct}% agree")
    press_enter()

# ─────────────────────────────────────────────
#  GAME 9: 🤡 CLOWN OF THE WEEK
# ─────────────────────────────────────────────
def game_clown_week(data):
    clr()
    banner("🤡  CLOWN OF THE WEEK  🤡", Y)
    box("Vote for today's biggest clown!\nWeekly crown = 🤡 Certified Clown title")
    print(f"\n  {C}Options:{RST}")
    print(f"  {Y}1.{RST} Cast my clown vote")
    print(f"  {Y}2.{RST} See today's clown votes")
    print(f"  {Y}3.{RST} Weekly clown standings")
    print(f"  {Y}4.{RST} Crown today's clown winner")
    choice = input_prompt("Pick option")
    if choice == "1":
        players = get_players(data)
        if len(players) < 2:
            print(f"  {R}Need at least 2 players!{RST}")
        else:
            print(f"\n  {C}Who was the biggest clown today?{RST}")
            for i, p in enumerate(players, 1):
                clown_count = data["clown_votes"].get(p, 0)
                print(f"  {Y}{i}.{RST} {p} 🤡×{clown_count}")
            try:
                idx = int(input_prompt("Vote number")) - 1
                if 0 <= idx < len(players):
                    name = players[idx]
                    data["clown_votes"][name] = data["clown_votes"].get(name, 0) + 1
                    save_data(data)
                    print(f"\n  {Y}🤡 Vote cast for {name}!{RST}")
                    most_clown = max(data["clown_votes"], key=data["clown_votes"].get)
                    print(f"  {DIM}Current leader: {most_clown} with {data['clown_votes'][most_clown]} 🤡 votes{RST}")
            except:
                pass
    elif choice == "2":
        if not data["clown_votes"]:
            print(f"  {R}No votes yet today!{RST}")
        else:
            print(f"\n  {C}{BLD}Today's Clown Votes:{RST}")
            for p, v in sorted(data["clown_votes"].items(), key=lambda x: -x[1]):
                bar = "🤡" * v
                print(f"  {Y}{p:<20}{RST} {bar} ({v})")
    elif choice == "3":
        clown_pts = {p: info["titles"].count("🤡 Certified Clown") for p, info in data["players"].items()}
        if not clown_pts:
            print(f"  {R}No clown history yet!{RST}")
        else:
            print(f"\n  {C}{BLD}All-time Clown Champions:{RST}")
            for p, c in sorted(clown_pts.items(), key=lambda x: -x[1]):
                print(f"  {Y}{p:<20}{RST} 🤡×{c}")
    elif choice == "4":
        if not data["clown_votes"]:
            print(f"  {R}No votes to crown from!{RST}")
        else:
            winner = max(data["clown_votes"], key=data["clown_votes"].get)
            clr()
            banner(f"🤡 CLOWN OF THE DAY: {winner.upper()} 🤡", R)
            slow_print(f"  With {data['clown_votes'][winner]} votes, {winner} is today's CERTIFIED CLOWN! 🎉", 0.04)
            ensure_player(data, winner)
            add_points(data, winner, 25, "Clown of the day (fame > shame)")
            data["players"][winner]["titles"].append("🤡 Certified Clown")
            data["clown_votes"] = {}
            save_data(data)
            print(f"\n  {DIM}Votes reset for tomorrow!{RST}")
    press_enter()

# ─────────────────────────────────────────────
#  GAME 10: 🎵 WORST SINGER SHOWDOWN
# ─────────────────────────────────────────────
SONG_PROMPTS = [
    "Happy Birthday but make it opera 🎭",
    "Your country's national anthem as a lullaby 😴",
    "A commercial jingle for toilet paper 🧻",
    "The alphabet song but jazz style 🎷",
    "Twinkle Twinkle as death metal 🤘",
    "Any song but every word rhymes with 'banana' 🍌",
    "A sad ballad about losing your keys 🔑",
]

def game_worst_singer(data):
    clr()
    banner("🎵  WORST SINGER SHOWDOWN  🎵", M)
    song_prompt = random.choice(SONG_PROMPTS)
    box(f"Today's singing challenge:\n'{song_prompt}'\nMost unhinged performance wins 55 pts!")
    print(f"\n  {C}Options:{RST}")
    print(f"  {Y}1.{RST} Register my performance")
    print(f"  {Y}2.{RST} Vote on performances")
    print(f"  {Y}3.{RST} Hall of Fame singers")
    choice = input_prompt("Pick option")
    if choice == "1":
        author = input_prompt("Your name")
        ensure_player(data, author)
        print(f"\n  {Y}Describe your performance (since we can't record audio here):{RST}")
        print(f"  {DIM}e.g. 'I sang it backward with a bucket on my head'{RST}")
        desc = input_prompt("Performance description")
        rating = input_prompt("Self rate your performance (1-10 for chaos)")
        data["singers"].append({
            "author": author,
            "prompt": song_prompt,
            "description": desc,
            "self_rating": rating,
            "votes": 0
        })
        save_data(data)
        print(f"\n  {G}Performance registered! 🎤{RST}")
        slow_print(f'  "{desc}"', 0.04)
        add_points(data, author, 10, "Brave enough to sing")
    elif choice == "2":
        if not data["singers"]:
            print(f"  {R}No performances yet!{RST}")
        else:
            print(f"\n  {C}Vote for the most UNHINGED performance:{RST}")
            for i, s in enumerate(data["singers"], 1):
                print(f"\n  {Y}{i}. {s['author']}{RST} (self-rated: {s.get('self_rating','?')}/10)")
                print(f"     Prompt: {s['prompt']}")
                print(f"     Performance: {s['description']}")
                print(f"     {G}🎤 {s['votes']} votes{RST}")
            try:
                idx = int(input_prompt("Vote number")) - 1
                if 0 <= idx < len(data["singers"]):
                    data["singers"][idx]["votes"] += 1
                    author = data["singers"][idx]["author"]
                    add_points(data, author, 15, "Singer vote received")
                    save_data(data)
                    best = max(data["singers"], key=lambda x: x["votes"])
                    if best["votes"] >= 3:
                        if "🎤 Unhinged Vocalist" not in data["players"][best["author"]]["titles"]:
                            data["players"][best["author"]]["titles"].append("🎤 Unhinged Vocalist")
                            add_points(data, best["author"], 30, "Worst Singer champion!")
                            save_data(data)
                            print(f"\n  {Y}🏆 {best['author']} earned '🎤 Unhinged Vocalist'!{RST}")
            except:
                pass
    elif choice == "3":
        if not data["singers"]:
            print(f"  {R}No hall of famers yet!{RST}")
        else:
            print(f"\n  {C}{BLD}🎤 Hall of Unhinged Vocalists:{RST}")
            for s in sorted(data["singers"], key=lambda x: -x["votes"]):
                print(f"\n  {Y}{s['author']}{RST}: {s['description']}")
                print(f"  {G}🎤 {s['votes']} votes | Self-rated: {s.get('self_rating','?')}/10{RST}")
    press_enter()

# ─────────────────────────────────────────────
#  PLAYER MANAGEMENT
# ─────────────────────────────────────────────
def manage_players(data):
    clr()
    banner("👥  PLAYER MANAGEMENT  👥", B)
    print(f"  {Y}1.{RST} Add new player")
    print(f"  {Y}2.{RST} View all players")
    print(f"  {Y}3.{RST} Reset a player's points")
    print(f"  {Y}4.{RST} Delete a player")
    choice = input_prompt("Pick option")
    if choice == "1":
        name = input_prompt("New player name")
        if name:
            ensure_player(data, name)
            save_data(data)
            print(f"  {G}✅ Player '{name}' added!{RST}")
    elif choice == "2":
        if not data["players"]:
            print(f"  {R}No players yet!{RST}")
        else:
            for name, info in data["players"].items():
                titles = ", ".join(info["titles"]) if info["titles"] else "No titles yet"
                print(f"\n  {Y}{name}{RST}")
                print(f"    Points : {G}{info['points']}{RST}")
                print(f"    Crowns : {info['crowns']} 👑")
                print(f"    Streak : {info['streak']} 🔥")
                print(f"    Titles : {DIM}{titles}{RST}")
    elif choice == "3":
        name = pick_player(data, "Choose player to reset")
        if name:
            confirm = input_prompt(f"Reset {name}'s points? (yes/no)")
            if confirm.lower() == "yes":
                data["players"][name]["points"] = 0
                save_data(data)
                print(f"  {G}Points reset for {name}.{RST}")
    elif choice == "4":
        name = pick_player(data, "Choose player to delete")
        if name:
            confirm = input_prompt(f"Delete {name}? This cannot be undone. (yes/no)")
            if confirm.lower() == "yes":
                del data["players"][name]
                save_data(data)
                print(f"  {R}Player {name} deleted.{RST}")
    press_enter()

# ─────────────────────────────────────────────
#  HISTORY LOG
# ─────────────────────────────────────────────
def show_history(data):
    clr()
    banner("📜  GAME HISTORY LOG  📜", DIM)
    if not data["history"]:
        print(f"  {R}No history yet — play some games!{RST}")
    else:
        for entry in data["history"][-30:]:
            print(f"  {DIM}• {entry}{RST}")
    press_enter()

# ─────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────
MENU_ITEMS = [
    ("🏆", "Leaderboard",          show_leaderboard),
    ("🐸", "Chaos King",           game_chaos_king),
    ("💀", "Roast Battle Arena",   game_roast_battle),
    ("🎯", "Daily Dare Club",      game_dare_club),
    ("🦆", "Duck Hunt Social",     game_duck_hunt),
    ("🧠", "Dumb Questions Battle",game_dumb_questions),
    ("🎪", "Spin & Win Chaos",     game_spin_win),
    ("😴", "Excuse Olympics",      game_excuse_olympics),
    ("🌶️", "Hot Takes Stadium",    game_hot_takes),
    ("🤡", "Clown of the Week",    game_clown_week),
    ("🎵", "Worst Singer Showdown",game_worst_singer),
    ("👥", "Player Management",    manage_players),
    ("📜", "History Log",          show_history),
]

def main():
    data = load_data()
    while True:
        clr()
        print(f"""
{M}{BLD}
  ██████╗██╗  ██╗ █████╗  ██████╗ ███████╗
 ██╔════╝██║  ██║██╔══██╗██╔═══██╗██╔════╝
 ██║     ███████║███████║██║   ██║███████╗
 ██║     ██╔══██║██╔══██║██║   ██║╚════██║
 ╚██████╗██║  ██║██║  ██║╚██████╔╝███████║
  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
{RST}
{Y}{BLD}  ░█████╗░██████╗░███████╗███╗░░██╗░█████╗░{RST}
{Y}{BLD}  ██╔══██╗██╔══██╗██╔════╝████╗░██║██╔══██╗{RST}
{Y}{BLD}  ███████║██████╔╝█████╗░░██╔██╗██║███████║{RST}
{Y}{BLD}  ██╔══██║██╔══██╗██╔══╝░░██║╚████║██╔══██║{RST}
{Y}{BLD}  ██║░░██║██║░░██║███████╗██║░╚███║██║░░██║{RST}
{Y}{BLD}  ╚═╝░░╚═╝╚═╝░░╚═╝╚══════╝╚═╝░░╚══╝╚═╝░░╚═╝{RST}
{C}        🎪 10 Playful Group Games + Leaderboard 🎪{RST}
""")
        # Quick stats
        total_players = len(data["players"])
        total_points = sum(p["points"] for p in data["players"].values())
        leader = max(data["players"], key=lambda x: data["players"][x]["points"]) if data["players"] else "—"
        print(f"  {DIM}Players: {total_players} | Total pts: {total_points} | Leader: {leader}{RST}\n")

        for i, (emoji, name, _) in enumerate(MENU_ITEMS, 1):
            num_color = Y if i <= 11 else C
            suffix = " ← START HERE" if i == 12 and total_players == 0 else ""
            print(f"  {num_color}{BLD}{str(i).rjust(2)}.{RST}  {emoji}  {name}{DIM}{suffix}{RST}")

        print(f"\n  {R}{BLD}  0.{RST}  ❌  Quit\n")
        divider()
        choice = input_prompt("Pick a game (0-13)")
        try:
            idx = int(choice)
            if idx == 0:
                clr()
                slow_print(f"\n  {M}{BLD}Thanks for playing CHAOS ARENA! 🎪{RST}", 0.04)
                slow_print(f"  {DIM}Your data is saved in {DATA_FILE}{RST}", 0.03)
                print()
                break
            elif 1 <= idx <= len(MENU_ITEMS):
                _, _, func = MENU_ITEMS[idx-1]
                func(data)
                data = load_data()  # reload in case saved
        except (ValueError, IndexError):
            print(f"  {R}Invalid choice!{RST}")
            time.sleep(0.8)

if __name__ == "__main__":
    main()
