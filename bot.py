import asyncio
import logging
import os.path as osp
import sys
import re

import pytoml

from cache import Cache

try:
    from discord.ext import commands
    from discord import utils
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

config_path = './config.toml'
description = """A bot to allow simple anonymous posting. Use at own risk!"""

def get_config(path):
    if osp.exists(path):
        config = pytoml.load(open(path, "r", encoding="UTF-8"))
    else:
        logger.error("Missing config file! Shutting down now...")
        sys.exit(1)

    return config

class AnonBot(commands.Bot):
    def __init__(self, cache, texts):
        super().__init__(description=description, command_prefix='?')
        self.cache = cache
        self.texts = texts

    def load_config(self, cache):
        saved_config = cache.load('saved_config.json').val
        if saved_config:
            self.server = self.get_server(saved_config['server'])
            self.anon_role = self.find_role(saved_config['anon_role'])
            self.header = saved_config['header']
            return True
        else:
            return False

    def save_config(self):
        saved_config = {
            "server": self.server.id,
            "header": self.header,
            "anon_role": self.anon_role.name,
        }
        self.cache.save('saved_config.json', saved_config)


    def is_command(self, cmd, s):
        return s.strip().split(' ')[0] == f"{self.command_prefix}{cmd}"

    def like_command(self, cmd, s):
        return s.strip().split(' ')[0].startswith(f"{self.command_prefix}{cmd}")

    def find_role(self, name_or_id):
        roles = self.server.role_hierarchy
        if name_or_id.startswith('<@&'):
            role_id = name_or_id[3:-1]
            return utils.find(lambda r: r.id == role_id, roles)
        else:
            return utils.find(lambda r: r.name == name_or_id, roles)

    async def initialize(self, channel, author):
        async def say(msg_id):
            await self.send_message(channel, self.texts[msg_id])
        async def ask(prompt):
            await say(prompt)
            return await self.wait_for_message(author=author, channel=channel)
        def is_yes_no(msg):
            return msg.content.lower() in ['y', 'n', 'yes', 'no']
        async def ask_yes_no(prompt):
            await say(prompt)
            return await self.wait_for_message(author=author, channel=channel, check=is_yes_no)

        if self.initialized:
            res = await ask_yes_no('overwrite_init')
            if res.content.lower() in ['n', 'no']:
                await say('overwrite_aborted')
                return

        self.server = channel.server
        while True:
            role = await ask('ask_role')
            self.anon_role = self.find_role(role.content)
            if self.anon_role:
                break
            else:
                await say('ask_role')
        header = await ask('ask_header')
        self.header = header.content

        self.save_config()
        await say('init_complete')
        self.initialized = True

    async def forward(self, msg):
        raise NotImplemenntedError()


def initialize(config):
    cache = Cache(config['cache_root'])
    texts = get_config(config['text_path'])
    bot = AnonBot(cache, texts)

    @bot.event
    async def on_ready():
        print("hi")
        bot.initialized = bot.load_config(cache)

    @bot.event
    async def on_message(msg):
        if msg.channel.is_private:
            if bot.initialized:
                await bot.forward(msg.content)
            else:
                await bot.send_message(msg.channel, texts['uninitialized'])
            return

        if bot.like_command("init", msg.content):
            await bot.initialize(msg.channel, msg.author)

    return bot


if __name__ == '__main__':
    config = get_config(config_path)
    if 'token' not in config or not config['token']:
        logger.error("Token is not filled in! Shutting down now...")
        sys.exit(1)
    border_bot = initialize(config)
    border_bot.run(config['token'])
