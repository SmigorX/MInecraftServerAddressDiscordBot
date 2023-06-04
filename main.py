# builtins
import datetime, time
import logging
import os

from typing import Optional

# 3rd party imports
import requests
import discord

from discord import utils
from discord.ext import commands
from discord.ext.tasks import loop
from mcstatus import JavaServer

# modules
from configuration import debug


class ServerBot(commands.Bot):
    def __init__(self):
        self._bot_token = __import__("configuration").bot_token
        self._requestUri = __import__("configuration").requestUri

        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, command_prefix="!")

    @property
    def public_url(self):
        """
        Function to fetch public server url as class attribute

        :returns: public server url fetched from Ngrok, or None if server isn't live
        :rtype: Optional[str]
        """
        try:
            response = requests.get(self._requestUri).json()
            logging.debug(response)
            public_url = response['tunnels'][0]['public_url'][6:]
        # Catch exceptions signaling server not being live
        except (requests.exceptions.ConnectionError, KeyError, IndexError):
            return None
        return public_url


    def start_bot(self):
        self.run(self._bot_token)

    async def on_ready(self):
        """
        When bot connects to API add cog to its tree and sync it, then setup logging handler
        """
        self.setup_logging()

        await self.add_cog(ServerCog(self))
        logging.info(f"Synced new tree containing: {len(self.tree.get_commands())}")
        await self.tree.sync()

    async def on_error(self, event_method: str, *args) -> None:
        """
        Stores uncaught exception traceback in log
        """
        logging.exception("Reporting uncaught exception:")

    @staticmethod
    def setup_logging():
        """
        Creates new file for log, and sets it as default log handler
        """
        # Create dir for logs if it doesn't exist
        if not os.path.exists('./logs'):
            os.mkdir('./logs')

        # Creates new log file in ./logs named with current Unix timestamp
        handler = logging.FileHandler(
            f"./logs/MinecraftServerStatus_{time.mktime(datetime.datetime.utcnow().timetuple())}.log", "a+")
        utils.setup_logging(handler=handler, level=logging.DEBUG if debug else logging.INFO)


class ServerCog(commands.Cog):
    def __init__(self, bot: ServerBot):
        self.bot: ServerBot = bot
        self.status.start()

    @loop(minutes=10)
    async def status(self):
        """
        Loop updating discord RPC for bot

        Gets current server status using
        """
        try:
            server = JavaServer.lookup(self.bot.public_url)
            status = server.status()
            presence = f" {status.players.online} player(s) online, latency {round(status.latency, 2)} ms"
        except TypeError:  # Caught when public_url is unavailable
            presence = "Server unavailable :skull:"
        
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=presence))

    @status.before_loop
    async def status_setup(self):
        """
        Wait for bot to startup before starting loop
        """
        await self.bot.wait_until_ready()

    """
    Functions 'get' and 'getIp' are a workaround to get spaces in discord commands
    We create a group "get" that has only one command "ip" this works as if we had one command "get ip"
    """
    @commands.hybrid_group(name='get', description='Get information about')
    async def get(self, ctx):
        """
        Command group for getting servers current ip
        """
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command")

    @get.command(name='ip', description='Current IP of the minecraft server')
    async def getIp(self, ctx):
        """
        Command in a group for getting servers current ip
        """
        tmp = "We couldn't handle this :skull:"
        try:
            assert (tmp := self.bot.public_url)
            await ctx.send(tmp, ephemeral=True)
        except AssertionError:
            logging.exception("Catched exception:")
            tmp = "Failed miserably :skull:"
        finally:
            await ctx.send(tmp, ephemeral=True)


if __name__ == "__main__":
    bot = ServerBot()
    bot.start_bot()
