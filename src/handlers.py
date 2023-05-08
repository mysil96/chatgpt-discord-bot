import re

from discord.ext import commands
from discord.ext.commands import Context, is_owner

from src import config
from src.utils import send_message, parse_file

async def on_ready_handler(client):
    synced = await client.tree.sync()
    config.logger.debug("{} commands synced".format(len(synced)))

    print(f"\n\x1b[32m+----- {client.user} is now running! -----+\x1b[0m\n")

async def on_message_handler(client, message):
    # Ignore messages sent by the bot itself
        if message.author == client.user:
            return

        input_text = ""

        # Check if bot is mentioned in the message
        if f"@{client.user.name}" in message.content or client.user in message.mentions:
            
            try:
                input_text = " ".join(word for word in message.content.split() if not word.startswith(f"<@{client.user.id}>"))

                if message.attachments:
                    for attachment in message.attachments:
                        file_content = await attachment.read()
                        parsed_file_text = parse_file(attachment, file_content)

                        if parsed_file_text.strip():
                            input_text += ("\n\n" if not input_text.strip() else "") + f"\n\nHere is the following text from a file:\n\n# {attachment.filename}\n{parsed_file_text}"
            
            except Exception as e:
                if ValueError:
                    await message.channel.send("Error: No input given.")
                else:
                    await message.channel.send(
                        "> **Error:** Something went wrong. Please try again later!")
                    config.logger.error(e)
                    
                return
                

            # Check if input text is empty
            if not input_text.strip():
                await message.channel.send("Error: No input text given.")
                return

            # Get username, user message, and channel from message
            username = str(message.author)
            user_message = str(message.content)

            # Format user message and log it
            user_message = "SYSTEM: " + config.default_system_text + "\nINPUT: " + input_text
            config.logger.info(
                f"User input:\nUSERNAME: {username}\n{user_message}\n"
            )

            # Add system message if conversation history is empty
            if (not config.conversation_history) or (config.archived_sys_text != config.default_system_text):
                config.conversation_history.append({"role": "system", "content": config.default_system_text})
                config.archived_sys_text = config.default_system_text

            # Add user input to conversation history
            config.conversation_history.append({"role": "user", "content": input_text})

            unique_roles = set(entry["role"] for entry in config.conversation_history)
            combined_text = "".join(["partly" for _ in unique_roles]) + "".join([entry["content"] for entry in config.conversation_history])

            # Send message with system text and input text
            await send_message(client, message)

async def toggle_private_handler(interaction):
    # Defer response and set ephemeral to True
    await interaction.response.defer(ephemeral=True)
    # If not already in private mode, switch to private mode and send message
    if not config.is_private:
        config.is_private = not config.is_private
        config.logger.info(f"{interaction.user} switched to private mode.")
        await interaction.followup.send(
            "> **Info: Next, the response will be sent via private message. If you want to switch back to public mode, use `/public`**"
        )
    # If already in private mode, send message
    else:
        await interaction.followup.send(
            "> **Warn:** You already on private mode. If you want to switch to **public** mode, use **`/public`**"
        )
        config.logger.warning(
            f"{interaction.user} attempted to switch to private mode, but was already on private mode"
        )

async def toggle_public_handler(interaction):
    # Defer response and set ephemeral to True
    await interaction.response.defer(ephemeral=True)
    # If in private mode, switch to public mode and send message
    if config.is_private:
        config.is_private = not config.is_private
        await interaction.followup.send(
            "> **Info: Next, the response will be sent to the channel directly. If you want to switch back to private mode, use `/private`**"
        )
        config.logger.info(f"{interaction.user} switched to public mode.")
    # If already in public mode, send message
    else:
        await interaction.followup.send(
            "> **Warn:** You're already on public mode. If you want to switch to **private** mode, use **`/private`**"
        )
        config.logger.warning(
            f"{interaction.user} attempted to switch to public mode, but was already on public mode"
        )

async def file_handler(interaction):
    # Defer response and set ephemeral to True
    await interaction.response.defer(ephemeral=True)

