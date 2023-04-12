# ChatGPT Discord Bot

This is a basic Python Discord bot that provides an interface for interacting with OpenAI's GPT-3.5 and GPT-4 models to generate text based on user input. The bot listens for messages that mention its name, and then looks for specific commands within those messages. The commands tell the bot what to generate and how to generate it.

This bot currently does NOT support back-and-forth chatting- it only provides a one-time response. is is meant to be a basic script for other people to use as a simple starting point. 

## Preview

![image](https://user-images.githubusercontent.com/125412472/231365157-3da73bf9-96c2-46f3-9d97-fc44fc7ab017.png)

## Prerequisites

To use this bot, you will need an OpenAI API key and a Discord bot token. You can get an API key from OpenAI's [website](https://openai.com/api/) and a Discord bot token from the [Discord Developer Portal](https://discord.com/developers/applications). You will also need to have Python 3.8 or higher installed on your system.

## Installation

1. Clone this repository: `git clone https://github.com/applebaconsoda123/chatgpt-discord-bot`
2. Install the required packages: `pip install -r requirements.txt`
3. Set the following environment variables:

    - `discord_token`: Your Discord bot token
    - `openai_key`: Your OpenAI API key
4. Run the bot: `python main.py`

## Usage

To use the bot, simply mention its name in a Discord message and include a command. The bot supports the following commands:

- `@botname /system <text> /input <text>`: Generates text based on the provided system text and input text. The system text is used to provide context for the input text, and the bot generates text that follows the context provided by the system text. For example:

    ```
    @botname /system You are a highly capable AI assistant. /input You are the average Redditor. Provide an answer to the following question: "AITA for telling my wife the lock on my daughter's door does not get removed til my brother inlaw and his daughters are out of our house?"
    ```
    If no `/system` text is given, then the system message automatically defaults to the following: 
    ```
    "You're a highly capable assistant trained to help users with every possible task."
    ```

- `@botname /private`: Toggles private mode on or off. When in private mode, the bot will only respond to the user in a DM.

- `@botname /public`: Toggles public mode on or off. When in public mode, the bot responds to the user in whatever channel the user tagged the bot in.

- `@botname /set_model`: Sets the model to either GPT-3.5 or GPT-4.

- `@botname /get_model`: Gets the current model being used. By default, this is GPT-4.

## Todo

- Support back-and-forth chatting (very easy implementation, I am just lazy)
- Implement commands for user to choose preset system messages
- Clean up code (it is a complete mess)

## Contributing

Pull requests are welcome. This code is rudimentary; it can (and should) be interpreted more as a helpful beginner's teaching tool than a working product with fully developed features.

## License

MIT License.
