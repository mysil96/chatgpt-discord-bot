import os
import openai
from src import log
from src import config

openai.api_key = os.getenv('openai_api_key')
logger = log.logger

# Define asynchronous function to send a message to the user
async def send_message(message, system_text, input_text):
  
  # Send a message indicating that the GPT model is processing the request
  model_name = "GPT-3.5" if config.gptModel == "gpt-3.5-turbo" else "GPT-4"
  sent_message = await message.channel.send(model_name + " is thinking...")
  
  try:
    # Get the ID of the message author
    author = message.author
    
    # Use OpenAI to generate a response to the user's message
    response = openai.ChatCompletion.create(model=config.gptModel,
                                            messages=[{
                                              "role": "system",
                                              "content": system_text
                                            }, {
                                              "role": "user",
                                              "content": input_text
                                            }],
                                            temperature=0.6,
                                            max_tokens=2048,
                                            frequency_penalty=0.02,
                                            presence_penalty=0.01)
    
    # Parse the response from OpenAI and format it for the user
    parsedResponse = response["choices"][0]["message"]["content"]

    # Add metadata indicating who the response is for
    response = '> ** Response to ' + str(
      author) + '**:' + '>\n\n' + parsedResponse
    
    # Determine whether the response should be sent privately or in the channel
    if config.isPrivate:
      author = await message.author.create_dm()
    else:
      author = message.channel
    
    # If the response is too long to send in a single message...
    if len(parsedResponse) > 1900:
      # ...and it contains code blocks...
      if "```" in parsedResponse:
        # Split the response into parts based on the code blocks
        parts = parsedResponse.split("```")
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
      await author.send(parsedResponse)
    # Log to console that response has been sent
    logger.debug("Response sent to user.")

  # Send an error message to the user if an exception is raised, then log the error
  except Exception as e:
    await message.channel.send(
      "> **Error: Something went wrong. Please try again later!**")
    logger.error(e)

  # Delete "GPT-4 is thinking..." message
  logger.debug("Deleting message...")
  await sent_message.delete()