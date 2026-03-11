"""
🏟️ CHAOS ARENA — Telegram Group Bot
=====================================
HOW TO RUN:
  1. Install:  pip install python-telegram-bot
  2. Put your token below in BOT_TOKEN
  3. Run:      python3 chaos_arena_bot.py

HOW TO GET A TOKEN:
  - Open Telegram → search @BotFather → /newbot → follow steps → copy token

HOW TO ADD TO A GROUP:
  - Add your bot to the group
  - Give it admin rights (so it can send messages)
  - Send /start in the group

GAMES INCLUDED (all with inline buttons):
  1. 🏆 Leaderboard
  2. 👑 Chaos King  — vote who caused most chaos
  3. 🔥 Roast Battle — submit & vote roasts
  4. 🎯 Dare Club    — random dares with point rewards
  5. 🧠 Dumb Qs     — submit & vote dumbest question
  6. 😴 Excuse Olympics — best excuse wins
  7. 🌶️ Hot Takes   — agree / disagree voting
  8. 📖 Story Builder — one sentence at a time
  9. 📣 Scream Void — scream & react
 10. 🔮 Predictions — predict & resolve
"""

import logging
import random
import json
import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ─────────────────────────────────────────
#  Token is read from Render environment variable
#  Set BOT_TOKEN in Render dashboard → Environment
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
# ─────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════
# IN-MEMORY STATE  (per chat_id)
# ══════════════════════════════════════════
# state[chat_id] = {
#   players: {user_id: name},
#   scores:  {name: int},
#   chaos_votes: {name: int},
#   roasts:  [{author, target, text, votes, id}],
#   dumb_qs: [{author, q, votes, id}],
#   excuses: [{author, text, votes, id}],
#   hot_takes:[{author, text, agree, disagree, id}],
#   story:   [{author, sentence}],
#   screams: [{author, text}],
#   predictions:[{author, text, status, id}],
#   dare_history:[{player, dare, level, pts, status}],
#   current_dare:{dare, level, pts} | None,
#   awaiting: None | "roast_text" | "dumb_q" | "excuse" | "hot_take" | "story_line" | "scream" | "prediction",
#   awaiting_author: str | None,
#   awaiting_target: str | None,
# }

state = {}

def get_state(chat_id):
    if chat_id not in state:
        state[chat_id] = {
            "players": {},
            "scores": {},
            "chaos_votes": {},
            "roasts": [],
            "dumb_qs": [],
            "excuses": [],
            "hot_takes": [],
            "story": [],
            "screams": [],
            "predictions": [],
            "dare_history": [],
            "current_dare": None,
            "awaiting": None,
            "awaiting_author": None,
            "awaiting_target": None,
        }
    return state[chat_id]

def get_name(s, user):
    uid = str(user.id)
    if uid in s["players"]:
        return s["players"][uid]
    name = user.first_name or user.username or "Player"
    s["players"][uid] = name
    if name not in s["scores"]:
        s["scores"][name] = 0
    if name not in s["chaos_votes"]:
        s["chaos_votes"][name] = 0
    return name

def add_points(s, name, pts):
    s["scores"][name] = max(0, s["scores"].get(name, 0) + pts)

def sorted_lb(s):
    return sorted(s["scores"].items(), key=lambda x: x[1], reverse=True)

def lb_text(s):
    medals = ["🥇","🥈","🥉"]
    rows = sorted_lb(s)
    if not rows:
        return "No players yet! Send /join to join the game."
    lines = ["🏆 <b>LEADERBOARD</b>\n"]
    for i,(name,pts) in enumerate(rows):
        m = medals[i] if i < 3 else f"#{i+1}"
        lines.append(f"{m} {name} — <b>{pts} pts</b>")
    return "\n".join(lines)

# ══════════════════════════════════════════
# DATA BANKS
# ══════════════════════════════════════════
DARE_BANK = {
    "easy": [
        "Do your best robot impression for 15 seconds 🤖",
        "Speak in a funny accent for your next 2 messages 🎭",
        "Send the most embarrassing emoji combo you can think of 😬",
        "Write a haiku about this group right now 🌸",
        "Text 'I am a potato 🥔' to one of your contacts",
    ],
    "medium": [
        "Change your profile pic to a potato for 1 hour 🥔",
        "Do a dramatic reading of your last sent message 🎬",
        "Speak only in rhymes for the next 5 minutes 🎵",
        "Call someone and sing Happy Birthday to them 🎂",
        "Post a blurry selfie in the group right now 🤳",
    ],
    "hard": [
        "Write a love poem about your fridge and post it ❤️🍕",
        "Send a voice message doing your best impression of a news anchor 📰",
        "Post an embarrassing childhood photo 😬",
        "Let the group pick your next profile photo for 2 hours 📸",
        "Do a 1-minute stand-up comedy bit in voice message 😂",
    ],
    "insane": [
        "Post 'I love homework 📚' on your main social media story 😱",
        "Prank call someone with the group listening on voice chat 📞",
        "Let someone post ONE thing from your account 📱",
        "Eat the weirdest food combo the group votes on 🍕🍫",
        "Wear a sign saying 'I lost a dare' to your next video call 🪧",
    ],
}
DARE_PTS = {"easy": 1, "medium": 2, "hard": 3, "insane": 5}

DUMB_QS = [
    "If I ate myself, would I become twice as big or disappear? 🤔",
    "Why do we park in driveways and drive on parkways? 🚗",
    "Can blind people see their dreams? 👁️",
    "Why is there a 'D' in fridge but not refrigerator? 🥶",
    "If you punch yourself and it hurts, are you weak or strong? 💪",
    "Do fish ever get thirsty? 🐟",
    "If no one buys a movie ticket, does it still play? 🎬",
    "Is cereal just cold soup? 🥣",
    "If a word is misspelled in the dictionary, how would we know? 📖",
    "Why do we call them buildings if they're already built? 🏢",
]

EXCUSES = [
    "I was abducted by aliens but they dropped me off late 👽",
    "My cat sat on my keyboard and declined the invite 🐱",
    "I got stuck in a time loop and just escaped ⏰",
    "My GPS took me to Narnia again 🦁",
    "I was busy saving the world — you're welcome 🦸",
    "My horoscope said not to be on time today ♈",
    "I was in a thumb war with myself and it went to overtime 👍",
    "The simulation had a bug and reset my alarm ⚙️",
    "I was conducting urgent research on cloud shapes ☁️",
    "My mirror told me I looked too good to rush 🪞",
]

HOT_TAKES = [
    "Pineapple on pizza is objectively the best topping 🍕",
    "Cereal is just cold soup and we need to accept that 🥣",
    "Sandwiches always taste better when someone else makes them 🥪",
    "Baths are just human soup and that's a fact 🛁",
    "Pigeons are underrated and deserve our respect 🐦",
    "Sleeping is objectively the most fun activity in existence 😴",
    "Elevator music is genuinely a vibe 🎵",
    "Alarm clocks should be illegal before 8am ⏰",
    "The best part of a group chat is leaving it 📱",
    "Cold pizza is better than hot pizza 🍕",
]

