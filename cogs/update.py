# discord
import discord
from discord.ext import commands, tasks
# web crawler
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from lxml import html
# system
import time
import datetime 
import logging

from cogs.public import Public

logger = logging.getLogger(__name__)

class Update(Public):
    loop_time = [
        datetime.time(hour = i*3, minute = 0, tzinfo = datetime.timezone(datetime.timedelta(hours = 8)))
        for i in range(0, 8)
    ]
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.send_news.start()
    
    def cog_unload(self):
        # 取消執行函式
        self.send_news.cancel()

    # 定義要執行的循環函式
    @tasks.loop(time = loop_time)
    # @tasks.loop(seconds=30)
    async def send_news(self):
        if self.bot.channel:
            file = open('titles.txt', mode='r')
            titles = file.read().split(',')
            file.close()

            url = "https://store.steampowered.com/news/app/322330"
            options = Options()
            options.add_argument("-inprivate")
            options.add_argument("--headless")
            #create chrome driver
            driver = webdriver.Edge(options=options)
            driver.get(url)
            driver.implicitly_wait(10)
            div = driver.find_elements(By.XPATH, '//a[@class="Focusable"]')
            for d in div:
                div_html = html.fromstring(d.get_attribute('innerHTML')) 
                title = div_html.xpath('//div[@class="eventcalendartile_EventName_3myvq"]/text()')[0]
                if title in titles: # 是否查過該標題
                    break
                image = div_html.xpath('//div[@class="eventcalendartile_AppBannerLogo_QRRaO eventcalendartile_FallbackImage_kbkLs"]/@style')
                description = 'click title to check more details...'
                if not image: # 有些縮圖是yt player
                    image = div_html.xpath('//img[@class="YoutubePreviewImage"]/@src')
                summary = div_html.xpath('//div[@class="eventcalendartile_EventSummaryDefault_23hMR"]/text()')
                if summary: # 不是每個區塊都有大綱
                    description = summary[0] + '\n' + description
                image_url = image[0].removeprefix('background-image: url("').removesuffix('");')
                titles.append(title)
                embed = discord.Embed(title=title, description=description, color=0x85d0ff, url=d.get_attribute('href'))
                embed.set_image(url=image_url)
                logger.info(f'''
                title: {title},
                description: {description},
                image: {image_url},
                url: {url},
                ''')
                await self.bot.channel.send("@everyone Klei發布新的貼文啦，快來看看這次有甚麼更新", embed=embed)
            
            file = open('titles.txt', mode='w')
            file.write(','.join(titles))
            file.close()

async def setup(bot: commands.Bot):
    await bot.add_cog(Update(bot))