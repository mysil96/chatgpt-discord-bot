import discord
from discord.ext import commands
from discord.utils import get
from gtts import gTTS

import asyncio



intents = discord.Intents.all()


bot = commands.Bot(command_prefix='', intents=intents)

@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))

@bot.command()
async def speak(ctx, *, text):

    voice_channel = ctx.author.voice.channel
    if voice_channel is None:
        await ctx.send("You are not connected to any voice channel.")
        return

    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if voice_client is None:
        voice_client = await voice_channel.connect()
    else:
        await voice_client.move_to(voice_channel)

    tts = gTTS(text=text, lang='no')
    tts.save('output.mp3')
    audio_source = discord.FFmpegPCMAudio('output.mp3')

    voice_client.play(audio_source)
    while voice_client.is_playing():
        await asyncio.sleep(1)

    voice_client.stop()
    await voice_client.disconnect()

bot.run('MTAyODQwMzQ4NzgzNjQ4MzYxNA.GsOVe8.JelDyfm7zLRg1ynsZcTcsURed4I2_4Mu49ObU4')
