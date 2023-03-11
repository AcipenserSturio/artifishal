import random

from discord import File
from discord.ext.commands import Cog

from ilo.cog_utils import Locale

from ilo.cogs.legmap.legmap import generate_leg_map


class CogLegmap(Cog):
    def __init__(self, bot):
        self.bot = bot

    locale = Locale(__file__)

    @locale.command("map")
    @locale.option("mode",
        default="control",
        choices=[
            "control",
            "population",
            "left",
            "macroregions",
            "adjacencies",
        ]
    )
    async def slash_map(self, ctx, mode):
        await ctx.respond("Generating map. Please wait...")
        map_path = generate_leg_map(mode.upper())
        await ctx.send(mode, file=File(map_path))
