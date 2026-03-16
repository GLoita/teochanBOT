import discord
from discord.ext import commands, tasks
import json
import asyncio
from datetime import datetime, timedelta
from datetime import datetime, timedelta, timezone
JST = timezone(timedelta(hours=9))

import os

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1482033547358507111
MENTION_TEXT = "@everyone"

DATA_FILE = "data.json"

FEED_INTERVAL = 12 * 60 * 60
WATER_INTERVAL = 48 * 60 * 60

async def send_control_panel(channel):

    await channel.send(
        "🐶 犬のお世話管理",
        view=DogCareView()
    )

def format_time(t):
    if t is None:
        return "記録なし"

    dt = parse_time(t)
    return dt.astimezone(JST).strftime("%Y/%m/%d %H:%M")

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "last_feed": None,
            "last_water": None,
            "last_walk": None
        }


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


data = load_data()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def parse_time(t):
    if t is None:
        return None
    return datetime.fromisoformat(t)


def time_since(t):
    if t is None:
        return None
    return  datetime.now(JST)- parse_time(t)


def next_feed():
    if data["last_feed"] is None:
        return None
    return parse_time(data["last_feed"]) + timedelta(hours=12)


class DogCareView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="ご飯をあげた", style=discord.ButtonStyle.green)
    async def feed(self, interaction: discord.Interaction, button: discord.ui.Button):

        data["last_feed"] = datetime.now(JST).isoformat()
        save_data(data)

        await interaction.response.send_message("🐶 ご飯を記録しました", ephemeral=True)

    @discord.ui.button(label="水を交換した", style=discord.ButtonStyle.blurple)
    async def water(self, interaction: discord.Interaction, button: discord.ui.Button):

        data["last_water"] = datetime.now(JST).isoformat()
        save_data(data)

        await interaction.response.send_message("💧 水交換を記録しました", ephemeral=True)

    @discord.ui.button(label="散歩に行った", style=discord.ButtonStyle.gray)
    async def walk(self, interaction: discord.Interaction, button: discord.ui.Button):

        data["last_walk"] = datetime.now(JST).isoformat()
        save_data(data)

        await interaction.response.send_message("🐕 散歩を記録しました", ephemeral=True)

@discord.ui.button(label="次のご飯時間", style=discord.ButtonStyle.secondary)
async def nextmeal(self, interaction: discord.Interaction, button: discord.ui.Button):

    if data["last_feed"] is None:
        msg = "まだご飯の記録がありません"
    else:
        last = parse_time(data["last_feed"])
        now = datetime.now()

        since = now - last
        next_time = last + timedelta(hours=12)
        remaining = next_time - now

        # 時間計算
        since_h = since.seconds // 3600
        since_m = (since.seconds % 3600) // 60

        rem_h = remaining.seconds // 3600
        rem_m = (remaining.seconds % 3600) // 60

        next_clock = next_time.strftime("%H:%M")

        since_h = since.seconds // 3600
        since_m = (since.seconds % 3600) // 60

        rem_h = remaining.seconds // 3600
        rem_m = (remaining.seconds % 3600) // 60

        next_clock = next_time.strftime("%H:%M")

        label = "今日"
        if next_time.date() > now.date():
            label = "明日"

        msg = (
            f"🐶 次のご飯\n"
            f"{label}：{next_clock} ({rem_h}時間{rem_m}分後)\n"
            f"最後のご飯：{since_h}時間{since_m}分前"
        )

    await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(label="ログ", style=discord.ButtonStyle.red)
    async def log(self, interaction: discord.Interaction, button: discord.ui.Button):

        msg = "🐶お世話ログ\n\n"

        if data["last_feed"]:
            msg += f"最後のご飯\n{format_time(data['last_feed'])}\n\n"

        if data["last_water"]:
            msg += f"最後の水交換\n{format_time(data['last_water'])}\n\n"

        if data["last_walk"]:
            msg += f"最後の散歩\n{format_time(data['last_walk'])}\n"

        await interaction.response.send_message(msg, ephemeral=False)

        channel = interaction.channel
        await send_control_panel(channel)


@bot.event
async def on_ready():
    print("BOT起動")

    channel = bot.get_channel(CHANNEL_ID)

    await channel.send(
        "🐶 ておちゃんお世話管理",
        view=DogCareView()
    )

    check_tasks.start()


@tasks.loop(minutes=1)
async def check_tasks():

    channel = bot.get_channel(CHANNEL_ID)

    now = datetime.now(JST)

    if data["last_feed"]:

        last_feed = parse_time(data["last_feed"])

        if now - last_feed > timedelta(hours=12):

            await channel.send(f"{MENTION_TEXT} 🐶お腹すいたー")
            await send_control_panel(channel)

            data["last_feed"] = now.isoformat()
            save_data(data)

    if data["last_water"]:

        last_water = parse_time(data["last_water"])

        if now - last_water > timedelta(hours=48):

            await channel.send(f"{MENTION_TEXT} 💧お水みてー")
            await send_control_panel(channel)

            data["last_water"] = now.isoformat()
            save_data(data)


bot.run(TOKEN)
