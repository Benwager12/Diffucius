from io import BytesIO

import disnake.ui
from PIL import Image
from disnake import app_commands
from disnake.ext import commands
from disnake.ext.commands import Bot

import utility


class ListModels(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @commands.slash_command(
        name="setmodel",
        description="Set the model to use",
        guild_ids=[1087519336408825916],
        dm_permission=False
    )
    async def setmodel(
            self,
            interaction: disnake.ApplicationCommandInteraction,
            model: str = commands.Param(
                name="model",
                description="The model to use",
                choices=utility.get_models()
            )
    ) -> None:

        if model not in utility.get_models():
            await interaction.response.send_message(
                content="Invalid model",
                ephemeral=True
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        utility.api.set_options(
            options={
                "sd_model_checkpoint": utility.model_name_to_hash_name(model)
            }
        )

        await interaction.followup.send(
            f"Selected the model `{model}`."
        )

    @commands.slash_command(
        name="create",
        description="Create an image from a prompt"
    )
    async def send_prompt(
            self,
            interaction: disnake.ApplicationCommandInteraction,
            prompt: str = commands.Param(
                name="prompt",
                description="The prompt to use"
            ),
            negative: str = commands.Param(
                name="negative",
                description="The negative prompt to use",
                default=""
            ),
            cfg_scale: float = commands.Param(
                name="cfg_scale",
                description="The cfg_scale value to use",
                gt=1.0,
                lt=14.0,
                default=7.0
            ),
            width: int = commands.Param(
                name="width",
                description="The width of the image",
                gt=127,
                lt=769,
                default=512
            ),
            height: int = commands.Param(
                name="height",
                description="The height of the image",
                gt=127,
                lt=769,
                default=512
            ),
            show: bool = commands.Param(
                name="show",
                description="Show the image in the chat",
                default=True
            ),
            seed: int = commands.Param(
                name="seed",
                description="The seed to use",
                default=-1
            ),
            steps: int = commands.Param(
                name="steps",
                description="The number of steps to use",
                default=20,
                gt=0,
                lt=150
            ),
            batch: int = commands.Param(
                name="batch",
                description="The batch count to use",
                default=1,
                gt=0,
                lt=5
            ),
            sampler: str = commands.Param(
                name="sampler",
                description="The sampler to use",
                choices=utility.get_sampler_names(),
                default=None
            ),
            save_image: bool = commands.Param(
                name="save_image",
                description="Save the image to the bot's local storage",
                default=True
            )
    ):
        if isinstance(interaction.channel, disnake.PartialMessageable):
            show = True

        save_image = save_image or isinstance(interaction.channel, disnake.TextChannel)

        if width > 512 and height > 512:
            await interaction.response.send_message(
                content="Width and height cannot be greater than 512 at the same time.",
                ephemeral=True
            )
            return

        await interaction.response.defer(
            ephemeral=not show
        )
        result = await utility.api.txt2img(
            prompt=prompt,
            negative_prompt=negative,
            cfg_scale=cfg_scale,
            use_async=True,
            width=width,
            height=height,
            seed=seed,
            steps=steps,
            batch_size=batch,
            sampler_name=sampler,
            save_images=save_image
        )
        images = []
        for index, image in enumerate(result.images):
            with BytesIO() as image_binary:
                image.save(image_binary, "PNG")
                image_binary.seek(0)
                images.append(disnake.File(image_binary, filename=f"image-{index}.png"))

        await interaction.followup.send(
            f"Generated image with model `{utility.get_model()}`, seed: `{result.info.get('seed')}`.",
            files=images
        )

    @commands.slash_command(
        name="getmodel",
        description="Get the current model",
        guild_ids=[1087519336408825916],
        dm_permission=False
    )
    async def getmodel(
            self,
            interaction: disnake.ApplicationCommandInteraction
    ):
        await interaction.response.defer(
            ephemeral=True
        )

        await interaction.followup.send(
            "Current model: `" + utility.get_model() + "`"
        )

    @commands.slash_command(
        name="describe",
        description="Describe the inputted photo"
    )
    async def describe(
            self,
            interaction: disnake.ApplicationCommandInteraction,
            model: str = commands.Param(
                name="interrogate_model",
                description="The model to use",
                choices=["DeepBooru", "CLIP"],
                default="DeepBooru"
            ),
            image: disnake.Attachment = commands.Param(
                name="image",
                description="The image to describe"
            ),
            hide: bool = commands.Param(
                name="hide",
                description="Hide the description",
                default=False
            ),
            hide_image: bool = commands.Param(
                name="hide_image",
                description="Hide the image",
                default=False
            )
    ) -> None:
        model_used = model.lower()
        if model_used == "deepbooru":
            model_used = "deepdanbooru"

        # Check if the disnake.File is a valid image
        if image.filename is None:
            await interaction.response.send_message(
                content="You have not provided a file",
                ephemeral=True
            )
            return

        if image.filename.split(".")[-1] not in ["png", "jpg", "jpeg", "webp", "gif"]:
            await interaction.response.send_message(
                "Invalid image",
                ephemeral=True
            )
            return

        await interaction.response.defer(
            ephemeral=hide
        )

        # Get PIL image from disnake.Attachment
        image_bytes = await image.read()
        image_pil = Image.open(BytesIO(image_bytes))

        try:
            result = utility.api.interrogate(
                model=model_used,
                image=image_pil
            )
        except RuntimeError as cie:
            await interaction.followup.send(
                "Error: " + str(cie)
            )
            return

        image_text = "image"
        if not hide_image:
            image_text = f"[{image_text}]({image.url})"
        else:
            print(f"Hiding image - {image.url}")

        await interaction.followup.send(
            f"{image_text} has the description `{result.info}`."
        )
        return

    @commands.message_command(
        name="Delete Message",
        description="Delete a message sent by the bot"
    )
    async def delete_message(
            self,
            interaction: disnake.Interaction,
            message: disnake.Message
    ) -> None:

        will_delete = message.author.id == self.bot.user.id and (  # If the message being deleted is the bot's message
                isinstance(interaction.channel, disnake.DMChannel) or  # If it's a DM channel
                interaction.author.guild_permissions.administrator or  # If the user is an admin
                interaction.author.id in utility.config.get("admins") or  # If the user is in the admins list
                interaction.author.id in interaction.channel.topic  # If the user id is in the channel topic
        )

        if not will_delete:
            await interaction.response.send_message(
                content="You do not have permission to delete this message.",
                ephemeral=True
            )
            return

        await message.delete()
        await interaction.response.send_message(
            content="You have deleted the message.",
            ephemeral=True
        )
        return


def setup(bot: Bot):
    bot.add_cog(ListModels(bot))