ROAST_TEMPLATES = [
    "{author} says {target} has the energy of a wet sock on a Monday 🧦",
    "{author} says {target}'s jokes are like WiFi passwords — nobody asks for them 📶",
    "{author} says {target} once got lost in a one-room apartment 🚪",
    "{author} says {target} is the human equivalent of a 5% battery 🔋",
    "{author} claims when {target} enters a room, even the plants move to the exit 🌿",
    "{author} says {target}'s fashion sense is 'close my eyes and try again' 👗",
    "{author} reports {target}'s brain lost a fight with autocorrect 🤖",
    "{author} says {target} is so slow, dial-up internet once passed them 🐌",
]

STORY_STARTERS = [
    "Once upon a time, a very confused penguin walked into a tech startup and said...",
    "Nobody expected that Tuesday would be the day the vending machine became sentient...",
    "The group chat was silent for 3 whole minutes — a world record — until...",
    "Scientists confirmed today that chairs are secretly plotting against humanity, and the first sign was...",
    "Everything was fine until the group's pet rock sent a Telegram message that read...",
]

PREDICTIONS = [
    "By next week, someone will forget their camera is on during a call 📹",
    "Someone will send a voice note longer than 5 minutes soon 🎙️",
    "The group chat will go silent for 24 hours this month 💤",
    "Someone will accidentally send a message to the wrong chat 😬",
    "Someone will pull an all-nighter before an important deadline 🌙",
    "At least 2 people will cancel last-minute on a group plan 😬",
]

CHAOS_ACTS = [
    "Everyone must respond in questions only for 5 minutes 🤔",
    "Next message must contain an animal sound 🐮",
    "Send a voice message screaming your own name 📣",
    "Change your profile pic to a potato for 1 hour 🥔",
    "Send the most chaotic meme you own 😂",
    "Describe your day using only food names 🍕",
    "Speak only in movie quotes for 3 messages 🎬",
    "Type everything BACKWARDS for next 2 messages 🔄",
    "Describe this group chat as a movie genre 🎬",
    "Everyone sends their current location vibe in one emoji 📍",
]

# ══════════════════════════════════════════
# KEYBOARDS
# ══════════════════════════════════════════
def main_menu_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🏆 Leaderboard", callback_data="lb"),
            InlineKeyboardButton("👑 Chaos King", callback_data="chaos_menu"),
        ],
        [
            InlineKeyboardButton("🔥 Roast Battle", callback_data="roast_menu"),
            InlineKeyboardButton("🎯 Dare Club", callback_data="dare_menu"),
        ],
        [
            InlineKeyboardButton("🧠 Dumb Questions", callback_data="dumb_menu"),
            InlineKeyboardButton("😴 Excuse Olympics", callback_data="excuse_menu"),
        ],
        [
            InlineKeyboardButton("🌶️ Hot Takes", callback_data="ht_menu"),
            InlineKeyboardButton("📖 Story Builder", callback_data="story_menu"),
        ],
        [
            InlineKeyboardButton("📣 Scream Void", callback_data="void_menu"),
            InlineKeyboardButton("🔮 Predictions", callback_data="pred_menu"),
        ],
        [
            InlineKeyboardButton("📋 How to Play", callback_data="howto"),
        ],
    ])

def back_kb(target="main"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Menu", callback_data=target)]])

# ══════════════════════════════════════════
# /start  /help  /join
# ══════════════════════════════════════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = get_state(update.effective_chat.id)
    name = get_name(s, update.effective_user)
    text = (
        "🏟️ <b>CHAOS ARENA</b> — The Ultimate Group Game!\n\n"
        f"Welcome, <b>{name}</b>! You're now registered.\n\n"
        "Everyone in the group should send /join to register.\n"
        "Then pick a game below and let the chaos begin! 👇"
    )
    await update.message.reply_html(text, reply_markup=main_menu_kb())

async def cmd_join(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = get_state(update.effective_chat.id)
    name = get_name(s, update.effective_user)
    await update.message.reply_html(
        f"✅ <b>{name}</b> has joined the arena! 🏟️\n\n"
        f"Current players: {', '.join(s['scores'].keys()) or 'just you!'}",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🎮 Open Menu", callback_data="main"),
        ]])
    )

async def cmd_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html("🏟️ <b>CHAOS ARENA MENU</b>", reply_markup=main_menu_kb())

async def cmd_lb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = get_state(update.effective_chat.id)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="lb"),
         InlineKeyboardButton("👑 Crown Winner", callback_data="lb_crown")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main")],
    ])
    await update.message.reply_html(lb_text(s), reply_markup=kb)

