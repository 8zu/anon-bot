import asyncio
import logging
import os.path as osp
import sys
import random

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
    rule = '__' + (' ' * 150) + '__'

    def __init__(self, cache, texts):
        super().__init__(description=description, command_prefix='?')
        self.cache = cache
        self.texts = texts

    def is_me(self, author):
        return author == self.user

    def is_owner(self, author):
        """ is server is not set then just return true. Otherwise author must be the server owner """
        return not self.server or author == self.server.owner

    def load_config(self, cache):
        saved_config = cache.load('saved_config.json').val
        if saved_config:
            self.server = self.get_server(saved_config['server'])
            self.anon_role = self.find_role(saved_config['anon_role'])
            self.channel = self.find_channel(saved_config['channel'])
            self.header = saved_config['header']
            self.counter = 0
            return True
        else:
            return False

    def save_config(self):
        saved_config = {
            "server": self.server.id,
            "header": self.header,
            "channel": self.channel.name,
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

    def find_channel(self, name_or_id):
        if name_or_id.startswith('<#'):
            ch_id = name_or_id[2:-1]
            return self.get_channel(ch_id)
        else:
            return utils.find(lambda ch: ch.name == name_or_id, self.get_all_channels())

    async def initialize(self, channel, author):
        async def say(msg_id):
            await self.send_message(channel, self.texts[msg_id])

        if not self.is_owner(author):
            await say('not_owner')

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
                await say('invalid_role')
        while True:
            ch_msg = await ask('ask_channel')
            self.channel = self.find_channel(ch_msg.content)
            if self.channel:
                break
            else:
                await say('invalid_channel')
        header = await ask('ask_header')
        self.header = header.content

        self.save_config()
        await say('init_complete')
        self.initialized = True

    def check_eligible(self, user):
        mem = utils.find(lambda m: m.id == user.id, self.get_all_members())
        if not mem:
            return False
        return self.anon_role in mem.roles

    def decorated_header(self):
        return '\n'.join(['```css', self.header.format(counter=f'{self.counter:04}', id=random.randint(10000, 99999)), '```'])

    async def forward(self, msg):
        self.counter += 1
        frame = '\n'.join([self.decorated_header(), msg])
        await self.send_message(self.channel, frame)

    async def set_counter(self, channel, author, msg):
        if not self.is_owner(author):
            await say('not_owner')
        try:
            cnt = int(msg.split(' ')[1])
        except ValueError:
            await self.send_message(channel, self.texts['counter_parse_error'])
        self.counter = cnt


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
        if bot.is_me(msg.author):
            return

        async def say(msg_id):
            await bot.send_message(msg.channel, msg_id)

        if msg.channel.is_private:
            if not bot.initialized:
                await say(texts['uninitialized'])
            elif not bot.check_eligible(msg.author):
                await say(texts['ineligible'].format(role=bot.anon_role))
            else:
                await bot.forward(msg.content)
            return

        if bot.like_command("init", msg.content):
            await bot.initialize(msg.channel, msg.author)
        elif bot.is_command('set_counter', msg.content):
            await bot.set_counter(msg.channel, msg.author, msg.content)

    return bot


if __name__ == '__main__':
    config = get_config(config_path)
    if 'token' not in config or not config['token']:
        logger.error("Token is not filled in! Shutting down now...")
        sys.exit(1)
    border_bot = initialize(config)
    border_bot.run(config['token'])
