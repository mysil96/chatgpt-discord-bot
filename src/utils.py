import os
import openai
import tiktoken
from src import log
from src import config

openai.api_key = os.getenv('openai_api_key')
logger = log.logger

def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(config.gpt_model)
    num_tokens = len(encoding.encode(string))
    return num_tokens

# Define asynchronous function to send a message to the user
async def send_message(message, system_text, input_text):
  
  # Send a message indicating that the GPT model is processing the request
  model_name = "GPT-3.5" if config.gpt_model == "gpt-3.5-turbo" else "GPT-4"
  sent_message = await message.channel.send(model_name + " is thinking...")
  
  try:
    # Get the ID of the message author
    author = message.author
    
    # Use OpenAI to generate a response to the user's message
    response = openai.ChatCompletion.create(model=config.gpt_model,
                                            messages=config.conversation_history,
                                            temperature=0.6,
                                            max_tokens=2048,
                                            n=1,
                                            stop=None)
    
    # Parse the response from OpenAI and format it for the user
    parsed_response = response["choices"][0]["message"]["content"]

    # Please never do this if-else statement in real life, this is absolutely the most troll method I could think of.
    # Wiping the array instead of coming up with an actual solution is honestly stupid
    # "Don't fix what's not broke" - Sun Tzu, probably
    if config.toggle_conversation_history == True:
      config.conversation_history.append({"role": "assistant", "content": parsed_response})
    else:
      config.conversation_history = []

    # Add metadata indicating who the response is for
    response = '> ** Response to ' + str(
      author) + '**:' + '>\n\n' + parsed_response
    
    # Determine whether the response should be sent privately or in the channel
    if config.is_private:
      author = await message.author.create_dm()
    else:
      author = message.channel
    
    # If the response is too long to send in a single message...
    if len(parsed_response) > 1900:
      # ...and it contains code blocks...
      if "```" in parsed_response:
        # Split the response into parts based on the code blocks
        parts = parsed_response.split("```")
        # Send the first part of the response as a regular message
        await message.followup.send(parts[0])
        # Split the code block into lines and format each line to fit within Discord's message length limits
        code_block = parts[1].split("\n")
        formatted_code_block = ""
        for line in code_block:
          while len(line) > 1900:
            formatted_code_block += line[:1900] + "\n"
            line = line[1900:]
          formatted_code_block += line + "\n"
        # If the formatted code block is still too long to send in a single message...
        if (len(formatted_code_block) > 2000):
          # ...split it into chunks of acceptable length and send each chunk as a separate message
          code_block_chunks = [
            formatted_code_block[i:i + 1900]
            for i in range(0, len(formatted_code_block), 1900)
          ]
          for chunk in code_block_chunks:
            await author.send("```" + chunk + "```")
        # If the formatted code block is short enough to send as a single message...
        else:
          await author.send("```" + formatted_code_block + "```")
        # If there are additional parts of the response (i.e., after the code block)...
        if len(parts) >= 3:
          # ...send them as separate messages
          await author.send(parts[2])

    else:
      await author.send(parsed_response)

    # Log to console that response has been sent
    logger.info("Response sent to user.\nRESPONSE:  " + parsed_response + "\n")

  # Send an error message to the user if an exception is raised, then log the error
  except Exception as e:
    if "That model is currently overloaded with other requests" in str(e):
        await message.channel.send(
      "> **Error:** " + model_name + " is currently overloaded. Please try again later!")
    else:
      await message.channel.send(
      "> **Error:** Something went wrong. Please try again later!")
      
    logger.error(e)

  # Delete "GPT-4 is thinking..." message
  logger.debug("Deleting '" + model_name + " is thinking' message...")
  await sent_message.delete()