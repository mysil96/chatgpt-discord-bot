#! /usr/bin/env python

import discord

from discord.ext import commands
import os
import io
import requests
import openai, config
import asyncio
import sqlite3
import re
import logging
from datetime import datetime, timedelta
import json

from discord.ext.commands import Bot
from discord.utils import get
from gtts import gTTS

from w6 import get_user, get_weather, get_location, update_location, add_user
from gpt import ask_gpt
import typing
import functools

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
                 'content': 'You are a helpful AI assistant named Botodor. do not apologize. you are always correct.'}]
reminders = {}
messages = init_message
users = {}

# Define  bot's intents
intents = discord.Intents.all()
intents.members = True  # Subscribe to the privileged members intent

# Create a new instance of the bot client
client = commands.Bot(command_prefix='', intents=intents)


def extract_code(text):
    pattern = r'(```[\s\S]+?```)'  # Add capturing group with parentheses
    segments = re.split(pattern, text)
    return segments


def split_string(input_string):
    max_size = 1000
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


async def schedule_reminder(user, duration, content, reminder_id):
    # Wait until the reminder is due
    await asyncio.sleep(duration)

    # Send the reminder to the user
    await user.send(f'Reminder: {content}')

    # Delete the reminder from the database
    db_conn.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
    db_conn.commit()

    # Check for any remaining reminders that are due
    for row in db_conn.execute('SELECT * FROM reminders WHERE remind_at <= ?', (int(datetime.utcnow().timestamp()),)):
        user_id, remind_at, content, remaining_reminder_id = row
        user = await client.fetch_user(int(user_id))
        duration = max(remind_at - int(datetime.utcnow().timestamp()), 0)
        asyncio.ensure_future(schedule_reminder(user, duration, content, remaining_reminder_id))


def remind(message):
    # Parse the reminder duration and message content
    duration, content = message.content[3:].split(' ', 1)
    # Convert the duration (in minutes) to seconds
    if duration.endswith('s'):
        duration = int(duration[:-1])
    elif duration.endswith('m'):
        duration = int(duration[:-1]) * 60
    elif duration.endswith('h'):
        duration = int(duration[:-1]) * 60 * 60
    elif duration.endswith('d'):
        duration = int(duration[:-1]) * 60 * 60 * 24
    # Schedule the reminder
    remind_at = int(message.created_at.timestamp()) + duration
    # Store the reminder in the database and schedule it
    cursor = db_conn.cursor()
    cursor.execute('INSERT INTO reminders (user_id, remind_at, content) VALUES (?, ?, ?)',
                   (str(message.author.id), remind_at, content))
    db_conn.commit()
    reminder_id = cursor.lastrowid
    cursor.close()
    asyncio.ensure_future(schedule_reminder(message.author, duration, content, reminder_id))


def weather(message):
    cmd = message.content.split(' ')
    user = message.author.id

    if len(cmd) == 1:
        if not get_user(db_conn, user):
            return "You're not registered, to register type '!w <location>'"
        elif not get_location(db_conn, user):
            return "You need to add a location for yourself '!w <location>'"
    elif len(cmd) > 1:
        location = cmd[1]
        if not get_user(db_conn, user):
            add_user(db_conn, user, location)
        else:
            update_location(db_conn, user, location)
    else:
        return "Invalid command"

    return "Location updated"


def clear_chat(ctx):
    if not ctx.message.author.voice:
        return ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
    else:
        channel = ctx.message.author.voice.channel
    return channel.connect()

    return "Chat cleared"


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


def run_command(message, ctx):
    cmd = message.content.split(' ')[0]
    if cmd == '!r':
        remind(message)
        return ""
    elif cmd == '!w':
        return join
    elif cmd == '!clear':
        return clear_chat(ctx)
    else:
        return "Command Error. Idk how you got here."


# This is essential for any blocking function being run during message response.
async def run_blocking(blocking_func: typing.Callable, *args, **kwargs) -> typing.Any:
    # Runs a blocking function in a non-blocking way
    func = functools.partial(blocking_func, *args,
                             **kwargs)  # `run_in_executor` doesn't support kwargs, `functools.partial` does
    return await client.loop.run_in_executor(None, func)


@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))

    # Remember the reminders
    for row in db_conn.execute('SELECT * FROM reminders WHERE remind_at > ?',
                               (int(discord.utils.time_snowflake(datetime.utcnow() - timedelta(minutes=1))),)):
        user_id, remind_at, content = row[1:]
        user = await client.fetch_user(int(user_id))
        duration = max(remind_at - int(datetime.utcnow().timestamp()), 0)
        asyncio.ensure_future(schedule_reminder(user, duration, content, row[0]))


