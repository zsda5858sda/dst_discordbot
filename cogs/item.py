#discord
from typing import Any
import discord
from discord import app_commands, ui
from discord.ext import commands
# web crawler
import requests
from bs4 import BeautifulSoup, ResultSet
from lxml import etree, html

from cogs.public import Public
from models.material import Material as MaterialModel
import logging
import traceback

logger = logging.getLogger(__name__)

class Item(Public):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self._user_map = {}
        self._result_map = {}

    @app_commands.command(name = "material", description = "查詢材料用途，請在後放加上欲搜尋之材料")
    @app_commands.describe(keyword = "輸入材料")
    async def material(self, interaction: discord.Interaction, keyword: str):
        await interaction.response.defer(thinking=True)
        if interaction.user.id in self._user_map.keys():
            self._user_map[interaction.user.id].__init__()
        try:
            logger.info(f"user id: {interaction.user.id}")
            logger.info(f"user name: {interaction.user.name}")
            logger.info(f"查詢道具: {keyword}")
            _title = f"有關 {keyword} 能製作的道具"
            _kw = keyword
            if not keyword.isascii(): # if keyword is not english, use method to change
                _kw = self.translation_from_tw(keyword)
            _index_list, _character_list = self.__search_available_items_index(_kw)
            _material = MaterialModel(index_list=_index_list, title=_title, kw=_kw, character_list=_character_list)

            if not _index_list:
                embed = discord.Embed(title=_title, color=0xe15158, description="查無該物品可製作之道具，或該物品不存在")
                await interaction.followup.send(embed=embed)
                return
                
            embeds = self.__set_embeds(_material)
            self._user_map[interaction.user.id] = _material
            await interaction.followup.send(content=f"{interaction.user.mention}", embeds=embeds)

        except KeyError:
            msg = f"查無關鍵字，請確認輸入文字是否正確。輸入文字：{keyword}"
            logger.error(msg)
            await interaction.followup.send(msg)
        except Exception as e:
            msg = f"出現錯誤：{str(e)}"
            logger.error(msg)
            await interaction.followup.send(msg)


    @app_commands.command(name = "more", description = "查詢更多")
    async def more(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        if interaction.user.id not in self._user_map.keys():
            await interaction.followup.send(f"無法使用該指令")
            return
        try:
            _material = self._user_map[interaction.user.id]
            if len(_material._index_list) == _material._cur_index:
                embed = discord.Embed(title=_material._title, color=0xffe481, description="無更多可製作之道具")
                await interaction.followup.send(embed=embed)
                return
            embeds = self.__set_embeds(_material)
            await interaction.followup.send(content=f"{interaction.user.mention}", embeds=embeds)
        except Exception as e:
            msg = f"出現錯誤：{str(e)}"
            logger.error(msg)
            await interaction.followup.send(msg)

    @app_commands.command(name = "search", description = "查詢")
    @app_commands.describe(keyword = "輸入關鍵字")
    async def search(self, interaction: discord.Interaction, keyword: str):
        await interaction.response.defer(thinking=True)
        try:
            host = "https://dontstarve.huijiwiki.com"
            r = requests.get(f"{host}/index.php?title=%E7%89%B9%E6%AE%8A:%E6%90%9C%E7%B4%A2&search={keyword}&profile=default&sort=just_match")
            soup = BeautifulSoup(r.content, 'lxml')
            results = soup.find_all('li', class_='mw-search-result')
            if len(results) > 0:
                if len(results) == 1:
                    url = f"{host}{results[0].find('a')['href']}"
                    embed = self.__get_search_result(url)
                    await interaction.followup.send(content=f"{interaction.user.mention}", embed=embed)
                else:
                    view = ui.View()
                    id_map = {}
                    for r in results:
                        title = r.find('a')['title']
                        button = ui.Button(style=discord.ButtonStyle.primary, label=title, custom_id=title)
                        button.callback = self.__button_callback
                        id_map[title] = f"{host}{r.find('a')['href']}"
                        view.add_item(button)
                    self._result_map = id_map
                    await interaction.followup.send(content=f"{interaction.user.mention}", view=view)
            else:
                #do something
                await interaction.followup.send(content="查無關鍵字")
        except Exception as e:
            msg = f"出現錯誤：{str(e)}"
            logger.error(msg)
            await interaction.followup.send(msg)

    # 創建按鈕交互函式
    async def __button_callback(self, interaction: discord.Interaction):
        
        url = self._result_map[interaction.data['custom_id']]
        embed = self.__get_search_result(url)
        await interaction.response.edit_message(view=None, embed=embed)

    def __get_all_items(self, keyword):
        r = requests.get(f"https://dontstarve.fandom.com/wiki/{keyword}")
        soup = BeautifulSoup(r.content, 'lxml')
        return soup.find_all('div', class_='recipe-container')

    def __search_available_items_index(self, keyword: str):
        
        recipes = self.__get_all_items(keyword)
        results = []
        character_list = []

        # find available items
        for index, recipe in enumerate(recipes):
            game_div = recipe.find('div', class_='recipe-game')
            if game_div and not game_div.find('img', attrs={'data-image-key': 'Don%27t_Starve_Together_icon.png'}):
                # check item has dst icon
                continue

            character_div = recipe.find('div', class_='recipe-character')
            if character_div:
                character_list.append(index)
            results.append(index)

        logger.info(f'查詢筆數: {len(results)}')
        logger.info(f'characters: {character_list}')
        return results, character_list
    
    def __get_result(self, index: int, recipes: ResultSet[Any]):
        result = recipes[index].find('div', class_='recipe-result')
        return result.find('a')['title'], result.find('img')['data-src']
    
    def __get_character(self, index: int, recipes: ResultSet[Any]):
        result = recipes[index].find('div', class_='recipe-character')
        return result.find('a')['title']
    
    def __get_science(self, index: int, recipes: ResultSet[Any]):
        result = recipes[index].find('div', class_='recipe-object')
        a = result.find('a')
        return a['title'] if a.has_attr('title') else '一般製作'
    
    def __get_structures(self, index: int, recipes: ResultSet[Any]):
        divs = recipes[index].find_all('div', class_='recipe-item')
        structure = {}
        for div in divs:
            title = div.find('a')['title']
            structure[title] = div.find('div', class_='recipe-count').text if div.find('div', class_='recipe-count') else '1x'
        logger.info(f"struceture: {structure}")
        return structure
    
    def __set_embeds(self, material: MaterialModel):
        embeds = []
        recipes = self.__get_all_items(material._kw)
        for index in range(material.cur_index, material._cur_index+material._limit):
            if len(material._index_list) <= index:
                break
            div_index = material._index_list[index]
            embed = discord.Embed(title=material._title, color=0x85d0ff)
            result, icon_url = self.__get_result(div_index, recipes)
            logger.info(f"result: {result}")
            science = self.__get_science(div_index, recipes)
            embed.set_thumbnail(url=icon_url) # available item icon
            for k, v in self.__get_structures(div_index, recipes).items():
                embed.add_field(name=self.translation_from_en(k), value=v, inline=True)
            embed.description =  f"使用 **{self.translation_from_en(science)}** 合成 **{self.translation_from_en(result)}**，需要材料有："
            if div_index in material._character_list:
                embed.description = f"使用 **{self.translation_from_en(science)}** 合成 **{self.translation_from_en(result)}**，需要材料有：（{self.translation_from_en(self.__get_character(div_index, recipes))}限定）"
                embed.color=0x227700
            embeds.append(embed)
            material._cur_index += 1
        return embeds
    
    def __get_search_result(self, url):
        r = requests.get(url)
        #用lxml的html函式來處理內容格式
        byte_data = r.content
        source_code = html.fromstring(byte_data)

        title = source_code.xpath('//*[@id="firstHeading"]/h1/text()')[0]
        contents = source_code.xpath('//*[@id="mw-content-text"]/div/h2[1]/preceding-sibling::p//text()')
        if len(contents) == 0:
            contents = source_code.xpath('//*[@id="mw-content-text"]/div/p//text()')
        content = (''.join(contents)).replace('\n', '\n\n')
        
        return discord.Embed(title=title, description=content, color=0x85d0ff, url=url)

async def setup(bot: commands.Bot):
    await bot.add_cog(Item(bot))