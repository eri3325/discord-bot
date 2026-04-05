import discord
from discord.ext import commands, tasks
import time
import datetime
import json
import os
from discord.ui import Button, View

# ===== 저장 / 불러오기 =====
def save_data():
    path = os.path.join(os.getcwd(), "data.json")
    with open(path, "w") as f:
        json.dump(study_totals, f, indent=4)

    print("🔥 저장됨:", study_totals)
    print("🔥 경로:", path)

def load_data():
    global study_totals
    path = os.path.join(os.getcwd(), "data.json")

    if not os.path.exists(path):
        print("파일 없음, 새로 시작")
        study_totals = {}
        return

    with open(path, "r") as f:
        try:
            data = json.load(f)
            study_totals = {str(k): int(v) for k, v in data.items()}
            print("불러옴:", study_totals)
        except:
            print("파일 비어있음")
            study_totals = {}

study_sessions = {}
study_totals = {}

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ===== 이벤트 =====
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    load_data()

# ===== 명령어 =====
@bot.command()
async def start(ctx):
    user_id = str(ctx.author.id)
    study_sessions[user_id] = time.time()

    print("🔥 START 저장됨:", study_sessions)
    await ctx.send("📚 공부 시작!")

@bot.command()
async def end(ctx):
    user_id = str(ctx.author.id)

    print("sessions:", study_sessions)
    print("user_id:", user_id)

    if user_id not in study_sessions:
        await ctx.send("❌ 먼저 !start 해주세요")
        return

    start_time = study_sessions.pop(user_id)
    elapsed = int(time.time() - start_time)

    if user_id not in study_totals:
        study_totals[user_id] = 0

    study_totals[user_id] += elapsed

    print("저장 직전:", study_totals)
    save_data()

    minutes = elapsed // 60
    await ctx.send(f"⏱ 공부 시간: {minutes}분")

@bot.command()
async def total(ctx):
    user_id = str(ctx.author.id)
    total_time = study_totals.get(user_id, 0)

    minutes = total_time // 60
    await ctx.send(f"📊 총 공부시간: {minutes}분")

# ===== 버튼 =====
@bot.command()
async def button(ctx):
    start_button = Button(label="📚 공부 시작", style=discord.ButtonStyle.green)
    end_button = Button(label="⏹ 공부 종료", style=discord.ButtonStyle.red)

    async def start_callback(interaction):
        user_id = str(interaction.user.id)
        study_sessions[user_id] = time.time()
        await interaction.response.send_message("📚 공부 시작!", ephemeral=True)

    async def end_callback(interaction):
        user_id = str(interaction.user.id)

        if user_id not in study_sessions:
            await interaction.response.send_message("❌ 먼저 시작하세요", ephemeral=True)
            return

        start_time = study_sessions.pop(user_id)
        elapsed = int(time.time() - start_time)

        if user_id not in study_totals:
            study_totals[user_id] = 0

        study_totals[user_id] += elapsed

        print("버튼 저장 직전:", study_totals)
        save_data()

        minutes = elapsed // 60
        await interaction.response.send_message(f"⏱ 공부 시간: {minutes}분", ephemeral=True)

    start_button.callback = start_callback
    end_button.callback = end_callback

    view = View()
    view.add_item(start_button)
    view.add_item(end_button)

    await ctx.send("📖 스터디 버튼", view=view)

# ===== 자동 랭킹 =====
@tasks.loop(minutes=1)
async def daily_rank():
    now = datetime.datetime.now()

    if now.minute == 0 and now.hour in [0, 12]:
        channel = bot.get_channel(TOKEN)

        if not study_totals:
            await channel.send("오늘 기록 없음")
            return

        sorted_users = sorted(study_totals.items(), key=lambda x: x[1], reverse=True)

        msg = "🏆 오늘의 공부 랭킹\n"

        for i, (user_id, t) in enumerate(sorted_users, 1):
            user = await bot.fetch_user(int(user_id))
            minutes = t // 60
            msg += f"{i}. {user.name} - {minutes}분\n"

        await channel.send(msg)

bot.run("TOKEN")