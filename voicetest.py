import asyncio
import base64
import io
import json
import logging
import os
import os.path

import aiohttp
import discord
import numpy
import openai
import pyttsx3
import spacy
import speech_recognition as sr


import youtube_dl
from PIL import Image
from discord import app_commands
from discord.ext.commands import Bot
from dotenv import load_dotenv
from pydub import AudioSegment
spacy.cli.download("en_core_web_sm")
nlp = spacy.load("en_core_web_sm")
import time



engine = pyttsx3.init()
rate = engine.getProperty('rate')
engine.setProperty('rate', rate + 50)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
task_running = False

# Use Bot instead of Discord Client for commands
# Give it ALL THE POWER
intents = discord.Intents.all()
bot = Bot("", intents=intents)

global_contexts = []
MAX_CONVERSATION_HISTORY = 3
nl = "\n"

# DALLE

CONFIG_DICT = {
    "BOT_TOKEN": (os.environ["DISCORD_TOKEN"]),
    "DALLE_MINI_BACKEND_URL": "https://bf.dallemini.ai/generate",
    "COLLAGE_FORMAT": "PNG",
    "IMAGE_SELECT_TIMEOUT": 10800
}


class DALLEMini(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def update_status(self):
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name=f'{len(self.guilds)} servers | /ai'))


class ImageSelect(discord.ui.Select):
    def __init__(self, collage: discord.File, images: list[discord.File]):
        options = [discord.SelectOption(label='Image collage')] + [discord.SelectOption(label=f'Image {i + 1}') for i in
                                                                   range(len(images))]
        super().__init__(placeholder='Enhance Image',
                         min_values=1, max_values=1, options=options)
        self.collage = collage
        self.images = images

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.values[0] == 'Image collage':
            logging.debug(f'{interaction.user} (ID: {interaction.user.id}) requested an image collage')
            self.collage.fp.seek(0)
            await interaction.edit_original_response(attachments=[self.collage])
        else:
            image_index = int(self.values[0].split(' ')[-1]) - 1
            logging.debug(f'{interaction.user} (ID: {interaction.user.id}) requested image #{image_index + 1}')
            self.images[image_index].fp.seek(0)
            await interaction.edit_original_response(attachments=[self.images[image_index]])


intents = discord.Intents.all()
client = DALLEMini(intents=intents)
config: object


class ImageSelectView(discord.ui.View):
    def __init__(self, collage: discord.File, images: list[discord.File], timeout: float):
        super().__init__(timeout=timeout)
        self.add_item(ImageSelect(collage, images))


async def generate_images(prompt: str) -> list[io.BytesIO]:
    async with aiohttp.ClientSession() as session:
        async with session.post(config['DALLE_MINI_BACKEND_URL'], json={'prompt': prompt}) as response:
            if response.status == 200:
                response_data = await response.json()
                images = [io.BytesIO(base64.decodebytes(bytes(image, 'utf-8')))
                          for image in response_data['images']]
                return images
            else:
                return None


def make_collage_sync(images: list[io.BytesIO], wrap: int) -> io.BytesIO:
    image_arrays = [numpy.array(Image.open(image)) for image in images]
    for image in images:
        image.seek(0)
    collage_horizontal_arrays = [numpy.hstack(
        image_arrays[i:i + wrap]) for i in range(0, len(image_arrays), wrap)]
    collage_array = numpy.vstack(collage_horizontal_arrays)
    collage_image = Image.fromarray(collage_array)
    collage = io.BytesIO()
    collage_image.save("dalle.png")
    collage.seek(0)
    return collage


async def make_collage(images: list[io.BytesIO], wrap: int) -> io.BytesIO:
    images = await asyncio.get_running_loop().run_in_executor(None, make_collage_sync, images, wrap)
    return images