# ══════════════════════════════════════════
# CALLBACK ROUTER
# ══════════════════════════════════════════
async def callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    chat_id = q.message.chat_id
    user = q.from_user
    s = get_state(chat_id)
    name = get_name(s, user)

    # ── MAIN MENU ──
    if data == "main":
        await q.edit_message_text("🏟️ <b>CHAOS ARENA MENU</b>\n\nPick a game! 👇",
                                   parse_mode="HTML", reply_markup=main_menu_kb())

    # ── HOW TO PLAY ──
    elif data == "howto":
        text = (
            "📋 <b>HOW TO PLAY</b>\n\n"
            "1️⃣ Everyone sends /join to register\n"
            "2️⃣ Pick a game from the menu\n"
            "3️⃣ Play, vote, earn points!\n"
            "4️⃣ Check 🏆 Leaderboard anytime\n\n"
            "<b>Commands:</b>\n"
            "/start — Show main menu\n"
            "/join  — Register as a player\n"
            "/menu  — Open menu\n"
            "/lb    — Show leaderboard\n\n"
            "<b>Points per game:</b>\n"
            "👑 Chaos King → +3pts\n"
            "🔥 Roast Winner → +3pts\n"
            "🎯 Dare Complete → +1 to +5pts\n"
            "🧠 Dumbest Q → +2pts\n"
            "😴 Best Excuse → +2pts\n"
            "🌶️ Most Controversial → +3pts\n"
            "📖 Funniest Story Line → +1pt\n"
            "🔮 Correct Prediction → +3pts\n"
        )
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=back_kb())

    # ══════════════════════════════════════════
    # 🏆 LEADERBOARD
    # ══════════════════════════════════════════
    elif data == "lb":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="lb"),
             InlineKeyboardButton("👑 Crown Winner", callback_data="lb_crown")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main")],
        ])
        await q.edit_message_text(lb_text(s), parse_mode="HTML", reply_markup=kb)

    elif data == "lb_crown":
        rows = sorted_lb(s)
        if not rows:
            await q.answer("No players yet!", show_alert=True)
            return
        winner, pts = rows[0]
        text = (
            f"👑 <b>CHAOS ARENA WINNER!</b>\n\n"
            f"🏆 <b>{winner}</b> wins with <b>{pts} points!</b>\n\n"
            + lb_text(s)
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]])
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=kb)

    # ══════════════════════════════════════════
    # 👑 CHAOS KING
    # ══════════════════════════════════════════
    elif data == "chaos_menu":
        players_list = list(s["scores"].keys())
        if not players_list:
            await q.answer("No players! Everyone send /join first.", show_alert=True)
            return
        total = sum(s["chaos_votes"].values())
        lines = ["👑 <b>CHAOS KING — Vote!</b>\n", "Who caused the most chaos today?\n"]
        for p in players_list:
            v = s["chaos_votes"].get(p, 0)
            bar = "▓" * v + "░" * max(0, 5 - v)
            lines.append(f"{bar} {p} — {v} votes")
        lines.append(f"\n<i>Total votes: {total}</i>")

        vote_btns = [InlineKeyboardButton(f"👹 {p}", callback_data=f"chaos_vote_{p}")
                     for p in players_list]
        rows_btns = [vote_btns[i:i+2] for i in range(0, len(vote_btns), 2)]
        rows_btns.append([
            InlineKeyboardButton("👑 Crown Chaos King (+3pts)", callback_data="chaos_crown"),
            InlineKeyboardButton("🎲 Random Chaos Act", callback_data="chaos_act"),
        ])
        rows_btns.append([InlineKeyboardButton("🔄 Refresh", callback_data="chaos_menu"),
                          InlineKeyboardButton("⬅️ Back", callback_data="main")])
        await q.edit_message_text("\n".join(lines), parse_mode="HTML",
                                   reply_markup=InlineKeyboardMarkup(rows_btns))

    elif data.startswith("chaos_vote_"):
        target = data[len("chaos_vote_"):]
        if target not in s["chaos_votes"]:
            s["chaos_votes"][target] = 0
        s["chaos_votes"][target] += 1
        await q.answer(f"👹 You voted {target} for chaos!")
        # Refresh panel
        players_list = list(s["scores"].keys())
        total = sum(s["chaos_votes"].values())
        lines = ["👑 <b>CHAOS KING — Vote!</b>\n", "Who caused the most chaos today?\n"]
        for p in players_list:
            v = s["chaos_votes"].get(p, 0)
            bar = "▓" * v + "░" * max(0, 5 - v)
            lines.append(f"{bar} {p} — {v} votes")
        lines.append(f"\n<i>Total votes: {total}</i>\n✅ {name} just voted for {target}!")
        vote_btns = [InlineKeyboardButton(f"👹 {p}", callback_data=f"chaos_vote_{p}")
                     for p in players_list]
        rows_btns = [vote_btns[i:i+2] for i in range(0, len(vote_btns), 2)]
        rows_btns.append([
            InlineKeyboardButton("👑 Crown Chaos King (+3pts)", callback_data="chaos_crown"),
            InlineKeyboardButton("🎲 Random Chaos Act", callback_data="chaos_act"),
        ])
        rows_btns.append([InlineKeyboardButton("🔄 Refresh", callback_data="chaos_menu"),
                          InlineKeyboardButton("⬅️ Back", callback_data="main")])
        await q.edit_message_text("\n".join(lines), parse_mode="HTML",
                                   reply_markup=InlineKeyboardMarkup(rows_btns))

    elif data == "chaos_crown":
        if not s["scores"]:
            await q.answer("No players!", show_alert=True); return
        winner = max(s["chaos_votes"], key=lambda p: s["chaos_votes"].get(p, 0))
        add_points(s, winner, 3)
        text = (
            f"👑 <b>CHAOS KING CROWNED!</b>\n\n"
            f"🥇 <b>{winner}</b> is today's Chaos King!\n"
            f"Votes: {s['chaos_votes'].get(winner, 0)} 👹\n"
            f"+3 points added!\n\n" + lb_text(s)
        )
        for p in s["chaos_votes"]: s["chaos_votes"][p] = 0
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]])
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=kb)

    elif data == "chaos_act":
        act = random.choice(CHAOS_ACTS)
        await q.edit_message_text(
            f"🎲 <b>CHAOS ACT!</b>\n\n{act}\n\n<i>Everyone must do this NOW! 😈</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎲 New Act", callback_data="chaos_act"),
                 InlineKeyboardButton("⬅️ Back", callback_data="chaos_menu")],
            ])
        )

    # ══════════════════════════════════════════
    # 🔥 ROAST BATTLE
    # ══════════════════════════════════════════
    elif data == "roast_menu":
        players_list = list(s["scores"].keys())
        lines = ["🔥 <b>ROAST BATTLE</b>\n"]
        if s["roasts"]:
            lines.append(f"<i>{len(s['roasts'])} roasts submitted</i>\n")
            for r in s["roasts"][-3:]:
                lines.append(f'"{r["text"]}"\n— {r["author"]} → {r["target"]} | 🔥{r["votes"]} votes\n')
        else:
            lines.append("<i>No roasts yet! Be the first!</i>")

        kb_rows = [
            [InlineKeyboardButton("✍️ Submit a Roast", callback_data="roast_start"),
             InlineKeyboardButton("🤖 Auto-Generate Roast", callback_data="roast_auto")],
            [InlineKeyboardButton("🏆 Crown Top Roaster (+3pts)", callback_data="roast_crown")],
            [InlineKeyboardButton("🔄 Show All Roasts", callback_data="roast_list"),
             InlineKeyboardButton("⬅️ Back", callback_data="main")],
        ]
        await q.edit_message_text("\n".join(lines), parse_mode="HTML",
                                   reply_markup=InlineKeyboardMarkup(kb_rows))

    elif data == "roast_start":
        players_list = list(s["scores"].keys())
        if len(players_list) < 2:
            await q.answer("Need at least 2 players!", show_alert=True); return
        # Pick target buttons
        btns = [InlineKeyboardButton(f"🎯 Roast {p}", callback_data=f"roast_target_{p}")
                for p in players_list if p != name]
        rows = [btns[i:i+2] for i in range(0, len(btns), 2)]
        rows.append([InlineKeyboardButton("⬅️ Back", callback_data="roast_menu")])
        await q.edit_message_text(
            f"🔥 <b>ROAST BATTLE</b>\n\n{name}, who do you want to roast?",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows)
        )

    elif data.startswith("roast_target_"):
        target = data[len("roast_target_"):]
        s["awaiting"] = "roast_text"
        s["awaiting_author"] = name
        s["awaiting_target"] = target
        await q.edit_message_text(
            f"🔥 <b>ROAST BATTLE</b>\n\n"
            f"<b>{name}</b>, now type your roast of <b>{target}</b>!\n\n"
            f"<i>Just type it in the chat right now 👇</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="roast_menu")]])
        )

    elif data == "roast_auto":
        players_list = list(s["scores"].keys())
        if len(players_list) < 2:
            await q.answer("Need at least 2 players!", show_alert=True); return
        author = name
        others = [p for p in players_list if p != author]
        target = random.choice(others) if others else random.choice(players_list)
        t = random.choice(ROAST_TEMPLATES)
        text = t.replace("{author}", author).replace("{target}", target)
        s["roasts"].append({"author": author, "target": target, "text": text, "votes": 0, "id": len(s["roasts"])})
        await q.edit_message_text(
            f"🔥 <b>AUTO ROAST SUBMITTED!</b>\n\n\"{text}\"",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔥 Vote this Fire!", callback_data=f"roast_vote_{len(s['roasts'])-1}"),
                 InlineKeyboardButton("🤖 Generate Another", callback_data="roast_auto")],
                [InlineKeyboardButton("⬅️ Back", callback_data="roast_menu")],
            ])
        )

    elif data.startswith("roast_vote_"):
        idx = int(data.split("_")[-1])
        if idx < len(s["roasts"]):
            s["roasts"][idx]["votes"] += 1
            await q.answer("🔥 Voted!")
            await q.edit_message_text(
                f"🔥 <b>ROAST</b>\n\n\"{s['roasts'][idx]['text']}\"\n"
                f"— {s['roasts'][idx]['author']} → {s['roasts'][idx]['target']}\n"
                f"🔥 {s['roasts'][idx]['votes']} votes",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"🔥 Fire! ({s['roasts'][idx]['votes']})", callback_data=f"roast_vote_{idx}"),
                     InlineKeyboardButton("⬅️ Back", callback_data="roast_menu")],
                ])
            )

    elif data == "roast_list":
        if not s["roasts"]:
            await q.answer("No roasts yet!", show_alert=True); return
        lines = ["🔥 <b>ALL ROASTS</b>\n"]
        btn_rows = []
        for i, r in enumerate(s["roasts"]):
            lines.append(f"{i+1}. \"{r['text']}\"\n   — {r['author']}→{r['target']} | 🔥{r['votes']}\n")
            btn_rows.append([InlineKeyboardButton(f"🔥 Vote #{i+1}", callback_data=f"roast_vote_{i}")])
        btn_rows.append([InlineKeyboardButton("⬅️ Back", callback_data="roast_menu")])
        await q.edit_message_text("\n".join(lines), parse_mode="HTML",
                                   reply_markup=InlineKeyboardMarkup(btn_rows))

    elif data == "roast_crown":
        if not s["roasts"]:
            await q.answer("No roasts yet!", show_alert=True); return
        top = max(s["roasts"], key=lambda r: r["votes"])
        add_points(s, top["author"], 3)
        await q.edit_message_text(
            f"🏆 <b>ROAST BATTLE WINNER!</b>\n\n"
            f"<b>{top['author']}</b> wins with:\n\"{top['text']}\"\n"
            f"🔥 {top['votes']} votes | +3 points!\n\n" + lb_text(s),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]])
        )

    # ══════════════════════════════════════════
    # 🎯 DARE CLUB
    # ══════════════════════════════════════════
    elif data == "dare_menu":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("😊 Easy (+1pt)", callback_data="dare_gen_easy"),
             InlineKeyboardButton("😅 Medium (+2pts)", callback_data="dare_gen_medium")],
            [InlineKeyboardButton("😱 Hard (+3pts)", callback_data="dare_gen_hard"),
             InlineKeyboardButton("💀 Insane (+5pts)", callback_data="dare_gen_insane")],
            [InlineKeyboardButton("🎲 Random Level Dare", callback_data="dare_gen_random"),
             InlineKeyboardButton("👤 Dare a Player", callback_data="dare_player_pick")],
            [InlineKeyboardButton("📋 Dare History", callback_data="dare_history"),
             InlineKeyboardButton("⬅️ Back", callback_data="main")],
        ])
        await q.edit_message_text(
            "🎯 <b>DARE CLUB</b>\n\nChoose a difficulty level!",
            parse_mode="HTML", reply_markup=kb
        )

    elif data.startswith("dare_gen_"):
        level = data[len("dare_gen_"):]
        if level == "random":
            level = random.choice(["easy","medium","hard","insane"])
        dare = random.choice(DARE_BANK[level])
        pts = DARE_PTS[level]
        s["current_dare"] = {"dare": dare, "level": level, "pts": pts, "assigned": name}
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ I Did It! (+{pts}pts)", callback_data="dare_complete"),
             InlineKeyboardButton("❌ Skip (-1pt)", callback_data="dare_skip")],
            [InlineKeyboardButton("🔄 New Dare (same level)", callback_data=f"dare_gen_{level}"),
             InlineKeyboardButton("⬅️ Back", callback_data="dare_menu")],
        ])
        await q.edit_message_text(
            f"🎯 <b>DARE — {level.upper()}</b> ({pts}pts)\n\n"
            f"<b>{name}</b>, your dare is:\n\n{dare}\n\n"
            f"<i>Complete it and tap ✅ to earn your points!</i>",
            parse_mode="HTML", reply_markup=kb
        )

    elif data == "dare_player_pick":
        players_list = list(s["scores"].keys())
        btns = [InlineKeyboardButton(f"🎯 {p}", callback_data=f"dare_assign_{p}") for p in players_list]
        rows = [btns[i:i+2] for i in range(0, len(btns), 2)]
        rows.append([InlineKeyboardButton("⬅️ Back", callback_data="dare_menu")])
        await q.edit_message_text("🎯 <b>DARE A PLAYER</b>\n\nPick who gets the dare:",
                                   parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))

    elif data.startswith("dare_assign_"):
        target = data[len("dare_assign_"):]
        level = random.choice(["easy","medium","hard","insane"])
        dare = random.choice(DARE_BANK[level])
        pts = DARE_PTS[level]
        s["current_dare"] = {"dare": dare, "level": level, "pts": pts, "assigned": target}
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ {target} Did It! (+{pts}pts)", callback_data="dare_complete_other"),
             InlineKeyboardButton("❌ Skip (-1pt)", callback_data="dare_skip")],
            [InlineKeyboardButton("🎲 New Dare", callback_data=f"dare_gen_{level}"),
             InlineKeyboardButton("⬅️ Back", callback_data="dare_menu")],
        ])
        await q.edit_message_text(
            f"🎯 <b>DARE FOR {target.upper()}</b> ({pts}pts)\n\n{dare}\n\n"
            f"<i>Mark complete when {target} finishes!</i>",
            parse_mode="HTML", reply_markup=kb
        )

    elif data == "dare_complete":
        d = s.get("current_dare")
        if not d:
            await q.answer("No dare active!", show_alert=True); return
        add_points(s, name, d["pts"])
        s["dare_history"].append({**d, "player": name, "status": "✅"})
        await q.edit_message_text(
            f"✅ <b>DARE COMPLETED!</b>\n\n"
            f"<b>{name}</b> completed:\n{d['dare']}\n\n"
            f"+{d['pts']} points! 🎉\n\n" + lb_text(s),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Another Dare", callback_data="dare_menu"),
                 InlineKeyboardButton("⬅️ Main Menu", callback_data="main")],
            ])
        )
        s["current_dare"] = None

    elif data == "dare_complete_other":
        d = s.get("current_dare")
        if not d:
            await q.answer("No dare active!", show_alert=True); return
        player = d.get("assigned", name)
        add_points(s, player, d["pts"])
        s["dare_history"].append({**d, "player": player, "status": "✅"})
        await q.edit_message_text(
            f"✅ <b>DARE COMPLETED!</b>\n\n"
            f"<b>{player}</b> completed:\n{d['dare']}\n\n"
            f"+{d['pts']} points! 🎉\n\n" + lb_text(s),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Another Dare", callback_data="dare_menu"),
                 InlineKeyboardButton("⬅️ Main Menu", callback_data="main")],
            ])
        )
        s["current_dare"] = None

    elif data == "dare_skip":
        d = s.get("current_dare")
        player = d.get("assigned", name) if d else name
        add_points(s, player, -1)
        s["current_dare"] = None
        await q.edit_message_text(
            f"❌ <b>Dare skipped!</b>\n\n{player} loses 1 point.\n\n" + lb_text(s),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Try Another Dare", callback_data="dare_menu"),
                 InlineKeyboardButton("⬅️ Main Menu", callback_data="main")],
            ])
        )

    elif data == "dare_history":
        hist = s["dare_history"]
        if not hist:
            await q.answer("No dare history yet!", show_alert=True); return
        lines = ["📋 <b>DARE HISTORY</b>\n"]
        for d in hist[-8:]:
            lines.append(f"{d['status']} {d.get('player','?')} — {d['dare'][:50]}...")
        await q.edit_message_text("\n".join(lines), parse_mode="HTML",
                                   reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="dare_menu")]]))

    # ══════════════════════════════════════════
    # 🧠 DUMB QUESTIONS
    # ══════════════════════════════════════════
    elif data == "dumb_menu":
        lines = ["🧠 <b>DUMB QUESTIONS BATTLE</b>\n"]
        if s["dumb_qs"]:
            lines.append(f"<i>{len(s['dumb_qs'])} questions submitted</i>\n")
            for q2 in s["dumb_qs"][-3:]:
                lines.append(f'"{q2["q"]}"\n— {q2["author"]} | 🧠{q2["votes"]} votes\n')
        else:
            lines.append("<i>No questions yet!</i>")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✍️ Submit a Dumb Q", callback_data="dumb_submit"),
             InlineKeyboardButton("🎲 Random Dumb Q", callback_data="dumb_random")],
            [InlineKeyboardButton("🗳️ Vote on Questions", callback_data="dumb_vote_list"),
             InlineKeyboardButton("🏆 Crown Dumbest (+2pts)", callback_data="dumb_crown")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="dumb_menu"),
             InlineKeyboardButton("⬅️ Back", callback_data="main")],
        ])
        await q.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=kb)

    elif data == "dumb_submit":
        s["awaiting"] = "dumb_q"
        s["awaiting_author"] = name
        await q.edit_message_text(
            "🧠 <b>DUMB QUESTIONS</b>\n\nType your dumbest question in the chat right now! 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="dumb_menu")]])
        )

    elif data == "dumb_random":
        dq = random.choice(DUMB_QS)
        s["dumb_qs"].append({"author": name, "q": dq, "votes": 0, "id": len(s["dumb_qs"])})
        await q.edit_message_text(
            f"🧠 <b>RANDOM DUMB Q SUBMITTED!</b>\n\n\"{dq}\"\n— {name}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🧠 Vote!", callback_data=f"dumb_vote_{len(s['dumb_qs'])-1}"),
                 InlineKeyboardButton("⬅️ Back", callback_data="dumb_menu")],
            ])
        )

    elif data == "dumb_vote_list":
        if not s["dumb_qs"]:
            await q.answer("No questions yet!", show_alert=True); return
        lines = ["🧠 <b>VOTE — DUMBEST QUESTION</b>\n"]
        btn_rows = []
        for i, dq in enumerate(s["dumb_qs"]):
            lines.append(f"{i+1}. \"{dq['q']}\"\n   — {dq['author']} | 🧠{dq['votes']}\n")
            btn_rows.append([InlineKeyboardButton(f"🧠 Vote #{i+1}", callback_data=f"dumb_vote_{i}")])
        btn_rows.append([InlineKeyboardButton("⬅️ Back", callback_data="dumb_menu")])
        await q.edit_message_text("\n".join(lines), parse_mode="HTML",
                                   reply_markup=InlineKeyboardMarkup(btn_rows))

    elif data.startswith("dumb_vote_"):
        idx = int(data.split("_")[-1])
        if idx < len(s["dumb_qs"]):
            s["dumb_qs"][idx]["votes"] += 1
            await q.answer("🧠 Voted!")
        await q.edit_message_text(
            f"🧠 Voted!\n\n\"{s['dumb_qs'][idx]['q']}\"\n🧠 {s['dumb_qs'][idx]['votes']} votes",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗳️ More Votes", callback_data="dumb_vote_list"),
                 InlineKeyboardButton("⬅️ Back", callback_data="dumb_menu")],
            ])
        )

    elif data == "dumb_crown":
        if not s["dumb_qs"]:
            await q.answer("No questions!", show_alert=True); return
        top = max(s["dumb_qs"], key=lambda x: x["votes"])
        add_points(s, top["author"], 2)
        await q.edit_message_text(
            f"🏆 <b>DUMBEST QUESTION WINNER!</b>\n\n"
            f"<b>{top['author']}</b> wins with:\n\"{top['q']}\"\n"
            f"🧠 {top['votes']} votes | +2 points!\n\n" + lb_text(s),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]])
        )

    # ══════════════════════════════════════════
    # 😴 EXCUSE OLYMPICS
    # ══════════════════════════════════════════
    elif data == "excuse_menu":
        lines = ["😴 <b>EXCUSE OLYMPICS</b>\n"]
        if s["excuses"]:
            lines.append(f"<i>{len(s['excuses'])} excuses submitted</i>\n")
            for e in s["excuses"][-3:]:
                lines.append(f'"{e["text"]}"\n— {e["author"]} | 🥇{e["votes"]}\n')
        else:
            lines.append("<i>No excuses yet!</i>")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✍️ Submit My Excuse", callback_data="excuse_submit"),
             InlineKeyboardButton("🎲 Random Excuse", callback_data="excuse_random")],
            [InlineKeyboardButton("🗳️ Vote on Excuses", callback_data="excuse_vote_list"),
             InlineKeyboardButton("🥇 Crown Best (+2pts)", callback_data="excuse_crown")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="excuse_menu"),
             InlineKeyboardButton("⬅️ Back", callback_data="main")],
        ])
        await q.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=kb)

    elif data == "excuse_submit":
        s["awaiting"] = "excuse"
        s["awaiting_author"] = name
        await q.edit_message_text(
            "😴 <b>EXCUSE OLYMPICS</b>\n\nType your excuse for being late/lazy right now! 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="excuse_menu")]])
        )

    elif data == "excuse_random":
        exc = random.choice(EXCUSES)
        s["excuses"].append({"author": name, "text": exc, "votes": 0, "id": len(s["excuses"])})
        await q.edit_message_text(
            f"😴 <b>EXCUSE SUBMITTED!</b>\n\n\"{exc}\"\n— {name}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🥇 Vote!", callback_data=f"excuse_vote_{len(s['excuses'])-1}"),
                 InlineKeyboardButton("⬅️ Back", callback_data="excuse_menu")],
            ])
        )

    elif data == "excuse_vote_list":
        if not s["excuses"]:
            await q.answer("No excuses yet!", show_alert=True); return
        lines = ["🥇 <b>VOTE — BEST EXCUSE</b>\n"]
        btn_rows = []
        for i, e in enumerate(s["excuses"]):
            lines.append(f"{i+1}. \"{e['text']}\"\n   — {e['author']} | 🥇{e['votes']}\n")
            btn_rows.append([InlineKeyboardButton(f"🥇 Vote #{i+1}", callback_data=f"excuse_vote_{i}")])
        btn_rows.append([InlineKeyboardButton("⬅️ Back", callback_data="excuse_menu")])
        await q.edit_message_text("\n".join(lines), parse_mode="HTML",
                                   reply_markup=InlineKeyboardMarkup(btn_rows))

    elif data.startswith("excuse_vote_"):
        idx = int(data.split("_")[-1])
        if idx < len(s["excuses"]):
            s["excuses"][idx]["votes"] += 1
            await q.answer("🥇 Voted!")
        await q.edit_message_text(
            f"🥇 Voted!\n\n\"{s['excuses'][idx]['text']}\"\n🥇 {s['excuses'][idx]['votes']} votes",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗳️ More Votes", callback_data="excuse_vote_list"),
                 InlineKeyboardButton("⬅️ Back", callback_data="excuse_menu")],
            ])
        )

    elif data == "excuse_crown":
        if not s["excuses"]:
            await q.answer("No excuses!", show_alert=True); return
        top = max(s["excuses"], key=lambda x: x["votes"])
        add_points(s, top["author"], 2)
        await q.edit_message_text(
            f"🥇 <b>EXCUSE OLYMPICS GOLD MEDAL!</b>\n\n"
            f"<b>{top['author']}</b> wins with:\n\"{top['text']}\"\n"
            f"🥇 {top['votes']} votes | +2 points!\n\n" + lb_text(s),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]])
        )

    # ══════════════════════════════════════════
    # 🌶️ HOT TAKES
    # ══════════════════════════════════════════
    elif data == "ht_menu":
        lines = ["🌶️ <b>HOT TAKES STADIUM</b>\n"]
        if s["hot_takes"]:
            lines.append(f"<i>{len(s['hot_takes'])} takes submitted</i>\n")
            for h in s["hot_takes"][-3:]:
                lines.append(f'"{h["text"]}"\n— {h["author"]} | ✅{h["agree"]} ❌{h["disagree"]}\n')
        else:
            lines.append("<i>No hot takes yet!</i>")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌶️ Submit My Take", callback_data="ht_submit"),
             InlineKeyboardButton("🎲 Random Take", callback_data="ht_random")],
            [InlineKeyboardButton("🗳️ Vote on Takes", callback_data="ht_vote_list"),
             InlineKeyboardButton("👑 Crown Controversial (+3pts)", callback_data="ht_crown")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="ht_menu"),
             InlineKeyboardButton("⬅️ Back", callback_data="main")],
        ])
        await q.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=kb)

    elif data == "ht_submit":
        s["awaiting"] = "hot_take"
        s["awaiting_author"] = name
        await q.edit_message_text(
            "🌶️ <b>HOT TAKES</b>\n\nDrop your spiciest opinion in the chat right now! 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="ht_menu")]])
        )

    elif data == "ht_random":
        ht = random.choice(HOT_TAKES)
        s["hot_takes"].append({"author": name, "text": ht, "agree": 0, "disagree": 0, "id": len(s["hot_takes"])})
        idx = len(s["hot_takes"]) - 1
        await q.edit_message_text(
            f"🌶️ <b>HOT TAKE SUBMITTED!</b>\n\n\"{ht}\"\n— {name}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"✅ Agree (0)", callback_data=f"ht_agree_{idx}"),
                 InlineKeyboardButton(f"❌ Disagree (0)", callback_data=f"ht_disagree_{idx}")],
                [InlineKeyboardButton("⬅️ Back", callback_data="ht_menu")],
            ])
        )

    elif data == "ht_vote_list":
        if not s["hot_takes"]:
            await q.answer("No hot takes yet!", show_alert=True); return
        lines = ["🌶️ <b>VOTE — HOT TAKES</b>\n"]
        btn_rows = []
        for i, h in enumerate(s["hot_takes"]):
            lines.append(f"{i+1}. \"{h['text']}\"\n   — {h['author']} | ✅{h['agree']} ❌{h['disagree']}\n")
            btn_rows.append([
                InlineKeyboardButton(f"✅ #{i+1}", callback_data=f"ht_agree_{i}"),
                InlineKeyboardButton(f"❌ #{i+1}", callback_data=f"ht_disagree_{i}"),
            ])
        btn_rows.append([InlineKeyboardButton("⬅️ Back", callback_data="ht_menu")])
        await q.edit_message_text("\n".join(lines), parse_mode="HTML",
                                   reply_markup=InlineKeyboardMarkup(btn_rows))

    elif data.startswith("ht_agree_"):
        idx = int(data.split("_")[-1])
        if idx < len(s["hot_takes"]):
            s["hot_takes"][idx]["agree"] += 1
            await q.answer("✅ Agreed!")
            h = s["hot_takes"][idx]
            await q.edit_message_text(
                f"🌶️ \"{h['text']}\"\n— {h['author']}\n\n✅ {h['agree']} agree | ❌ {h['disagree']} disagree",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"✅ Agree ({h['agree']})", callback_data=f"ht_agree_{idx}"),
                     InlineKeyboardButton(f"❌ Disagree ({h['disagree']})", callback_data=f"ht_disagree_{idx}")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="ht_vote_list")],
                ])
            )

    elif data.startswith("ht_disagree_"):
        idx = int(data.split("_")[-1])
        if idx < len(s["hot_takes"]):
            s["hot_takes"][idx]["disagree"] += 1
            await q.answer("❌ Disagreed!")
            h = s["hot_takes"][idx]
            await q.edit_message_text(
                f"🌶️ \"{h['text']}\"\n— {h['author']}\n\n✅ {h['agree']} agree | ❌ {h['disagree']} disagree",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"✅ Agree ({h['agree']})", callback_data=f"ht_agree_{idx}"),
                     InlineKeyboardButton(f"❌ Disagree ({h['disagree']})", callback_data=f"ht_disagree_{idx}")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="ht_vote_list")],
                ])
            )

    elif data == "ht_crown":
        if not s["hot_takes"]:
            await q.answer("No hot takes!", show_alert=True); return
        top = max(s["hot_takes"], key=lambda h: h["agree"] + h["disagree"])
        add_points(s, top["author"], 3)
        await q.edit_message_text(
            f"👑 <b>MOST CONTROVERSIAL PLAYER!</b>\n\n"
            f"<b>{top['author']}</b> wins with:\n\"{top['text']}\"\n"
            f"✅{top['agree']} agree | ❌{top['disagree']} disagree\n+3 points!\n\n" + lb_text(s),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]])
        )

    # ══════════════════════════════════════════
    # 📖 STORY BUILDER
    # ══════════════════════════════════════════
    elif data == "story_menu":
        lines = ["📖 <b>STORY BUILDER</b>\n"]
        if s["story"]:
            lines.append("<i>The story so far:</i>\n")
            full = " ".join(x["sentence"] for x in s["story"])
            lines.append(full[:600] + ("..." if len(full) > 600 else ""))
            lines.append(f"\n\n<i>{len(s['story'])} sentences by {len(set(x['author'] for x in s['story']))} authors</i>")
        else:
            lines.append("<i>Story not started yet!</i>")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✍️ Add a Sentence", callback_data="story_add"),
             InlineKeyboardButton("🌟 New Story Starter", callback_data="story_new")],
            [InlineKeyboardButton("😂 Vote Funniest Line (+1pt)", callback_data="story_funny"),
             InlineKeyboardButton("📜 Read Full Story", callback_data="story_read")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="story_menu"),
             InlineKeyboardButton("⬅️ Back", callback_data="main")],
        ])
        await q.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=kb)

    elif data == "story_add":
        s["awaiting"] = "story_line"
        s["awaiting_author"] = name
        ctx_text = ""
        if s["story"]:
            last = s["story"][-1]["sentence"]
            ctx_text = f"\n\nLast line: <i>\"{last}\"</i>"
        await q.edit_message_text(
            f"📖 <b>STORY BUILDER</b>{ctx_text}\n\nNow add YOUR sentence to continue the story! 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="story_menu")]])
        )

    elif data == "story_new":
        starter = random.choice(STORY_STARTERS)
        s["story"] = [{"author": "📖 Narrator", "sentence": starter}]
        await q.edit_message_text(
            f"🌟 <b>NEW STORY STARTED!</b>\n\n<i>\"{starter}\"</i>\n\nNow add a sentence!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✍️ Add a Sentence", callback_data="story_add"),
                 InlineKeyboardButton("⬅️ Back", callback_data="story_menu")],
            ])
        )

    elif data == "story_funny":
        if not s["story"]:
            await q.answer("No story yet!", show_alert=True); return
        real = [x for x in s["story"] if x["author"] != "📖 Narrator"]
        if not real:
            await q.answer("No player sentences yet!", show_alert=True); return
        last = real[-1]
        add_points(s, last["author"], 1)
        await q.answer(f"😂 +1pt to {last['author']}!")
        await q.edit_message_text(
            f"😂 <b>FUNNIEST LINE AWARD!</b>\n\n"
            f"<b>{last['author']}</b> gets +1pt for:\n\"{last['sentence']}\"",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="story_menu")]])
        )

    elif data == "story_read":
        if not s["story"]:
            await q.answer("No story yet!", show_alert=True); return
        full = " ".join(f"{x['sentence']}" for x in s["story"])
        await q.edit_message_text(
            f"📜 <b>THE FULL STORY</b>\n\n{full[:3000]}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="story_menu")]])
        )

    # ══════════════════════════════════════════
    # 📣 SCREAM VOID
    # ══════════════════════════════════════════
    elif data == "void_menu":
        lines = ["📣 <b>SCREAM INTO THE VOID</b>\n"]
        if s["screams"]:
            lines.append(f"<i>{len(s['screams'])} screams in the void</i>\n")
            for sc in s["screams"][-3:]:
                lines.append(f'"{sc["text"]}"\n— {sc["author"]}\n')
        else:
            lines.append("<i>The void is empty... 👁️</i>")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📣 SCREAM!", callback_data="void_scream"),
             InlineKeyboardButton("😂 React to Screams", callback_data="void_react_list")],
            [InlineKeyboardButton("👑 Crown Loudest Screamer (+1pt)", callback_data="void_crown")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="void_menu"),
             InlineKeyboardButton("⬅️ Back", callback_data="main")],
        ])
        await q.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=kb)

    elif data == "void_scream":
        s["awaiting"] = "scream"
        s["awaiting_author"] = name
        await q.edit_message_text(
            "📣 <b>SCREAM INTO THE VOID</b>\n\nType your frustration, rant, or anything in the chat RIGHT NOW! 👇\n\nThe void hears all! 👁️",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="void_menu")]])
        )

    elif data == "void_react_list":
        if not s["screams"]:
            await q.answer("No screams yet!", show_alert=True); return
        lines = ["📣 <b>REACT TO SCREAMS</b>\n"]
        btn_rows = []
        reactions = ["😂","💀","😭","🔥","💥"]
        for i, sc in enumerate(s["screams"][-5:]):
            real_i = len(s["screams"]) - 5 + i
            if real_i < 0: continue
            lines.append(f"{i+1}. \"{sc['text'][:60]}...\"\n— {sc['author']}\n")
            btn_rows.append([InlineKeyboardButton(f"{r} #{i+1}", callback_data=f"void_react_{real_i}_{r}") for r in reactions[:3]])
        btn_rows.append([InlineKeyboardButton("⬅️ Back", callback_data="void_menu")])
        await q.edit_message_text("\n".join(lines), parse_mode="HTML",
                                   reply_markup=InlineKeyboardMarkup(btn_rows))

    elif data.startswith("void_react_"):
        parts = data.split("_")
        emoji = parts[-1]
        await q.answer(f"{emoji} Reacted!")

    elif data == "void_crown":
        if not s["screams"]:
            await q.answer("No screams!", show_alert=True); return
        counts = {}
        for sc in s["screams"]:
            counts[sc["author"]] = counts.get(sc["author"], 0) + 1
        valid = {k: v for k, v in counts.items() if k in s["scores"]}
        if not valid:
            await q.answer("No valid players!", show_alert=True); return
        winner = max(valid, key=lambda k: valid[k])
        add_points(s, winner, 1)
        await q.edit_message_text(
            f"📣 <b>LOUDEST SCREAMER AWARD!</b>\n\n"
            f"<b>{winner}</b> screamed {valid[winner]} time(s)!\n+1 point!\n\n" + lb_text(s),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]])
        )

    # ══════════════════════════════════════════
    # 🔮 PREDICTIONS
    # ══════════════════════════════════════════
    elif data == "pred_menu":
        lines = ["🔮 <b>GROUP PREDICTION GAME</b>\n"]
        if s["predictions"]:
            for p2 in s["predictions"][-4:]:
                lines.append(f'"{p2["text"]}"\n— {p2["author"]} | {p2["status"]}\n')
        else:
            lines.append("<i>No predictions yet!</i>")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔮 Make a Prediction", callback_data="pred_submit"),
             InlineKeyboardButton("🎲 Random Prediction", callback_data="pred_random")],
            [InlineKeyboardButton("✅ Mark Correct (+3pts)", callback_data="pred_resolve_list"),
             InlineKeyboardButton("📋 All Predictions", callback_data="pred_list")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="pred_menu"),
             InlineKeyboardButton("⬅️ Back", callback_data="main")],
        ])
        await q.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=kb)

    elif data == "pred_submit":
        s["awaiting"] = "prediction"
        s["awaiting_author"] = name
        await q.edit_message_text(
            "🔮 <b>PREDICTIONS</b>\n\nType your prediction for the group in the chat right now! 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="pred_menu")]])
        )

    elif data == "pred_random":
        pred = random.choice(PREDICTIONS)
        s["predictions"].append({"author": name, "text": pred, "status": "🔮 Pending", "id": len(s["predictions"])})
        await q.edit_message_text(
            f"🔮 <b>PREDICTION SUBMITTED!</b>\n\n\"{pred}\"\n— {name}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Was Correct! (+3pts)", callback_data=f"pred_correct_{len(s['predictions'])-1}"),
                 InlineKeyboardButton("❌ Was Wrong", callback_data=f"pred_wrong_{len(s['predictions'])-1}")],
                [InlineKeyboardButton("⬅️ Back", callback_data="pred_menu")],
            ])
        )

    elif data == "pred_list":
        if not s["predictions"]:
            await q.answer("No predictions!", show_alert=True); return
        lines = ["🔮 <b>ALL PREDICTIONS</b>\n"]
        btn_rows = []
        for i, p2 in enumerate(s["predictions"]):
            lines.append(f"{i+1}. \"{p2['text']}\"\n   — {p2['author']} | {p2['status']}\n")
            if p2["status"] == "🔮 Pending":
                btn_rows.append([
                    InlineKeyboardButton(f"✅ #{i+1} Correct", callback_data=f"pred_correct_{i}"),
                    InlineKeyboardButton(f"❌ #{i+1} Wrong", callback_data=f"pred_wrong_{i}"),
                ])
        btn_rows.append([InlineKeyboardButton("⬅️ Back", callback_data="pred_menu")])
        await q.edit_message_text("\n".join(lines), parse_mode="HTML",
                                   reply_markup=InlineKeyboardMarkup(btn_rows))

    elif data == "pred_resolve_list":
        pending = [(i, p2) for i, p2 in enumerate(s["predictions"]) if p2["status"] == "🔮 Pending"]
        if not pending:
            await q.answer("No pending predictions!", show_alert=True); return
        lines = ["🔮 <b>RESOLVE PREDICTIONS</b>\n"]
        btn_rows = []
        for i, p2 in pending:
            lines.append(f"\"{p2['text']}\"\n— {p2['author']}\n")
            btn_rows.append([
                InlineKeyboardButton(f"✅ Correct! (+3pts)", callback_data=f"pred_correct_{i}"),
                InlineKeyboardButton(f"❌ Wrong", callback_data=f"pred_wrong_{i}"),
            ])
        btn_rows.append([InlineKeyboardButton("⬅️ Back", callback_data="pred_menu")])
        await q.edit_message_text("\n".join(lines), parse_mode="HTML",
                                   reply_markup=InlineKeyboardMarkup(btn_rows))

    elif data.startswith("pred_correct_"):
        idx = int(data.split("_")[-1])
        if idx < len(s["predictions"]):
            p2 = s["predictions"][idx]
            p2["status"] = "✅ Correct!"
            add_points(s, p2["author"], 3)
            await q.edit_message_text(
                f"✅ <b>PREDICTION CORRECT!</b>\n\n"
                f"<b>{p2['author']}</b> predicted:\n\"{p2['text']}\"\n\n"
                f"They were RIGHT! +3 points! 🎉\n\n" + lb_text(s),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]])
            )

    elif data.startswith("pred_wrong_"):
        idx = int(data.split("_")[-1])
        if idx < len(s["predictions"]):
            s["predictions"][idx]["status"] = "❌ Wrong"
            await q.answer("❌ Marked as wrong!")
        await q.edit_message_text(
            "❌ Prediction marked as wrong!\n\n" + lb_text(s),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="pred_menu")]])
        )

