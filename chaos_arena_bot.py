import os
import json
import random
import time
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.environ.get("BOT_TOKEN","")
DATA_FILE = "chaos_data.json"

START_COINS = 100
DAILY_REWARD = 50
BANK_INTEREST = 0.02

# =========================
# LOGGING
# =========================

logging.basicConfig(level=logging.INFO)

# =========================
# DATABASE
# =========================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE,"r") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE,"w") as f:
        json.dump(state,f,indent=2)

state = load_data()

# =========================
# HELPERS
# =========================

def medals(i):
    if i==0: return "🥇"
    if i==1: return "🥈"
    if i==2: return "🥉"
    return f"#{i+1}"

def get_chat(chat_id):

    chat_id=str(chat_id)

    if chat_id not in state:

        state[chat_id]={"players":{}, "boss":None}

    return state[chat_id]

def get_player(chat,user):

    uid=str(user.id)

    if uid not in chat["players"]:

        chat["players"][uid]={

        "name":user.first_name,
        "points":0,
        "coins":START_COINS,
        "xp":0,
        "level":1,
        "bank":0,
        "inventory":[],
        "memes":0,
        "last_daily":0

        }

    return chat["players"][uid]

# =========================
# LEADERBOARD
# =========================

def leaderboard(chat):

    players=list(chat["players"].values())

    players.sort(key=lambda x:x["points"],reverse=True)

    text="🏆 LEADERBOARD\n\n"

    for i,p in enumerate(players):

        text+=f"{medals(i)} {p['name']} — {p['points']} pts\n"

    return text

async def global_lb(update,ctx):

    players=[]

    for chat in state.values():
        players.extend(chat["players"].values())

    players.sort(key=lambda x:x["points"],reverse=True)

    text="🌍 GLOBAL LEADERBOARD\n\n"

    for i,p in enumerate(players[:10]):

        text+=f"{i+1}. {p['name']} — {p['points']} pts\n"

    await update.message.reply_text(text)

# =========================
# DAILY REWARD
# =========================

def claim_daily(player):

    now=time.time()

    if now-player["last_daily"] < 86400:
        return False

    player["coins"] += DAILY_REWARD

    player["last_daily"] = now

    return True

# =========================
# DARES
# =========================

DARES=[
"Speak only emojis for 3 messages",
"Send a cursed meme",
"Change profile pic to potato 🥔",
"Type backwards once",
"Sing a line from a song"
]

# =========================
# CASINO
# =========================

async def slots(update,ctx):

    chat=get_chat(update.effective_chat.id)
    player=get_player(chat,update.effective_user)

    icons=["🍒","💎","7️⃣","⭐","🍋"]

    r=[random.choice(icons) for _ in range(3)]

    if r[0]==r[1]==r[2]:

        reward=50
        player["coins"]+=reward
        msg=f"🎰 {' '.join(r)}\nJackpot! +{reward} coins"

    elif r[0]==r[1] or r[1]==r[2]:

        reward=15
        player["coins"]+=reward
        msg=f"🎰 {' '.join(r)}\nNice! +{reward} coins"

    else:
        msg=f"🎰 {' '.join(r)}\nNo win"

    save_data()

    await update.message.reply_text(msg)

async def blackjack(update,ctx):

    cards=[2,3,4,5,6,7,8,9,10,10,10,11]

    player_score=random.choice(cards)+random.choice(cards)
    dealer=random.choice(cards)+random.choice(cards)

    chat=get_chat(update.effective_chat.id)
    player=get_player(chat,update.effective_user)

    if player_score>21:

        player["coins"]-=10
        msg="Bust! -10 coins"

    elif dealer>21 or player_score>dealer:

        player["coins"]+=30
        msg="You win +30 coins"

    else:

        player["coins"]-=10
        msg="Dealer wins"

    save_data()

    await update.message.reply_text(
        f"You:{player_score} Dealer:{dealer}\n{msg}"
    )

# =========================
# ROULETTE
# =========================

async def roulette(update,ctx):

    if not ctx.args:
        await update.message.reply_text("Use /roulette number")
        return

    bet=int(ctx.args[0])

    spin=random.randint(0,36)

    chat=get_chat(update.effective_chat.id)
    player=get_player(chat,update.effective_user)

    if spin==bet:

        player["coins"]+=100
        msg=f"Spin {spin} — WIN +100"

    else:

        player["coins"]-=10
        msg=f"Spin {spin} — lost"

    save_data()

    await update.message.reply_text(msg)

# =========================
# LOOT BOX
# =========================

LOOT_TABLE=[

("coins",20),
("coins",50),
("coins",100),
("points",5),
("points",10)

]

async def loot(update,ctx):

    chat=get_chat(update.effective_chat.id)
    player=get_player(chat,update.effective_user)

    if player["coins"]<25:

        await update.message.reply_text("Need 25 coins")
        return

    player["coins"]-=25

    reward=random.choice(LOOT_TABLE)

    if reward[0]=="coins":

        player["coins"]+=reward[1]
        msg=f"🎁 Loot: {reward[1]} coins"

    else:

        player["points"]+=reward[1]
        msg=f"🎁 Loot: {reward[1]} points"

    save_data()

    await update.message.reply_text(msg)

# =========================
# BANK
# =========================

async def deposit(update,ctx):

    amount=int(ctx.args[0])

    chat=get_chat(update.effective_chat.id)
    player=get_player(chat,update.effective_user)

    if player["coins"]<amount:

        await update.message.reply_text("Not enough coins")
        return

    player["coins"]-=amount
    player["bank"]+=amount

    save_data()

    await update.message.reply_text(f"Deposited {amount}")

