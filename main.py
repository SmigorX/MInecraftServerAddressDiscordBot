import requests
import discord

from configuration import bot_token, requestUri
from discord.ext import commands


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix="!")


@bot.hybrid_command(name='get_ip', description='Current ip of the minecraft server')
async def getIp(ctx):
    try:
        request = requests.get(requestUri).text
        public_url = request['tunnels'][0]['public_url'][6:]
        await ctx.send(public_url)
    except Exception:
        await ctx.send(":skull:")

@bot.event
async def on_ready():
    await bot.tree.sync()


bot.run(bot_token)
