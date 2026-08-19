# -*- coding: utf-8 -*-
"""
Discord Invite Giveaway Bot
---------------------------
Ngitung berapa temen yang di-undang tiap member ke server. 1 undangan = 1 poin.
Pas nyampe INVITE_GOAL (default 10), bot ngasih tau hadiahnya.

Cara jalan: .venv/Scripts/python bot.py
Perlu permission bot: Manage Server (baca invite) + Members intent ON.
"""

import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from tracker import InviteTracker

load_dotenv()

logging.basicConfig(
    filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("invite-bot")

TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
GOAL = int(os.getenv("INVITE_GOAL", 10))
REWARD_TEXT = os.getenv("REWARD_TEXT", "klaim hadiah ke owner")
REWARD_CHANNEL_ID = os.getenv("REWARD_CHANNEL_ID", "").strip()
STATE_FILE = os.getenv("STATE_FILE", "invite_state.json")

intents = discord.Intents.default()
intents.guilds = True        # baca daftar invite guild
intents.members = True       # tau siapa yang join (PRIVILEGED - nyalain di portal)

bot = commands.Bot(command_prefix="!", intents=intents)
tracker = InviteTracker(STATE_FILE)


def _invite_rows(invites):
    return [(i.code, i.inviter.id if i.inviter else None, i.uses) for i in invites]


async def refresh_snapshot(guild):
    try:
        invites = await guild.invites()
    except discord.Forbidden:
        log.warning(f"[{guild.name}] Gak bisa baca invite - kasih permission Manage Server ke bot.")
        return False
    tracker.snapshot_invites(guild.id, _invite_rows(invites))
    return True


@bot.event
async def on_ready():
    log.info(f"Login sebagai {bot.user} (ID {bot.user.id})")
    for guild in bot.guilds:
        ok = await refresh_snapshot(guild)
        log.info(f"  [{guild.name}] snapshot invite: {'OK' if ok else 'GAGAL'}")
    try:
        synced = await bot.tree.sync()
        log.info(f"Slash command tersync: {len(synced)}")
    except Exception as e:
        log.error(f"Sync slash command gagal: {e}")


@bot.event
async def on_member_join(member):
    guild = member.guild
    try:
        fresh = await guild.invites()
    except discord.Forbidden:
        return
    inviter_id, code = tracker.find_inviter(
        guild.id, _invite_rows(fresh)
    )
    await refresh_snapshot(guild)

    if inviter_id and str(inviter_id) != str(member.id):
        count = tracker.record(guild.id, inviter_id)
        inviter = guild.get_member(int(inviter_id))
        log.info(f"[{guild.name}] {member} join via {code} dari {inviter} - progres {count}/{GOAL}")
        if count >= GOAL:
            await announce_reward(guild, inviter, count)


async def announce_reward(guild, inviter, count):
    msg = (
        f"Selamat {inviter.mention}! Lu udah ngundang {count} orang, "
        f"target {GOAL} tercapai. Hadiah: {REWARD_TEXT}"
    )
    if REWARD_CHANNEL_ID:
        ch = guild.get_channel(int(REWARD_CHANNEL_ID))
        if ch is not None:
            await ch.send(msg)
            return
    try:
        await inviter.send(msg)
    except discord.Forbidden:
        for ch in guild.text_channels:
            if ch.permissions_for(guild.me).send_messages:
                await ch.send(msg)
                return


def _progress_bar(count):
    filled = min(count, GOAL)
    return "[" + "=" * filled + "-" * (GOAL - filled) + "]"


@bot.tree.command(name="invite", description="Cek progres undangan giveaway")
async def invite_progress(interaction: discord.Interaction):
    count = tracker.progress(interaction.guild_id, interaction.user.id)
    remaining = max(GOAL - count, 0)
    text = (
        f"Progres undangan lu: {count}/{GOAL}\n"
        f"{_progress_bar(count)}\n"
        f"Tinggal {remaining} undangan lagi buat dapet hadiah: {REWARD_TEXT}"
    )
    await interaction.response.send_message(text)


@bot.tree.command(name="invite_top", description="Top 10 pengundang terbanyak")
async def invite_top(interaction: discord.Interaction):
    lb = tracker.leaderboard(interaction.guild_id, 10)
    if not lb:
        await interaction.response.send_message("Belum ada yang ngundang.")
        return
    lines = []
    for rank, (uid, count) in enumerate(lb, 1):
        member = interaction.guild.get_member(int(uid))
        name = member.display_name if member else f"user {uid}"
        lines.append(f"{rank}. {name} - {count} undangan")
    await interaction.response.send_message("**Top pengundang:**\n" + "\n".join(lines))


if __name__ == "__main__":
    if not TOKEN:
        print("DISCORD_BOT_TOKEN kosong! Isi di .env dulu.")
        raise SystemExit(1)
    bot.run(TOKEN)