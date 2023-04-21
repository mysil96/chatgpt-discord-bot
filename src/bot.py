import os
import re
import discord
import tiktoken
from discord.ext import commands
from discord.ext.commands import is_owner, Context
from src import log
from src import config
from src.utils import send_message, num_tokens_from_string

discord_token = os.getenv("discord_token", default=None)
logger = log.logger
default_system_text = config.general_sys
archived_sys_text = ""

# Define function to run Discord bot
def run_discord_bot():
    # Set up Discord intents and activity
    intents = discord.Intents.default()
    intents.message_content = True
    activity = discord.Activity(
        type=discord.ActivityType.watching, name="you play with yourself"
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
        print(f"\n\x1b[32m+----- {client.user} is now running! -----+\n")

    # Define event handler for when a message is received
    @client.event
    async def on_message(message):
        global archived_sys_text

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
                system_text = default_system_text
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
                if message.attachments:
                    attachment = message.attachments[0]
                    file_content = await attachment.read()
                    file_text = file_content.decode("utf-8")

                    if file_text.strip():  # Check if file contains text
                        input_text += ("\n\n" if not input_text.strip() else "") + f"Here is the following text from a file:\n\n{file_text}"
            except ValueError:
                await message.channel.send("Error: No '/input' given.")
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
            logger.info(
                f"User input:\nUSERNAME: {username}\n{user_message}\n"
            )

            # Add system message if conversation history is empty
            if (not config.conversation_history) or (archived_sys_text != system_text):
                config.conversation_history.append({"role": "system", "content": system_text})
                archived_sys_text = system_text

            # Add user input to conversation history
            config.conversation_history.append({"role": "user", "content": input_text})

            unique_roles = set(entry["role"] for entry in array)
            combined_text = "".join(["partly" for _ in unique_roles]) + "".join([entry["content"] for entry in config.conversation_history])

            num_tokens = num_tokens_from_string(combined_text)
            if num_tokens >= 7500:
                await message.channel.send(f"Your input is too large to process ({num_tokens} tokens). Please shorten your input, or clear chat history.")
                logger.warning(
                    f"{username} tried to send input containing {num_tokens} tokens, which is too large to process."
                )
            # Send message with system text and input text
            await send_message(message, system_text, input_text)

    # Define command to toggle private access
    @client.tree.command(name="private", description="Toggle private bot messages")
    async def private(interaction: discord.Interaction):
        # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        # If not already in private mode, switch to private mode and send message
        if not config.is_private:
            config.is_private = not config.is_private
            logger.info(f"{interaction.user} switched to private mode.")
            await interaction.followup.send(
                "> **Info: Next, the response will be sent via private message. If you want to switch back to public mode, use `/public`**"
            )
        # If already in private mode, send message
        else:
            await interaction.followup.send(
                "> **Warn:** You already on private mode. If you want to switch to **public** mode, use **`/public`**"
            )
            logger.warning(
                f"{interaction.user} attempted to switch to private mode, but was already on private mode"
            )

    # Define command to toggle public access
    @client.tree.command(name="public", description="Toggle public bot messages")
    async def public(interaction: discord.Interaction):
        # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        # If in private mode, switch to public mode and send message
        if config.is_private:
            config.is_private = not config.is_private
            await interaction.followup.send(
                "> **Info: Next, the response will be sent to the channel directly. If you want to switch back to private mode, use `/private`**"
            )
            logger.info(f"{interaction.user} switched to public mode.")
        # If already in public mode, send message
        else:
            await interaction.followup.send(
                "> **Warn:** You're already on public mode. If you want to switch to **private** mode, use **`/private`**"
            )
            logger.warning(
                f"{interaction.user} attempted to switch to public mode, but was already on public mode"
            )
            
    # Define command to switch OpenAI models
    @client.tree.command(name="set_model", description='Switch between OpenAI models "gpt-3.5-turbo" or "gpt-4".')
    async def set_model(interaction: discord.Interaction, new_model: str):
        # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        
        # Define regular expressions to recognize variations of model names
        gpt_3_5_regex = re.compile(r"^gpt[-\s_]*3\.?[5]*$|^3\.?[5]*$", re.IGNORECASE)
        gpt_4_regex = re.compile(r"^gpt[-\s_]*4$|^4$", re.IGNORECASE)
        
        # Check if the new model matches either of the regular expressions
        if gpt_3_5_regex.match(new_model):
            # Check if the current model is already set to the new model
            if config.gpt_model == "gpt-3.5-turbo":
                await interaction.followup.send(
                "> **Info:** You're already using GPT-3.5."
                )
                # Log a warning message
                logger.warning(
                f"{interaction.user} attempted to switch to GPT-3.5, but was already using GPT-3.5"
                )
            else:
                # Set the new model
                config.gpt_model = "gpt-3.5-turbo"
                await interaction.followup.send("OpenAI model successfully set to **GPT-3.5**.")
        elif gpt_4_regex.match(new_model):
            # Check if the current model is already set to the new model
            if config.gpt_model == "gpt-4":
                await interaction.followup.send(
                "> **Info:** You're already using GPT-4."
                )
                # Log a warning message
                logger.warning(
                f"{interaction.user} attempted to switch to GPT-4, but was already using GPT-4"
                )
            else:
                # Set the new model
                config.gpt_model = "gpt-4"
                await interaction.followup.send("OpenAI model successfully set to **GPT-4**.")
        else:
            # Send an error message if the model name is invalid
            await interaction.followup.send("**Error:** Invalid model specified. Please type either '**gpt-3.5**' or '**gpt-4**' (without quotes).")

    # Define command to get current OpenAI model
    @client.tree.command(name="get_model", description="Get the current OpenAI model being used (GPT-4 by default).")
    async def get_model(interaction: discord.Interaction):
        # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        
        model_name = "GPT-3.5" if config.gpt_model == "gpt-3.5-turbo" else "GPT-4"

        # Return the current OpenAI model
        await interaction.followup.send(f"Current OpenAI model: {model_name}")
        logger.info(f"{interaction.user} requested the current OpenAI model: {config.gpt_model}")

    # Define command to change default system text to programming assistant
    @client.tree.command(name="programming_assistant", description="Sets the default system text for the AI to be a programming assistant.")
    async def programming_assistant(interaction: discord.Interaction):
        # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        
        # Set default system text to programming preset
        if default_system_text != config.programming_sys:
            default_system_text = config.programming_sys
            await interaction.followup.send(
                "> **Info:** Default system text changed to **PROGRAMMER** preset."
            )
            logger.info(f"{interaction.user} switched to PROGRAMMER preset.")
        # If already in public mode, send message
        else:
            await interaction.followup.send(
                "> **Warn:** You're already using the **PROGRAMMER** preset. To switch back to the general preset, use /general_assistant."
            )
            logger.warning(
                f"{interaction.user} attempted to switch to PROGRAMMER preset, but was already using that preset"
            )

    # Define command to change default system text to scientific assistant
    @client.tree.command(name="scientific_assistant", description="Sets the default system text for the AI to be a scientific assistant.")
    async def scientific_assistant(interaction: discord.Interaction):
        # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        
        # Set default system text to programming preset
        if default_system_text != config.scientific_sys:
            default_system_text = config.scientific_sys
            await interaction.followup.send(
                "> **Info:** Default system text changed to **SCIENTIFIC** preset."
            )
            logger.info(f"{interaction.user} switched to SCIENTIFIC preset.")
        # If already in public mode, send message
        else:
            await interaction.followup.send(
                "> **Warn:** You're already using the **SCIENTIFIC** preset. To switch back to the general preset, use /general_assistant."
            )
            logger.warning(
                f"{interaction.user} attempted to switch to SCIENTIFIC preset, but was already using that preset"
            )

    # Define command to change default system text to ELI5 assistant
    @client.tree.command(name="eli5_assistant", description="Sets the default system text for the AI to be an ELI5 assistant.")
    async def eli5_assistant(interaction: discord.Interaction):
        # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        
        # Set default system text to programming preset
        if default_system_text != config.eli5_sys:
            default_system_text = config.eli5_sys
            await interaction.followup.send(
                "> **Info:** Default system text changed to **ELI5** preset."
            )
            logger.info(f"{interaction.user} switched to ELI5 preset.")
        # If already in public mode, send message
        else:
            await interaction.followup.send(
                "> **Warn:** You're already using the **ELI5** preset. To switch back to the general preset, use /general_assistant."
            )
            logger.warning(
                f"{interaction.user} attempted to switch to ELI5 preset, but was already using that preset"
            )

    # Define command to change default system text to general assistant
    @client.tree.command(name="general_assistant", description="Sets the default system text for the AI to be a general assistant.")
    async def general_assistant(interaction: discord.Interaction):
        # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        
        # Set default system text to programming preset
        if default_system_text != config.general_sys:
            default_system_text = config.general_sys
            await interaction.followup.send(
                "> **Info:** Default system text changed to **GENERAL** preset."
            )
            logger.info(f"{interaction.user} switched to GENERAL preset.")
        # If already in public mode, send message
        else:
            await interaction.followup.send(
                "> **Warn:** You're already using the **GENERAL** preset."
            )
            logger.warning(
                f"{interaction.user} attempted to switch to GENERAL preset, but was already using that preset"
            )

    # Reset chat history
    @client.tree.command(name="reset_chat", description="Reset the current chat and chat history.")
    async def reset_chat(interaction: discord.Interaction):
        # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        
        config.conversation_history = []

        # Return the current OpenAI model
        await interaction.followup.send(f"The current conversation and all corresponding history has been wiped.")
        logger.info(f"{interaction.user} reset their convo and corresponding convo history")
    
    # Toggle chat history on or off
    @client.tree.command(name="toggle_chat_history", description="Toggles chat history on or off.")
    async def toggle_chat_history(interaction: discord.Interaction):
        # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        
        # Toggle conversation history on or off
        config.toggle_conversation_history = False if config.toggle_conversation_history == True else False
        config.conversation_history = []

        # Return the current OpenAI model
        await interaction.followup.send(f"Chat history has been turned " + ("on" if config.toggle_conversation_history == True else "off") + ". Chat history has been wiped.")
        logger.info(f"{interaction.user} toggled convo history" + ("on" if config.toggle_conversation_history == True else "off"))

    # Run Discord bot with token
    if not discord_token:
        logger.error("Error: discord_token environment variable not set.")
        return
    
    client.run(discord_token)
