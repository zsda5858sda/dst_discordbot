# discord
import discord
from discord import app_commands, ui
from discord.ext import commands
# web crawler
import requests
from bs4 import BeautifulSoup, ResultSet
from lxml import html
# typing
from typing import Any, Dict, List, Tuple, Optional

from cogs.public import Public
from models.material import Material as MaterialModel
import logging

logger = logging.getLogger(__name__)

class Item(Public):
    WIKI_BASE_URL = "https://dontstarve.huijiwiki.com"
    FANDOM_BASE_URL = "https://dontstarve.fandom.com/wiki"
    
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self._user_map = {}  # 用戶ID到材料模型的映射
        self._result_map = {}  # 搜索結果映射
    
    @app_commands.command(name="material", description="查詢材料用途，請在後放加上欲搜尋之材料")
    @app_commands.describe(keyword="輸入材料")
    async def material(self, interaction: discord.Interaction, keyword: str):
        """查詢材料可以製作的物品"""
        await interaction.response.defer(thinking=True)
        
        try:
            # 記錄查詢信息
            logger.info(f"用戶信息: ID={interaction.user.id}, 名稱={interaction.user.name}")
            logger.info(f"查詢道具: {keyword}")
            
            # 準備查詢數據
            _title = f"有關 {keyword} 能製作的道具"
            _kw = self._prepare_keyword(keyword)
            
            # 獲取可用物品索引
            _index_list, _character_list = self._get_available_items_index(_kw)
            _material = MaterialModel(
                index_list=_index_list, 
                title=_title, 
                kw=_kw, 
                character_list=_character_list
            )
            
            # 沒有找到結果的情況
            if not _index_list:
                embed = discord.Embed(
                    title=_title,
                    color=0xe15158,
                    description="查無該物品可製作之道具，或該物品不存在"
                )
                await interaction.followup.send(embed=embed)
                return
            
            # 創建並發送結果嵌入
            embeds = self._create_embeds(_material)
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
    
    @app_commands.command(name="more", description="查詢更多")
    async def more(self, interaction: discord.Interaction):
        """顯示更多查詢結果"""
        await interaction.response.defer(thinking=True)
        
        if interaction.user.id not in self._user_map:
            await interaction.followup.send("無法使用該指令，請先使用 /material 命令進行查詢")
            return
            
        try:
            _material = self._user_map[interaction.user.id]
            
            # 檢查是否還有更多結果
            if len(_material._index_list) == _material._cur_index:
                embed = discord.Embed(
                    title=_material._title,
                    color=0xffe481,
                    description="無更多可製作之道具"
                )
                await interaction.followup.send(embed=embed)
                return
                
            # 獲取並發送更多結果
            embeds = self._create_embeds(_material)
            await interaction.followup.send(content=f"{interaction.user.mention}", embeds=embeds)
            
        except Exception as e:
            msg = f"出現錯誤：{str(e)}"
            logger.error(msg)
            await interaction.followup.send(msg)
    
    @app_commands.command(name="search", description="查詢")
    @app_commands.describe(keyword="輸入關鍵字")
    async def search(self, interaction: discord.Interaction, keyword: str):
        """通用搜索功能"""
        await interaction.response.defer(thinking=True)
        
        try:
            # 構建搜索 URL 並發送請求
            search_url = f"{self.WIKI_BASE_URL}/index.php?title=%E7%89%B9%E6%AE%8A:%E6%90%9C%E7%B4%A2&search={keyword}&profile=default&sort=just_match"
            r = requests.get(search_url)
            soup = BeautifulSoup(r.content, 'lxml')
            results = soup.find_all('li', class_='mw-search-result')
            
            # 處理搜索結果
            if results:
                if len(results) == 1:
                    # 只有一個結果時直接顯示
                    url = f"{self.WIKI_BASE_URL}{results[0].find('a')['href']}"
                    embed = self._get_search_result(url)
                    await interaction.followup.send(content=f"{interaction.user.mention}", embed=embed)
                else:
                    # 多個結果時顯示按鈕供選擇
                    view = self._create_result_buttons(results)
                    await interaction.followup.send(content=f"{interaction.user.mention}", view=view)
            else:
                await interaction.followup.send(content="查無關鍵字")
                
        except Exception as e:
            msg = f"出現錯誤：{str(e)}"
            logger.error(msg)
            await interaction.followup.send(msg)
    
    def _prepare_keyword(self, keyword: str) -> str:
        """準備關鍵字，轉換非英文關鍵字"""
        if not keyword.isascii():
            return self.translation_from_tw(keyword)
        return keyword
    
    def _get_available_items_index(self, keyword: str) -> Tuple[List[int], List[int]]:
        """獲取可用物品的索引和角色專屬物品索引"""
        recipes = self._get_all_items(keyword)
        results = []
        character_list = []
        
        # 查找可用物品
        for index, recipe in enumerate(recipes):
            # 檢查是否適用於 DST
            game_div = recipe.find('div', class_='recipe-game')
            if game_div and not game_div.find('img', attrs={'data-image-key': 'Don%27t_Starve_Together_icon.png'}):
                continue
            
            # 檢查是否為角色專屬物品
            character_div = recipe.find('div', class_='recipe-character')
            if character_div:
                character_list.append(index)
            
            results.append(index)
        
        logger.info(f'查詢筆數: {len(results)}')
        logger.info(f'角色專屬物品: {character_list}')
        return results, character_list
    
    def _get_all_items(self, keyword: str) -> ResultSet:
        """獲取所有物品信息"""
        r = requests.get(f"{self.FANDOM_BASE_URL}/{keyword}")
        soup = BeautifulSoup(r.content, 'lxml')
        return soup.find_all('div', class_='recipe-container')
    
    def _get_item_details(self, index: int, recipes: ResultSet) -> Dict[str, Any]:
        """獲取物品詳細信息"""
        # 獲取結果物品名稱和圖標
        result_div = recipes[index].find('div', class_='recipe-result')
        result_name = result_div.find('a')['title']
        icon_url = result_div.find('img')['data-src']
        
        # 獲取科技類型
        science_div = recipes[index].find('div', class_='recipe-object')
        science_a = science_div.find('a')
        science = science_a['title'] if science_a and science_a.has_attr('title') else '一般製作'
        
        # 獲取材料結構
        materials = {}
        material_divs = recipes[index].find_all('div', class_='recipe-item')
        for div in material_divs:
            title = div.find('a')['title']
            count = div.find('div', class_='recipe-count').text if div.find('div', class_='recipe-count') else '1x'
            materials[title] = count
        
        # 獲取角色信息（如果有）
        character = None
        character_div = recipes[index].find('div', class_='recipe-character')
        if character_div and character_div.find('a'):
            character = character_div.find('a')['title']
        
        return {
            'result_name': result_name,
            'icon_url': icon_url,
            'science': science,
            'materials': materials,
            'character': character
        }
    
    def _create_embeds(self, material: MaterialModel) -> List[discord.Embed]:
        """創建嵌入消息列表"""
        embeds = []
        recipes = self._get_all_items(material._kw)
        
        # 創建每個結果的嵌入消息
        for index in range(material.cur_index, material._cur_index + material._limit):
            if len(material._index_list) <= index:
                break
                
            div_index = material._index_list[index]
            item_details = self._get_item_details(div_index, recipes)
            
            # 創建嵌入消息
            embed = discord.Embed(title=material._title, color=0x85d0ff)
            embed.set_thumbnail(url=item_details['icon_url'])
            
            # 添加材料字段
            for material_name, count in item_details['materials'].items():
                embed.add_field(
                    name=self.translation_from_en(material_name),
                    value=count,
                    inline=True
                )
            
            # 設置描述
            description = f"使用 **{self.translation_from_en(item_details['science'])}** 合成 **{self.translation_from_en(item_details['result_name'])}**，需要材料有："
            
            # 為角色專屬物品添加額外信息
            if div_index in material._character_list and item_details['character']:
                description = f"使用 **{self.translation_from_en(item_details['science'])}** 合成 **{self.translation_from_en(item_details['result_name'])}**，需要材料有：（{self.translation_from_en(item_details['character'])}限定）"
                embed.color = 0x227700
                
            embed.description = description
            embeds.append(embed)
            material._cur_index += 1
            
        return embeds
    
    def _create_result_buttons(self, results: ResultSet) -> ui.View:
        """創建搜索結果按鈕"""
        view = ui.View()
        id_map = {}
        
        for result in results:
            title = result.find('a')['title']
            button = ui.Button(style=discord.ButtonStyle.primary, label=title, custom_id=title)
            button.callback = self._button_callback
            id_map[title] = f"{self.WIKI_BASE_URL}{result.find('a')['href']}"
            view.add_item(button)
            
        self._result_map = id_map
        return view
    
    async def _button_callback(self, interaction: discord.Interaction):
        """按鈕交互回調函數"""
        url = self._result_map[interaction.data['custom_id']]
        embed = self._get_search_result(url)
        await interaction.response.edit_message(view=None, embed=embed)
    
    def _get_search_result(self, url: str) -> discord.Embed:
        """獲取搜索結果的嵌入消息"""
        r = requests.get(url)
        source_code = html.fromstring(r.content)
        
        # 提取標題和內容
        title = source_code.xpath('//*[@id="firstHeading"]/h1/text()')[0]
        contents = source_code.xpath('//*[@id="mw-content-text"]/div/h2[1]/preceding-sibling::p//text()')
        if not contents:
            contents = source_code.xpath('//*[@id="mw-content-text"]/div/p//text()')
            
        content = (''.join(contents)).replace('\n', '\n\n')
        
        # 創建嵌入消息
        return discord.Embed(
            title=title,
            description=content,
            color=0x85d0ff,
            url=url
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Item(bot))