import disnake
from disnake import Message
from disnake.ext import commands
from disnake.ext.commands import Bot
from os import walk
import logging

import utility

logger = logging.getLogger('disnake')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='disnake.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


def get_prefix(_: Bot, message: Message):
    return utility.config.get("prefix") if message.guild else ""


intents = disnake.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents
)

logger = logging.getLogger('disnake')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='disnake.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Get all cogs
for folder, _, files in walk("cogs"):
    folder = folder.replace("\\", ".")

    for file in files:
        if file.endswith(".py"):
            bot.load_extension(f"{folder}.{file[:-3]}")


@bot.event
async def on_ready():
    print("Bot is ready.")
    await bot.change_presence(
        activity=disnake.Activity(
            type=disnake.ActivityType.playing,
            name=f"with {utility.get_model()}.",
        ),
        status=disnake.Status.online
    )

bot.run(utility.config.get("token"))
