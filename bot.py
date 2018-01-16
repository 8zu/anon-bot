import asyncio
import logging
import os.path as osp
import sys

from cache import Cache

try:
    from discord.ext import commands
    import discord
except ImportError:
    print("Discord.py is not installed.\n"
          "Consult the guide for your operating system "
          "and do ALL the steps in order.\n"
          "https://twentysix26.github.io/Red-Docs/\n")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger = logging.getLogger('ccbot')
logger.addHandler(handler)

description = """A bot to allow simple anonymous posting. Use at own risk!"""

def get_config(path):
    if osp.exists(path):
        config = pytoml.load(open(path, "r", encoding="UTF-8"))
    else:
        logger.error("Missing config file! Shutting down now...")
        sys.exit(1)

    if 'token' not in config or not config['token']:
        logger.error("Token is not filled in! Shutting down now...")
        sys.exit(1)

    return config

class AnonBot(commands.Bot):
    def __init__(self, cache):
        self.cache = cache
        self.initialized = not self.cache.load('saved_config.json').is_none()
        super().__init__(description=description, command_prefix='?')

    def is_command(self, cmd, s):
        return s.strip().split(' ')[0] == f"{self.command_prefix}{cmd}"

    async def initialize(self, channel, author):
        await self.send_message(channel, texts['ask_role'])
        role_user = await self.wait_for_message(author=author, channel=channel)
        print(role_user.content) # DEBUG
        await self.send_message(channel, texts['ask_header'])
        header = await self.wait_for_message(author=author, channel=channel)
        print(header.content) # DEBUG

        # DEBUG
        # self.initialized = True

    async def forward(self, msg):
        raise NotImplemenntedError()


def initialize(config):
    cache = Cache(config['cache_root'])
    bot = AnonBot(cache)
    texts = get_config(config['texts_path'])

    @bot.event
    async def on_ready():
        print("hi")

    @bot.event
    async def on_message(msg):
        if msg.channel.is_private:
            if bot.initialized:
                await bot.forward(msg.content)
            else:
                await bot.send_message(msg.channel, texts['uninitialized'])
            return

        if bot.is_command("initialize", msg.content):
            await bot.initialize(msg.channel, msg.author)


    return bot


if __name__ == '__main__':
    config = get_config(config_path)
    border_bot = initialize(config)
    border_bot.run(config['token'])