async def gen(input, interaction: discord.Interaction):
    # Generates images based on prompt given.
    prompt = input
    logging.info(
        f'Got request to generate images with prompt "{prompt}" from user')

    images = None
    attempt = 0
    while not images:
        if attempt > 0:
            logging.warning(
                f'Image generate request failed on attempt {attempt} for prompt "{prompt}" issued by user')
        attempt += 1
        images = await generate_images(prompt)

    logging.info(
        f'Successfully generated images with prompt "{prompt}" from user on attempt {attempt}')
    collage = await make_collage(images, 3)
    collage = discord.File(collage, filename=f'collage.{config["COLLAGE_FORMAT"]}')
    images = [discord.File(images[i], filename=f'{i}.jpg') for i in range(len(images))]
    collage1 = Image.open("dalle.png")
    collage1.show()  # interaction.followup.send(f'`{prompt}`', file=collage,
    # view=ImageSelectView(collage, images, timeout=config['IMAGE_SELECT_TIMEOUT']))


def get_config(path: str):
    """
    get_config()
    Parameters:
        - path: full filepath to a .json file that contains config keys and values
    Returns:
        - json.load object of config file
        or
        - dictionary

    Function tries to load a .json file for app config, if no file exists it then tries to use system environment variables and returns dictionary of keys,values for settings.
    """
    try:
        with open(path, 'r') as file:
            config = json.load(file)
        return config
    # If a .json file doesn't exist for settings, use sytem environment variables
    except FileNotFoundError:
        print(f"Warning no config file found at: {path}, attempting to use environment variables.")
        config = {}
        # Iterate through keys in CONFIG_DICT and set using os.getenv
        # Defaults are provided from CONFIG_DICT
        for setting in CONFIG_DICT.keys():
            config[setting] = os.getenv(setting.upper(), default=CONFIG_DICT[setting])
            print(f"{setting}: {config[setting]}")
        return config


# DALLE


# MUSIC

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'worstaudio/worst',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename


@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()


async def play(input, ctx, url):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()
    try:
        server = ctx.message.guild
        voice_channel = server.voice_client

        async with ctx.typing():
            filename = await YTDLSource.from_url(url, loop=bot.loop)
            voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
        await ctx.send('**Now playing:** {}'.format(filename))
    except:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name='pause', help='This command pauses the song')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
    else:
        await ctx.send("The bot is not playing anything at the moment.")


@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        await ctx.send("The bot was not playing anything before this. Use play_song command")


@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.stop()
    else:
        await ctx.send("The bot is not playing anything at the moment.")


save_path = ("temp.wav")




@bot.event
async def on_ready():
    # there are no english models for large

    model = "tiny.en"
    audio_model = whisper.load_model(model)

    english = False
    verbose = False

    # load the speech recognizer and set the initial energy threshold and pause threshold
    r = sr.Recognizer()
    r.energy_threshold = 300
    r.pause_threshold = 0.5
    r.dynamic_energy_threshold = True

    with sr.Microphone(sample_rate=48000) as source:
        print("Say something!")
        while True:
            # get and save audio to wav file
            audio = r.listen(source)
            data = io.BytesIO(audio.get_wav_data())
            audio_clip = AudioSegment.from_file(data)
            audio_clip.export(save_path, format="wav")

            if english:
                result = audio_model.transcribe(save_path, language='english')
            else:
                result = audio_model.transcribe(save_path)

            if not verbose:
                prompt1 = result["text"]
                print("You: " + prompt1)

                if "Generate" in prompt1:
                    print("$ Dalle2 started")
                    prompt3 = prompt1.replace("Generate", "")
                    await gen(prompt3, interaction=discord.Interaction)

            ai = await getAIResponse(prompt1)


@bot.event
async def getAIResponse(input):
    api_json = openai.Completion.create(
        model="text-curie-001",
        prompt=input,
        temperature=0.5,
        max_tokens=10,
        top_p=1,
        frequency_penalty=0.5,
        presence_penalty=0,
    )

    response = api_json.choices[0].text.strip('"')

    print(response)

    engine.say(response)
    engine.runAndWait()

    return response


async def on_message(message):
    await message.reply("test")


if __name__ == '__main__':
    # Run bot
    print("Logging in...")
    config = get_config('config.json')
    bot.run(os.environ["DISCORD_TOKEN"])