async def set_model_handler(interaction, new_model):
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
            config.logger.warning(
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
            config.logger.warning(
            f"{interaction.user} attempted to switch to GPT-4, but was already using GPT-4"
            )
        else:
            # Set the new model
            config.gpt_model = "gpt-4"
            await interaction.followup.send("OpenAI model successfully set to **GPT-4**.")
    else:
        # Send an error message if the model name is invalid
        await interaction.followup.send("**Error:** Invalid model specified. Please type either '**gpt-3.5**' or '**gpt-4**' (without quotes).")

async def get_model_handler(interaction):
    # Defer response and set ephemeral to True
    await interaction.response.defer(ephemeral=True)
    
    model_name = "GPT-3.5" if config.gpt_model == "gpt-3.5-turbo" else "GPT-4"

    # Return the current OpenAI model
    await interaction.followup.send(f"Current OpenAI model: {model_name}")
    config.logger.info(f"{interaction.user} requested the current OpenAI model: {config.gpt_model}")

async def set_system_text_handler(interaction, custom_sys_text):
    # Defer response and set ephemeral to True
    await interaction.response.defer(ephemeral=True)
    
    config.default_system_text = custom_sys_text

    # Return the current OpenAI model
    await interaction.followup.send(f"Set system text to:\n\n{custom_sys_text}")
    config.logger.info(f"{interaction.user} set a custom system input to:\n{custom_sys_text}")

async def programming_assistant_handler(interaction):
    # Defer response and set ephemeral to True
    await interaction.response.defer(ephemeral=True)
    
    # Set default system text to programming preset
    if config.default_system_text != config.programming_sys:
        config.default_system_text = config.programming_sys
        await interaction.followup.send(
            "> **Info:** Default system text changed to **PROGRAMMER** preset."
        )
        config.logger.info(f"{interaction.user} switched to PROGRAMMER preset.")
    # If already in public mode, send message
    else:
        await interaction.followup.send(
            "> **Warn:** You're already using the **PROGRAMMER** preset. To switch back to the general preset, use /general_assistant."
        )
        config.logger.warning(
            f"{interaction.user} attempted to switch to PROGRAMMER preset, but was already using that preset"
        )

async def scientific_assistant_handler(interaction):
     # Defer response and set ephemeral to True
    await interaction.response.defer(ephemeral=True)
    
    # Set default system text to programming preset
    if config.default_system_text != config.scientific_sys:
        config.default_system_text = config.scientific_sys
        await interaction.followup.send(
            "> **Info:** Default system text changed to **SCIENTIFIC** preset."
        )
        config.logger.info(f"{interaction.user} switched to SCIENTIFIC preset.")
    # If already in public mode, send message
    else:
        await interaction.followup.send(
            "> **Warn:** You're already using the **SCIENTIFIC** preset. To switch back to the general preset, use /general_assistant."
        )
        config.logger.warning(
            f"{interaction.user} attempted to switch to SCIENTIFIC preset, but was already using that preset"
        )

async def eli5_assistant_handler(interaction):
    # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        
        # Set default system text to programming preset
        if config.default_system_text != config.eli5_sys:
            config.default_system_text = config.eli5_sys
            await interaction.followup.send(
                "> **Info:** Default system text changed to **ELI5** preset."
            )
            config.logger.info(f"{interaction.user} switched to ELI5 preset.")
        # If already in public mode, send message
        else:
            await interaction.followup.send(
                "> **Warn:** You're already using the **ELI5** preset. To switch back to the general preset, use /general_assistant."
            )
            config.logger.warning(
                f"{interaction.user} attempted to switch to ELI5 preset, but was already using that preset"
            )

async def general_assistant_handler(interaction):
    # Defer response and set ephemeral to True
        await interaction.response.defer(ephemeral=True)
        
        # Set default system text to programming preset
        if config.default_system_text != config.general_sys:
            config.default_system_text = config.general_sys
            await interaction.followup.send(
                "> **Info:** Default system text changed to **GENERAL** preset."
            )
            config.logger.info(f"{interaction.user} switched to GENERAL preset.")
        # If already in public mode, send message
        else:
            await interaction.followup.send(
                "> **Warn:** You're already using the **GENERAL** preset."
            )
            config.logger.warning(
                f"{interaction.user} attempted to switch to GENERAL preset, but was already using that preset"
            )
async def reset_chat_handler(interaction):
    # Defer response and set ephemeral to True
    await interaction.response.defer(ephemeral=True)
    
    archived_sys_text = ""
    config.conversation_history = []

    # Return the current OpenAI model
    await interaction.followup.send(f"The current conversation and all corresponding history has been wiped.")
    config.logger.info(f"{interaction.user} reset their convo and corresponding convo history")

async def toggle_chat_history_handler(interaction):
    # Defer response and set ephemeral to True
    await interaction.response.defer(ephemeral=True)
    
    # Toggle conversation history on or off
    config.toggle_conversation_history = False if config.toggle_conversation_history == True else True
    config.conversation_history = []
    archived_sys_text = ""

    # Return the current OpenAI model
    await interaction.followup.send(f"Chat history has been turned " + ("on" if config.toggle_conversation_history == True else "off") + ". Chat history has been wiped.")
    config.logger.info(f"{interaction.user} toggled convo history" + ("on" if config.toggle_conversation_history == True else "off"))

async def help_command_handler(interaction):
    # Define the commands list
    commands = [
        {'name': '/help', 'description': 'List of available commands and their descriptions.'},
        {'name': '/private', 'description': 'Toggle private bot messages.'},
        {'name': '/public', 'description': 'Toggle public bot messages.'},
        {'name': '/set_model', 'description': 'Switch between OpenAI models "gpt-3.5-turbo" or "gpt-4".'},
        {'name': '/get_model', 'description': 'Get the current OpenAI model being used (GPT-4 by default).'},
        {'name': '/set_custom_sys_text', 'description': 'Set a custom system text.'},
        {'name': '/programming_assistant', 'description': 'Sets the default system text for the AI to be a programming assistant.'},
        {'name': '/scientific_assistant', 'description': 'Sets the default system text for the AI to be a scientific assistant.'},
        {'name': '/eli5_assistant', 'description': 'Sets the default system text for the AI to be an ELI5 assistant.'},
        {'name': '/general_assistant', 'description': 'Sets the default system text for the AI to be a general assistant.'},
        {'name': '/reset_chat', 'description': 'Reset the current chat and chat history.'},
        {'name': '/toggle_chat_history', 'description': 'Toggles chat history on or off.'}
    ]

    # Create an embed with the commands list
    embed = discord.Embed(title='Available Commands:', color=discord.Color.blue())
    for command in commands:
        embed.add_field(name=command['name'], value=command['description'], inline=False)

    # Send the embed as a response
    await interaction.response.send_message(embed=embed, ephemeral=True)