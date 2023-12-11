#discord
from discord.ext import commands
import json

class Public(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # def translation_from_list(self, inputs: list[str]) -> list[str]:
    #     with open("EN_to_TW.json", 'r', encoding='utf-8') as f:
    #         ref = json.loads(f.read())
    #         results = [ref[x] for x in inputs]
    #         print(results)
    #         return results

    def translation_from_en(self, input: str) -> str:
        with open("EN_to_TW.json", 'r', encoding='utf-8') as f:
            ref = json.loads(f.read())
            if input in ref.keys():
                return ref[input]
            else:
                return input
        
    def translation_from_tw(self, input: str) -> str:
        with open("TW_to_EN.json", 'r', encoding='utf-8') as f:
            ref = json.loads(f.read())
            if input in ref.keys():
                return ref[input]
            else:
                return input

if __name__ == "__main__":
    with open("EN_to_TW.json", 'r', encoding='utf-8') as f:
        ref = json.loads(f.read())
        inputs = ['Top Hat', 'Breezy Vest', 'Beekeeper Hat', 'Winter Hat', 'Dapper Vest', 'Boomerang', 'Fishing Rod', 'Bird Trap', 'Puffy Vest', 'Sewing Kit', 'Umbrella', 'Bug Net', 'Tent', 'Piggyback', 'Spider Eggs', 'Cat Cap', 'Floral Shirt', 'Floral Shirt', 'Siesta Lean-to', 'Bernie Inactive']
        results = [ref[x] for x in inputs]
        print(results)