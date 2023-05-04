import os
import re
import discord
import tiktoken
from discord.ext import commands
from discord.ext.commands import is_owner, Context
from src import config
from src import handlers
from src.utils import send_message

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
        await handlers.on_ready_handler(client)

    # Define event handler for when a message is received
    @client.event
    async def on_message(message):
        await handlers.on_message_handler(client, message)

    # Define command to toggle private access
    @client.tree.command(name="private", description="Toggle private bot messages")
    async def private(interaction: discord.Interaction):
        await handlers.toggle_private_handler(interaction)

    # Define command to toggle public access
    @client.tree.command(name="public", description="Toggle public bot messages")
    async def public(interaction: discord.Interaction):
        await handlers.toggle_public_handler(interaction)
            
    # Define command to switch OpenAI models
    @client.tree.command(name="set_model", description='Switch between OpenAI models "gpt-3.5-turbo" or "gpt-4".')
    async def set_model(interaction: discord.Interaction, new_model: str):
        await handlers.set_model_handler(interaction, new_model)

    # Define command to get current OpenAI model
    @client.tree.command(name="get_model", description="Get the current OpenAI model being used (GPT-4 by default).")
    async def get_model(interaction: discord.Interaction):
        await handlers.get_model_handler(interaction)

    # Define command to set user's own system text
    @client.tree.command(name="set_system_text", description="Change the system field to a custom input.")
    async def programming_assistant(interaction: discord.Interaction, custom_sys_text: str):
        await handlers.set_system_text_handler(interaction, custom_sys_text)

    # Define command to change default system text to programming assistant
    @client.tree.command(name="programming_assistant", description="Sets the default system text for the AI to be a programming assistant.")
    async def programming_assistant(interaction: discord.Interaction):
        await handlers.programming_assistant_handler(interaction)

    # Define command to change default system text to scientific assistant
    @client.tree.command(name="scientific_assistant", description="Sets the default system text for the AI to be a scientific assistant.")
    async def scientific_assistant(interaction: discord.Interaction):
        await handlers.scientific_assistant_handler(interaction)

    # Define command to change default system text to ELI5 assistant
    @client.tree.command(name="eli5_assistant", description="Sets the default system text for the AI to be an ELI5 assistant.")
    async def eli5_assistant(interaction: discord.Interaction):
        await handlers.eli5_assistant_handler(interaction)

    # Define command to change default system text to general assistant
    @client.tree.command(name="general_assistant", description="Sets the default system text for the AI to be a general assistant.")
    async def general_assistant(interaction: discord.Interaction):
        await handlers.general_assistant_handler(interaction)
    # Reset chat history
    @client.tree.command(name="reset_chat", description="Reset the current chat and chat history.")
    async def reset_chat(interaction: discord.Interaction):
        await handlers.reset_chat_handler(interaction)
    
    # Toggle chat history on or off
    @client.tree.command(name="toggle_chat_history", description="Toggles chat history on or off.")
    async def toggle_chat_history(interaction: discord.Interaction):
        await handlers.toggle_chat_history_handler(interaction)
    
    @client.tree.command(name='help', description='List of available commands and their descriptions.')
    async def help_command(interaction: discord.Interaction):
        await handlers.help_command_handler(interaction)

    # Run Discord bot with token
    if not config.discord_token:
        config.logger.error("Error: discord_token environment variable not set.")
        return
    
    client.run(config.discord_token)