async def withdraw(update,ctx):

    amount=int(ctx.args[0])

    chat=get_chat(update.effective_chat.id)
    player=get_player(chat,update.effective_user)

    if player["bank"]<amount:

        await update.message.reply_text("Not enough in bank")
        return

    player["bank"]-=amount
    player["coins"]+=amount

    save_data()

    await update.message.reply_text(f"Withdrew {amount}")

# =========================
# SHOP
# =========================

SHOP={

"vip":200,
"sword":300,
"ticket":100

}

async def shop(update,ctx):

    text="🪙 SHOP\n\n"

    for item,price in SHOP.items():
        text+=f"{item} — {price} coins\n"

    await update.message.reply_text(text)

async def buy(update,ctx):

    item=ctx.args[0]

    chat=get_chat(update.effective_chat.id)
    player=get_player(chat,update.effective_user)

    if item not in SHOP:

        await update.message.reply_text("Item not found")
        return

    price=SHOP[item]

    if player["coins"]<price:

        await update.message.reply_text("Not enough coins")
        return

    player["coins"]-=price
    player["inventory"].append(item)

    save_data()

    await update.message.reply_text(f"Bought {item}")

# =========================
# MEME WAR
# =========================

async def meme(update,ctx):

    chat=get_chat(update.effective_chat.id)
    player=get_player(chat,update.effective_user)

    score=random.randint(1,10)

    player["points"]+=score

    save_data()

    await update.message.reply_text(
        f"🎭 Meme Score {score}"
    )

# =========================
# MINI GAMES
# =========================

GAMES=[

("Coin Flip", lambda: random.choice(["Heads","Tails"])),

("Dice Roll", lambda: f"You rolled {random.randint(1,6)}"),

("Magic 8 Ball", lambda: random.choice(["Yes","No","Maybe"]))

]

async def play(update,ctx):

    g=random.choice(GAMES)

    await update.message.reply_text(
        f"🎮 {g[0]}\n{g[1]()}"
    )

# =========================
# BOSS
# =========================

BOSSES=[

{"name":"Chaos Goblin","hp":100,"reward":50},
{"name":"Meme Dragon","hp":200,"reward":100}

]

async def boss(update,ctx):

    chat=get_chat(update.effective_chat.id)

    chat["boss"]=random.choice(BOSSES).copy()

    save_data()

    await update.message.reply_text(
        f"🧟 Boss Appeared\n{chat['boss']['name']}\nHP:{chat['boss']['hp']}"
    )

async def attack(update,ctx):

    chat=get_chat(update.effective_chat.id)

    if not chat["boss"]:
        await update.message.reply_text("No boss")
        return

    dmg=random.randint(10,30)

    chat["boss"]["hp"]-=dmg

    if chat["boss"]["hp"]<=0:

        reward=chat["boss"]["reward"]

        player=get_player(chat,update.effective_user)

        player["coins"]+=reward

        chat["boss"]=None

        msg=f"Boss defeated! +{reward} coins"

    else:

        msg=f"Damage {dmg}\nHP {chat['boss']['hp']}"

    save_data()

    await update.message.reply_text(msg)

# =========================
# START / MENU
# =========================

async def start(update:Update,ctx:ContextTypes.DEFAULT_TYPE):

    chat=get_chat(update.effective_chat.id)
    get_player(chat,update.effective_user)

    save_data()

    kb=InlineKeyboardMarkup([

    [InlineKeyboardButton("🎯 Dare",callback_data="dare")],
    [InlineKeyboardButton("🏆 Leaderboard",callback_data="lb")],
    [InlineKeyboardButton("🎁 Daily Reward",callback_data="daily")]

    ])

    await update.message.reply_text(
        "🏟️ CHAOS ARENA PRO",
        reply_markup=kb
    )

# =========================
# CALLBACK
# =========================

async def callback(update:Update,ctx:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    chat=get_chat(q.message.chat_id)
    player=get_player(chat,q.from_user)

    if q.data=="lb":

        await q.edit_message_text(
            leaderboard(chat)
        )

    if q.data=="dare":

        dare=random.choice(DARES)

        player["points"]+=2

        save_data()

        await q.edit_message_text(
            f"🎯 Dare\n\n{dare}"
        )

    if q.data=="daily":

        if claim_daily(player):

            save_data()

            await q.edit_message_text("Daily reward claimed!")

        else:

            await q.edit_message_text("Already claimed today")

# =========================
# MESSAGE XP
# =========================

async def message(update:Update,ctx:ContextTypes.DEFAULT_TYPE):

    chat=get_chat(update.effective_chat.id)
    player=get_player(chat,update.effective_user)

    player["xp"]+=2

    save_data()

# =========================
# MAIN
# =========================

def main():

    app=ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",start))

    app.add_handler(CommandHandler("slots",slots))
    app.add_handler(CommandHandler("blackjack",blackjack))
    app.add_handler(CommandHandler("roulette",roulette))

    app.add_handler(CommandHandler("loot",loot))

    app.add_handler(CommandHandler("deposit",deposit))
    app.add_handler(CommandHandler("withdraw",withdraw))

    app.add_handler(CommandHandler("shop",shop))
    app.add_handler(CommandHandler("buy",buy))

    app.add_handler(CommandHandler("meme",meme))
    app.add_handler(CommandHandler("play",play))

    app.add_handler(CommandHandler("boss",boss))
    app.add_handler(CommandHandler("attack",attack))

    app.add_handler(CommandHandler("global",global_lb))

    app.add_handler(CallbackQueryHandler(callback))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,message))

    print("🏟️ Chaos Arena PRO Running")

    app.run_polling()

if __name__=="__main__":
    main()