# ══════════════════════════════════════════
# TEXT MESSAGE HANDLER (for awaiting inputs)
# ══════════════════════════════════════════
async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    chat_id = update.effective_chat.id
    user = update.effective_user
    s = get_state(chat_id)
    name = get_name(s, user)
    text = update.message.text.strip()
    awaiting = s.get("awaiting")

    if not awaiting:
        return  # Not waiting for input, ignore

    author = s.get("awaiting_author", name)

    if awaiting == "roast_text":
        target = s.get("awaiting_target", "someone")
        s["roasts"].append({"author": author, "target": target, "text": text, "votes": 0, "id": len(s["roasts"])})
        idx = len(s["roasts"]) - 1
        s["awaiting"] = None
        await update.message.reply_html(
            f"🔥 <b>ROAST SUBMITTED!</b>\n\n"
            f"<b>{author}</b> roasts <b>{target}</b>:\n\"{text}\"",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🔥 Vote this Fire! (0)", callback_data=f"roast_vote_{idx}"),
                 InlineKeyboardButton("⬅️ Back to Roasts", callback_data="roast_menu")],
            ])
        )

    elif awaiting == "dumb_q":
        s["dumb_qs"].append({"author": author, "q": text, "votes": 0, "id": len(s["dumb_qs"])})
        idx = len(s["dumb_qs"]) - 1
        s["awaiting"] = None
        await update.message.reply_html(
            f"🧠 <b>DUMB QUESTION SUBMITTED!</b>\n\n\"{text}\"\n— {author}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🧠 Vote this Dumbest! (0)", callback_data=f"dumb_vote_{idx}"),
                 InlineKeyboardButton("⬅️ Back", callback_data="dumb_menu")],
            ])
        )

    elif awaiting == "excuse":
        s["excuses"].append({"author": author, "text": text, "votes": 0, "id": len(s["excuses"])})
        idx = len(s["excuses"]) - 1
        s["awaiting"] = None
        await update.message.reply_html(
            f"😴 <b>EXCUSE SUBMITTED!</b>\n\n\"{text}\"\n— {author}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🥇 Vote Best Excuse! (0)", callback_data=f"excuse_vote_{idx}"),
                 InlineKeyboardButton("⬅️ Back", callback_data="excuse_menu")],
            ])
        )

    elif awaiting == "hot_take":
        s["hot_takes"].append({"author": author, "text": text, "agree": 0, "disagree": 0, "id": len(s["hot_takes"])})
        idx = len(s["hot_takes"]) - 1
        s["awaiting"] = None
        await update.message.reply_html(
            f"🌶️ <b>HOT TAKE DROPPED!</b>\n\n\"{text}\"\n— {author}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Agree (0)", callback_data=f"ht_agree_{idx}"),
                 InlineKeyboardButton("❌ Disagree (0)", callback_data=f"ht_disagree_{idx}")],
                [InlineKeyboardButton("⬅️ Back", callback_data="ht_menu")],
            ])
        )

    elif awaiting == "story_line":
        s["story"].append({"author": author, "sentence": text})
        s["awaiting"] = None
        full = " ".join(x["sentence"] for x in s["story"])
        await update.message.reply_html(
            f"📖 <b>SENTENCE ADDED!</b>\n\n{author}: <i>\"{text}\"</i>\n\n"
            f"Story length: {len(s['story'])} sentences",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✍️ Add Another", callback_data="story_add"),
                 InlineKeyboardButton("📜 Read Story", callback_data="story_read")],
                [InlineKeyboardButton("😂 Funniest Line (+1pt)", callback_data="story_funny"),
                 InlineKeyboardButton("⬅️ Back", callback_data="story_menu")],
            ])
        )

    elif awaiting == "scream":
        s["screams"].append({"author": author, "text": text})
        s["awaiting"] = None
        await update.message.reply_html(
            f"📣 <b>SCREAMED INTO THE VOID!</b>\n\n👁️ <i>\"{text}\"</i>\n\n— {author}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("😂", callback_data="void_react_0_😂"),
                 InlineKeyboardButton("💀", callback_data="void_react_0_💀"),
                 InlineKeyboardButton("🔥", callback_data="void_react_0_🔥"),
                 InlineKeyboardButton("💥", callback_data="void_react_0_💥"),
                 InlineKeyboardButton("😭", callback_data="void_react_0_😭")],
                [InlineKeyboardButton("📣 Scream Again", callback_data="void_scream"),
                 InlineKeyboardButton("⬅️ Back", callback_data="void_menu")],
            ])
        )

    elif awaiting == "prediction":
        s["predictions"].append({"author": author, "text": text, "status": "🔮 Pending", "id": len(s["predictions"])})
        idx = len(s["predictions"]) - 1
        s["awaiting"] = None
        await update.message.reply_html(
            f"🔮 <b>PREDICTION SUBMITTED!</b>\n\n\"{text}\"\n— {author}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Was Correct! (+3pts)", callback_data=f"pred_correct_{idx}"),
                 InlineKeyboardButton("❌ Was Wrong", callback_data=f"pred_wrong_{idx}")],
                [InlineKeyboardButton("⬅️ Back", callback_data="pred_menu")],
            ])
        )

# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════
def main():
    if not BOT_TOKEN:
        print("=" * 50)
        print("⚠️  ERROR: BOT_TOKEN environment variable not set!")
        print("   In Render dashboard → Environment → Add BOT_TOKEN")
        print("=" * 50)
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("join", cmd_join))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("lb", cmd_lb))
    app.add_handler(CommandHandler("leaderboard", cmd_lb))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("=" * 50)
    print("🏟️  CHAOS ARENA BOT IS RUNNING!")
    print("   Add your bot to a Telegram group")
    print("   and send /start to begin!")
    print("   Press Ctrl+C to stop.")
    print("=" * 50)

    app.run_polling()

if __name__ == "__main__":
    main()
