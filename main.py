# 導入Discord.py模組
import discord
from discord import app_commands
from discord.ext import commands

import os
import logging.config
import yaml
from dotenv import load_dotenv
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# client是跟discord連接，intents是要求機器人的權限
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents = intents)

# 當機器人完成啟動時
@bot.event
async def on_ready():
    slash = await bot.tree.sync()
    logging.info(f"目前登入身份 --> {bot.user}")
    logging.info(f"載入 {len(slash)} 個斜線指令")

# 一開始bot開機需載入全部程式檔案
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and "public" not in filename:
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    if not os.path.exists('log'):
        os.mkdir('log')

    with open(file="logconfig.yaml", mode='r', encoding="utf-8") as file:
        logging_yaml = yaml.load(stream=file, Loader=yaml.FullLoader)
        logging.config.dictConfig(config=logging_yaml)

    asyncio.run(main())

    # import requests
    # from lxml import etree, html

    # r = requests.get(f"https://dontstarve.huijiwiki.com/wiki/%E9%A5%A5%E9%A5%BF%E8%85%B0%E5%B8%A6")
    # #用lxml的html函式來處理內容格式
    # byte_data = r.content
    # source_code = html.fromstring(byte_data)
    # title = source_code.xpath('//*[@id="firstHeading"]/h1/text()')
    # content = source_code.xpath('//*[@id="mw-content-text"]/div/div[2]/preceding-sibling::p//text()')
    # print(''.join(title))
    # print(''.join(content)=='')
    # import requests
    # from bs4 import BeautifulSoup
    # import io


    # r = requests.get(f"https://dontstarve.fandom.com/wiki/silk")
    # soup = BeautifulSoup(r.content, 'lxml')

    # results = []
    # recipe = soup.find('div', class_='recipe-container')
    # print(recipe.find('div', class_='recipe-count').text)
    # # find available items
    # for index, recipe in enumerate(recipes):
    #     game_td = recipe.find('td', class_='game')
    #     character_td = recipe.find('td', class_='character')
    #     if character_td:
    #         continue
        
    #     if game_td and not game_td.find('img', attrs={'data-image-key': 'Don%27t_Starve_Together_icon.png'}):
    #         # check item has dst icon
    #         # if :
    #         continue
    #     print(recipe.find('td', class_='result').find('a')['title'])
    #     results.append(index)
    # print(len(results))