from io import BytesIO

import disnake.ui
from PIL import Image
from disnake.ext import commands
from disnake.ext.commands import CommandInvokeError

import utility


class ListModels(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.last_member = None

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
	):

		if model not in utility.get_models():
			await interaction.response.send_message(
				"Invalid model",
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
			"Selected the model `"+model+"`."
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
			)
	):
		if show and interaction.author.id not in utility.config.get("admins"):
			show = False

		if isinstance(interaction.channel, disnake.PartialMessageable):
			show = True

		if width > 512 and height > 512:
			await interaction.response.send_message(
				"Width and height cannot be greater than 512 at the same time.",
				ephemeral=True
			)
			return

		print(interaction)

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
			sampler_name=sampler
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
			"Current model: `"+utility.get_model()+"`"
		)

	@commands.slash_command(
		name="describe",
		description="Describe the inputted photo",
		guild_ids=[1087519336408825916],
		dm_permission=False
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
	):
		model_used = model.lower()
		if model_used == "deepbooru":
			model_used = "deepdanbooru"

		# Check if the disnake.File is a valid image
		if image.filename is None:
			if interaction:
				await interaction.response.send_message(
					"You have not provided a file",
					ephemeral=True
				)
				return
			else:
				return -1

		if image.filename.split(".")[-1] not in ["png", "jpg", "jpeg", "webp", "gif", "mp4"]:
			if interaction:
				await interaction.response.send_message(
					"Invalid image",
					ephemeral=True
				)
				return
			return -1

		if interaction:
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
			if interaction:
				await interaction.followup.send(
					"Error: "+str(cie)
				)
				return
			return -1

		image_text = "image"
		if not hide_image:
			image_text = f"[{image_text}]({image.url})"
		else:
			print(f"Hiding image - {image.url}")

		if interaction:
			await interaction.followup.send(
				f"{image_text} has the description `{result.info}`."
			)
			return


	@commands.slash_command(
		name="recreate",
		description="Recreate an image from an image",
		guild_ids=[1087519336408825916],
		dm_permission=False
	)
	async def recreate(
			self,
			interaction: disnake.ApplicationCommandInteraction,
			image: disnake.Attachment = commands.Param(
				name="image",
				description="The image to recreate"
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
			sampler: str = commands.Param(
				name="sampler",
				description="The sampler to use",
				choices=utility.get_sampler_names(),
				default=None
			),
			steps: int = commands.Param(
				name="steps",
				description="The number of steps to use",
				default=20,
				gt=0,
				lt=150
			),
	):
		await interaction.response.defer(
			ephemeral=not show
		)
		text = await self.describe(None, "DeepBooru", image, True, True)
		await interaction.followup.send(
			text
		)




def setup(bot):
	bot.add_cog(ListModels(bot))
