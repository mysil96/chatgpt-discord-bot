# ChatGPT Discord Bot

This is a basic Python Discord bot that provides an interface for interacting with OpenAI's GPT-3.5 and GPT-4 models to generate text based on user input. The bot listens for messages that mention its name, and then looks for specific commands within those messages. The commands tell the bot what to generate and how to generate it.

This bot currently supports chat history (toggleable), file upload (limited to plaintext UTF-8), and preset system messages (useable through commands).

## Preview

![image](https://user-images.githubusercontent.com/125412472/231365157-3da73bf9-96c2-46f3-9d97-fc44fc7ab017.png)

## Prerequisites

To use this bot, you will need an OpenAI API key and a Discord bot token. You can get an API key from OpenAI's [website](https://openai.com/api/) and a Discord bot token from the [Discord Developer Portal](https://discord.com/developers/applications). You will also need to have Python 3.8 or higher installed on your system.

## Installation

1. Clone this repository: `git clone https://github.com/applebaconsoda123/chatgpt-discord-bot`
2. Install the required packages: `pip install -r requirements.txt`
3. Set the following environment variables:

    - `discord_token`: Your Discord bot token
    - `openai_api_key`: Your OpenAI API key
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
    If files are uploaded, then the plaintext from the very first file will be incorporated as part of the input.
    
- `/help`:  List of available commands and their descriptions.

- `/private`: Toggles private mode on or off. When in private mode, the bot will only respond to the user in a DM.

- `/public`: Toggles public mode on or off. When in public mode, the bot responds to the user in whatever channel the user tagged the bot in.

- `/set_model`: Sets the model to either GPT-3.5 or GPT-4.

- `/get_model`: Gets the current model being used. By default, this is GPT-4.

- `/programming_assistant`: Sets the default system text for the AI to be a programming assistant.

- `/scientific_assistant`: Sets the default system text for the AI to be a scientific assistant.

- `/eli5_assistant`: Sets the default system text for the AI to be an "Explain Like I'm 5" (ELI5) assistant.

- `/general_assistant`: Sets the default system text for the AI to be a general assistant.

- `/reset_chat`: Resets the current chat and chat history.

- `/toggle_chat_history`: Toggles chat history on or off. When chat history is on, the bot will save and display previous messages from the chat. 

To use the bot, simply type one of the commands above in the chat with the bot. The bot will respond with the appropriate action or information. You can also tag the bot in a channel to have it respond publicly or DM the bot to have it respond privately.

## Todo

- Clean up code
- Support more input types (e.g. PDFs)
- Add more comments and revise poor existing comments

## Contributing

Pull requests are welcome. This code is rudimentary; it can (and should) be interpreted more as a helpful beginner's teaching tool than a working product with fully developed features.

## License

MIT License.
