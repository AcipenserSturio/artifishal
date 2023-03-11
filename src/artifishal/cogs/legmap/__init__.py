from .cog import CogLegmap


def setup(bot):
    bot.add_cog(CogLegmap(bot))
