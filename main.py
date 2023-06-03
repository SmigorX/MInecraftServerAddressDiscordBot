import requests
import discord
import asyncio

from configuration import bot_token, requestUri
from discord.ext import commands
from mcstatus import JavaServer


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix="!")

public_url = ""
presence = ""

async def status():
    try:
        response = requests.get(requestUri).json()
        print(response)
        public_url = response['tunnels'][0]['public_url'][6:]
    except Exception:
        public_url = None
    while True:
        if public_url is not None:
            try:
                server = JavaServer.lookup(public_url)
                status = server.status()
                status = server.status()
                presence = f" {status.players.online} player(s) online, latency {round(status.latency,2)} ms"
            except Exception:
                presence = "mcstatus not fetched :skull:"
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=presence))
        await asyncio.sleep(60)


@bot.hybrid_command(name='get_ip', description='Current ip of the minecraft server')
async def getIp(ctx):
    try:
        response = requests.get(requestUri).json()
        print(response)
        public_url = response['tunnels'][0]['public_url'][6:]
        await ctx.send(public_url, ephemeral=True)
    except Exception:
        await ctx.send("Failed miserably :skull:", ephemeral=True)


@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.loop.create_task(status())


bot.run(bot_token)