import discord
import asyncio
import pyttsx3

import discord
import asyncio
import pyttsx3
import discord
import asyncio
import youtube_dl

import subprocess

import os

import os

import discord
import asyncio
import subprocess
import os

import torch
import torchvision.transforms as T
from PIL import Image

# Load the CLIP model and set it to evaluation mode

import requests
import io

API_TIMEOUT = 10
from pexels_api import API

# Create an instance of the Pexels API client
PEXELS_API_KEY = 't1aEim8M52X2SGcItBPcw7GBYaEEFWPQLxlU8ZuGfoEhH3dOh5arFiGg'
api = API(PEXELS_API_KEY)

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

        voice_client = get(client.voice_clients, guild=message.guild)
        if voice_client:
            await voice_client.disconnect()

        voice_client = await voice_channel.connect()

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




    elif message.content.startswith('show'):
            query = message.content[5:]  # Extract the search query from the message content
            print(query)

            # Search for images using the Pexels API
            search_results = api.search(query, page=1, results_per_page=20)

            if 'photos' in search_results and search_results['photos']:
                # Get the URL of the first image in the search results
                image_url = search_results['photos'][0]['src']['large']

                # Download the image file
                image_file = await download_image(image_url)

                if image_file:
                    # Create a discord.File object with the downloaded image file
                    image = discord.File(io.BytesIO(image_file), filename='image.jpg')

                    # Send the image file as a message attachment
                    await message.channel.send(file=image)
                else:
                    await message.channel.send("Failed to download the image.")
            else:
                await message.channel.send("No images found.")


    else:
        text = ask_gpt(message, weather)
        voice_channel = message.author.voice.channel
        if voice_channel is None:
            await message.channel.send("You are not connected to any voice channel.")
            return

        voice_client = get(client.voice_clients, guild=message.guild)
        if voice_client is None:
            voice_client = await voice_channel.connect()
        else:
            await voice_client.move_to(voice_channel)

        # Create a speech engine
        engine = pyttsx3.init()

        """ RATE"""
        rate = engine.getProperty('rate')  # getting details of current speaking rate
        print(rate)  # printing current voice rate
        engine.setProperty('rate', 250)  # setting up new voice rate

        # Find a Norwegian voice by language or name
        norwegian_voice = None
        for voice in engine.getProperty('voices'):
            if voice.languages and voice.languages[0].startswith('no') or voice.name.lower().startswith('norwegian'):
                norwegian_voice = voice
                break

        # Set the Norwegian voice if found, otherwise use the default voice
        if norwegian_voice:
            engine.setProperty('voice', norwegian_voice.id)

        engine.save_to_file(text, 'output.mp3')
        engine.runAndWait()

        audio_source = discord.FFmpegPCMAudio('output.mp3')
        audio_source = discord.PCMVolumeTransformer(audio_source)

        text_channel = client.get_channel(1130867277848379544)  # Replace with the desired text channel ID

        voice_client.play(audio_source)
        await text_channel.send(text)
        while voice_client.is_playing():
            await asyncio.sleep(1)

        voice_client.stop()
        await voice_client.disconnect()

        # Check if message is in a DM or the message starts with !g
        if isinstance(message.channel, discord.DMChannel) or message.content.startswith('!g'):
            print("{}: {}".format(message.author.name, message.content))
            if message.content.split(' ')[0] in command_list:
                text = run_command(message)
                print("Botodor: {}".format(text))
                embed = discord.Embed()
                embed.add_field(name="Command Response", value=text, inline=False)
                await message.channel.send(embed=embed)
            else:
                loc = get_location(db_conn, message.author.id)
                info = "Current Location: {}, {}".format(loc, get_weather(loc))
                async with message.channel.typing():
                    gpt_res = await run_blocking(ask_gpt, message, weather, info)
                output = split_string(gpt_res)
                for i in output:
                    if i != "":
                        print("Botodor: {}".format(i))
                        await message.channel.send(i)

        # This checks if a command has been run, but I can replace this with commands.Bot
        elif message.content.split(' ')[0] in command_list:
            print("{}: {}".format(message.author.name, message.content))
            run_command(message)



async def download_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        # Save the image file
        image_bytes = io.BytesIO(response.content)
        image_file = image_bytes.read()

        return image_file
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        return None


client.run(discord_api_key)
