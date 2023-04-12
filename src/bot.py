import os
import re
import discord
from discord.ext import commands
from discord.ext.commands import is_owner, Context
from src import log
from src import config
from src.utils import send_message

discord_token = os.getenv("discord_token", default=None)
logger = log.logger

# Define function to run Discord bot
def run_discord_bot():
    # Set up Discord intents and activity
    intents = discord.Intents.default()
    intents.message_content = True
    activity = discord.Activity(
        type=discord.ActivityType.watching, name="/private | /public"
    )
    # Create Discord bot with command prefix, intents, and activity
    client = commands.Bot(command_prefix="/", intents=intents, activity=activity)

    # Define event handler for when bot is ready
    @client.event
    async def on_ready():
        # Sync tree commands and print number of commands synced
        synced = await client.tree.sync()
        logger.debug("{} commands synced".format(len(synced)))

        # Print that bot is up and running
        print(f"\n\x1b[32m+----- {client.user} is now running! -----+\x1b[0m")

    # Define event handler for when a message is received
    @client.event
    async def on_message(message):
        # Ignore messages sent by the bot itself
        if message.author == client.user:
            return

        # Check if bot is mentioned in the message
        if f"@{client.user.name}" in message.content or client.user in message.mentions:
            # Split message content into arguments
            args = message.content.split()

            # Check if "/input" command is present in message
            if "/input" not in args:
                await message.channel.send("Error: No input given.")
                return
            # Check if "/input" command appears after mention of bot
            elif not args.index(client.user.mention) < args.index("/input"):
                await message.channel.send("Error: Invalid command format.")
                return
            # Check if "/system" command is present in message
            elif "/system" not in args:
                system_text = (
                    "You're a highly capable assistant trained to help users with every possible task."
                )
            # Check if "/system" command appears after mention of bot and before "/input" command
            elif "/system" in args:
                if not (
                    args.index(client.user.mention)
                    < args.index("/system")
                    < args.index("/input")
                ):
                    await message.channel.send("Error: Invalid command format.")
                    return
                else:
                    try:
                        system_text = args[
                            args.index("/system") + 1 : args.index("/input")
                        ]
                        system_text = " ".join(system_text)
                    except ValueError:
                        await message.channel.send("Error: No input given.")
                        return

            # Get input text from message
            try:
                input_text = args[args.index("/input") + 1 :]
                input_text = " ".join(input_text)
            except ValueError:
                await message.channel.send("Error: No input given.")
                return

            # Check if system text is empty
            if not system_text.strip():
                await message.channel.send("Error: No system text given.")
                return
            # Check if input text is empty
            if not input_text.strip():
                await message.channel.send("Error: No input text given.")
                return

            # Get username, user message, and channel from message
            username = str(message.author)
            user_message = str(message.content)
            channel = str(message.channel)

            # Format user message and log it
            user_message = "SYSTEM: " + system_text + "\nINPUT: " + input_text
            print("\n+=====   Input to GPT-4 recognized   =====+\n")
            logger.info(
                f"\x1b[31m{username}\x1b[0m : \n'{user_message}' ({channel})\n"
            )

            # Send message with system text and input text
            await send_message(message, system_text, input_text)

    # Define command to toggle private access
    @client.tree.command(name="private", description="Toggle private bot messages")
    async def private(interaction: discord.Interaction):
        # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        # If not already in private mode, switch to private mode and send message
        if not config.isPrivate:
            config.isPrivate = not config.isPrivate
            logger.info(f"{interaction.user} \x1b[31mswitched to private mode.\x1b[0m")
            await interaction.followup.send(
                "> **Info: Next, the response will be sent via private message. If you want to switch back to public mode, use `/public`**"
            )
        # If already in private mode, send message
        else:
            await interaction.followup.send(
                "> **Warn:** You already on private mode. If you want to switch to **public** mode, use **`/public`**"
            )
            logger.warning(
                f"{interaction.user} \x1b[31mattempted to switch to private mode, but was already on private mode\x1b[0me"
            )

    # Define command to toggle public access
    @client.tree.command(name="public", description="Toggle public bot messages")
    async def public(interaction: discord.Interaction):
        # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        # If in private mode, switch to public mode and send message
        if config.isPrivate:
            config.isPrivate = not config.isPrivate
            await interaction.followup.send(
                "> **Info: Next, the response will be sent to the channel directly. If you want to switch back to private mode, use `/private`**"
            )
            logger.info(f"{interaction.user} \x1b[31mSwitched to public mode.\x1b[0m")
        # If already in public mode, send message
        else:
            await interaction.followup.send(
                "> **Warn:** You're already on public mode. If you want to switch to **private** mode, use **`/private`**"
            )
            logger.warning(
                f"{interaction.user} \x1b[31mattempted to switch to public mode, but was already on public mode\x1b[0m"
            )
            
    # Define command to switch OpenAI models
    @client.tree.command(name="set_model", description='Switch between OpenAI models "gpt-3.5-turbo" or "gpt-4".')
    async def model(interaction: discord.Interaction, new_model: str):
        # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        
        # Define regular expressions to recognize variations of model names
        gpt_3_5_regex = re.compile(r"^gpt[-\s_]*3\.?[5]*$|^3\.?[5]*$", re.IGNORECASE)
        gpt_4_regex = re.compile(r"^gpt[-\s_]*4$|^4$", re.IGNORECASE)
        
        # Check if the new model matches either of the regular expressions
        if gpt_3_5_regex.match(new_model):
            # Check if the current model is already set to the new model
            if config.gptModel == "gpt-3.5-turbo":
                await interaction.followup.send(
                "> **Info:** You're already using GPT-3.5."
                )
                # Log a warning message
                logger.warning(
                f"{interaction.user} \x1b[31mattempted to switch to GPT-3.5, but was already using GPT-3.5\x1b[0m"
                )
            else:
                # Set the new model
                config.gptModel = "gpt-3.5-turbo"
                await interaction.followup.send("OpenAI model successfully set to **GPT-3.5**.")
        elif gpt_4_regex.match(new_model):
            # Check if the current model is already set to the new model
            if config.gptModel == "gpt-4":
                await interaction.followup.send(
                "> **Info:** You're already using GPT-4."
                )
                # Log a warning message
                logger.warning(
                f"{interaction.user} \x1b[31mattempted to switch to GPT-4, but was already using GPT-4\x1b[0m"
                )
            else:
                # Set the new model
                config.gptModel = "gpt-4"
                await interaction.followup.send("OpenAI model successfully set to **GPT-4**.")
        else:
            # Send an error message if the model name is invalid
            await interaction.followup.send("**Error:** Invalid model specified. Please type either '**gpt-3.5**' or '**gpt-4**' (without quotes).")


    # Define command to get current OpenAI model
    @client.tree.command(name="get_model", description="Get the current OpenAI model being used (GPT-4 by default).")
    async def current_model(interaction: discord.Interaction):
        # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        
        model_name = "GPT-3.5" if config.gptModel == "gpt-3.5-turbo" else "GPT-4"

        # Return the current OpenAI model
        await interaction.followup.send(f"Current OpenAI model: {model_name}")
        logger.info(f"{interaction.user} requested the current OpenAI model: {config.gptModel}")

    # Run Discord bot with token
    if not discord_token:
        logger.error("Error: discord_token environment variable not set.")
        return
    
    client.run(discord_token)
