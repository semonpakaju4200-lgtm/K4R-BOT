import discord
from discord.ext import commands, tasks
import sqlite3
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("scrims.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    team_name TEXT,
    players TEXT,
    slot INTEGER,
    status TEXT
)
""")

conn.commit()

MAX_TEAMS = 16
scrim_active = False

# ---------------- EMBED ----------------
def create_embed():
    embed = discord.Embed(
        title="🎮 PRO SCRIMS",
        description="Live scrims registration",
        color=0x00ff00
    )

    c.execute("SELECT team_name, slot FROM teams WHERE status='accepted'")
    accepted = c.fetchall()

    for team, slot in accepted:
        embed.add_field(
            name=f"T{slot}",
            value=team,
            inline=False
        )

    c.execute("SELECT team_name FROM teams WHERE status='waitlist'")
    waitlist = c.fetchall()

    if waitlist:
        wait = "\n".join([x[0] for x in waitlist])
        embed.add_field(
            name="⏳ WAITLIST",
            value=wait,
            inline=False
        )

    return embed

# ---------------- OPEN SCRIMS ----------------
@bot.command()
async def openscrim(ctx):
    global scrim_active
    scrim_active = True
    await ctx.send("🟢 SCRIMS OPEN!")

# ---------------- CLOSE SCRIMS ----------------
@bot.command()
async def closescrim(ctx):
    global scrim_active
    scrim_active = False
    await ctx.send("🔴 SCRIMS CLOSED!")

# ---------------- REGISTER ----------------
@bot.command()
async def register(ctx, team_name, *, players):

    global scrim_active

    if not scrim_active:
        return await ctx.send("❌ Scrims closed")

    # DUPLICATE CHECK
    c.execute("SELECT * FROM teams WHERE user_id=?", (str(ctx.author.id),))
    exists = c.fetchone()

    if exists:
        return await ctx.send("❌ You already registered")

    # TEAM COUNT
    c.execute("SELECT COUNT(*) FROM teams WHERE status='accepted'")
    count = c.fetchone()[0]

    if count < MAX_TEAMS:
        slot = count + 1

        c.execute("""
        INSERT INTO teams
        (user_id, team_name, players, slot, status)
        VALUES (?, ?, ?, ?, ?)
        """, (
            str(ctx.author.id),
            team_name,
            players,
            slot,
            "accepted"
        ))

        conn.commit()

        await ctx.send(
            f"✅ {team_name} registered as T{slot}"
        )

    else:

        c.execute("""
        INSERT INTO teams
        (user_id, team_name, players, slot, status)
        VALUES (?, ?, ?, ?, ?)
        """, (
            str(ctx.author.id),
            team_name,
            players,
            0,
            "waitlist"
        ))

        conn.commit()

        await ctx.send(
            f"⏳ {team_name} added to waitlist"
        )

# ---------------- VIEW SCRIMS ----------------
@bot.command()
async def scrims(ctx):
    await ctx.send(embed=create_embed())

# ---------------- RESET ----------------
@bot.command()
async def reset(ctx):
    c.execute("DELETE FROM teams")
    conn.commit()
    await ctx.send("♻️ Scrims reset complete")

bot.run(TOKEN)
