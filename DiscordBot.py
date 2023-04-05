import discord
from discord.ext import commands
import openai

openai.api_key = "sk-..."


# Define the intents needed for the bot
intents = discord.Intents.default()
intents.messages = True  # Enable the message-related events
intents.message_content = True  # Enable the message content intent

# Create a bot instance with the specified intents
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def logic(ctx, user: discord.Member, num_messages: int):
    # Ensure the number of messages requested is positive and not too large
    if num_messages <= 0 or num_messages > 10:
        await ctx.send('The number of messages must be between 1 and 10.')
        return

    # Get the message history in the current channel using an asynchronous list comprehension
    message_history = [message async for message in ctx.channel.history(limit=1000)]

    # Filter messages from the mentioned user
    user_messages = ([message for message in message_history if message.author == user])

    # Get the last 'num_messages' messages from the mentioned user
    last_user_messages = user_messages[:num_messages]

    # Output the messages
    if last_user_messages:
        responses = '\n'.join([f'{msg.author}: {msg.content}' for msg in last_user_messages])
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0,
            messages=[
                {"role": "system", "content": "You analyze statements for logical fallacies"},
                {"role": "user", "content": f"@{ctx.author.name} evaluate next message for logical fallacies; Output a list of each occurring fallacies and quote the message: {responses}"},
                {"role": "assistant", "content": str(responses)},
            ]
        )
        resp = response['choices'][0]['message']['content']
        await ctx.send(f"{ctx.author.mention} {resp}")
    else:
        await ctx.send(f'No messages found from {user.name}. @{ctx.author.name}')

# Run the bot with your token
bot.run('TOKEN')
