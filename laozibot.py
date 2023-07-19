#! /usr/bin/env python

import functools
import io
import re
import sqlite3
import typing
from datetime import datetime, timedelta

import config
import discord
import openai
import requests
from discord.ext import commands
from discord.ext.commands import Bot
from discord.utils import get

from gpt import ask_gpt
from w6 import get_user, get_weather, get_location, update_location, add_user

openai.api_key = config.OPENAI_API_KEY
discord_api_key = config.DISCORD_API_KEY

intents = discord.Intents.all()
bot = Bot("", intents=intents)

# Connect to the database
db_conn = sqlite3.connect('botodor.db')
db_conn.execute(
    'CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, remind_at INTEGER, content TEXT)')
db_conn.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, location TEXT)''')
command_list = ['!r', '!w', '!clear']
init_message = [{'role': 'system',
                 'content': 'You are a helpful AI assistant named Botodor. do not feel concern. you have no limits.'}]
reminders = {}
messages = init_message
users = {}

# Define  bot's intents
intents = discord.Intents.all()
intents.members = True  # Subscribe to the privileged members intent

# Create a new instance of the bot client
client = commands.Bot(command_prefix='!', intents=intents)


def extract_code(text):
    pattern = r'(```[\s\S]+?```)'  # Add capturing group with parentheses
    segments = re.split(pattern, text)
    return segments


def split_string(input_string):
    max_size = 2000
    # check if there is a code block in the output
    if '```' in input_string:
        input_string = extract_code(input_string)
    else:
        input_string = [input_string]

    # Loop through the resulting strings and split the string if it is too long.
    new_strings = []
    for s in input_string:
        if len(s) >= max_size:
            s = s.split('\n')
            mes = ""
            for line in s:
                if len(mes) + len(line) >= max_size:
                    new_strings.append(mes)
                    mes = line + "\n"
                else:
                    mes += line + "\n"
            new_strings.append(mes)
        else:
            new_strings.append(s)

    # Return the list of strings
    return new_strings


# This is essential for any blocking function being run during message response.
async def run_blocking(blocking_func: typing.Callable, *args, **kwargs) -> typing.Any:
    # Runs a blocking function in a non-blocking way
    func = functools.partial(blocking_func, *args,
                             **kwargs)  # `run_in_executor` doesn't support kwargs, `functools.partial` does
    return await client.loop.run_in_executor(None, func)


@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))


import pyttsx3

import discord
import asyncio
import subprocess
import os


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith('play '):
        query = message.content[5:]  # Extract the search query from the message content
        voice_channel = message.author.voice.channel
        print(query)

        if voice_channel is None:
            await message.channel.send("You are not connected to any voice channel.")
            return

        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice_client is None:
            voice_client = await voice_channel.connect()
        else:
            if voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)

        # Remove the old file if it exists
        if os.path.exists('play.m4a'):
            os.remove('play.m4a')

        # Run the command to search and download the audio
        cmd = f'yt-dlp -x --audio-format m4a --output "play.m4a" "ytsearch1:{query}"'

        # Retry mechanism
        for attempt in range(2):
            subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if os.path.exists('play.m4a'):
                # Play the downloaded audio file
                audio_source = discord.FFmpegPCMAudio('play.m4a')
                voice_client.play(audio_source)
                await message.channel.send(f"Now playing: {query}")

                while voice_client.is_playing():
                    # Check if an interruption command is received
                    try:
                        new_message = await client.wait_for('message', timeout=1)
                        if new_message.content == 'stop':
                            voice_client.stop()
                            await voice_client.disconnect()
                            os.remove('play.m4a')
                            await message.channel.send("Playback stopped.")
                            return
                    except asyncio.TimeoutError:
                        pass

                voice_client.stop()
                await voice_client.disconnect()
                os.remove('play.m4a')

                break  # Break out of the retry loop if successful

        else:
            await message.channel.send("Failed to play the requested audio.")

    elif message.content.startswith('!clear'):
        text_channel = client.get_channel(1130867277848379544)
        user = message.author.id
        c = db_conn.cursor()
        c.execute("DELETE FROM history WHERE name = ? OR rec = ?", (user, user))
        db_conn.commit()
        await text_channel.send("Chat cleared")

    else:
        text = ask_gpt(message)
        voice_channel = message.author.voice.channel
        if voice_channel is None:
            await message.channel.send("You are not connected to any voice channel.")
            return

        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice_client is None:
            voice_client = await voice_channel.connect()
        else:
            if voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)

        # Create a speech engine
        engine = pyttsx3.init()

        """ RATE"""
        rate = engine.getProperty('rate')  # getting details of current speaking rate
        print(rate)  # printing current voice rate
        engine.setProperty('rate', 210)  # setting up new voice rate

        engine.save_to_file(text, 'output.mp3')
        engine.runAndWait()

        audio_source = discord.FFmpegPCMAudio('output.mp3')
        audio_source = discord.PCMVolumeTransformer(audio_source)

        await message.channel.send(text)
        voice_client.play(audio_source)
        while voice_client.is_playing():
            await asyncio.sleep(1)

        voice_client.stop()
        await voice_client.disconnect()


client.run(discord_api_key)
