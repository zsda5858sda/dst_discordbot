# 導入Discord.py模組
import discord
from discord import app_commands
from discord.ext import commands

import os
import logging.config
import yaml
from dotenv import load_dotenv
import asyncio

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = kwargs.pop('token')
        self.channel_id = kwargs.pop('channel_id')

    # 當機器人完成啟動時
    async def on_ready(self):
        slash = await self.tree.sync()
        logging.info(f"目前登入身份 --> {self.user}")
        logging.info(f"載入 {len(slash)} 個斜線指令")

    async def start(self):
        async with self:
            await self.__load_extensions__()
            await super().start(self.token)

    # 一開始bot開機需載入全部程式檔案
    async def __load_extensions__(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and "public" not in filename:
                await self.load_extension(f"cogs.{filename[:-3]}")

if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    channel_id = os.getenv("DISCORD_CHANNEL")
    
    # bot是跟discord連接，intents是要求機器人的權限
    intents = discord.Intents.default()
    bot = Bot(command_prefix='!', intents=intents, token=token, channel_id=channel_id)

    if not os.path.exists('log'):
        os.mkdir('log')

    with open(file="logconfig.yaml", mode='r', encoding="utf-8") as file:
        logging_yaml = yaml.load(stream=file, Loader=yaml.FullLoader)
        logging.config.dictConfig(config=logging_yaml)

    asyncio.run(bot.start())