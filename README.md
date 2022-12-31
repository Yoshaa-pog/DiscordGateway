
Simple way to interact with your discord bot.


**Installation**
```cmd
pip install yoshaas-gateway
```


**Example Usage**
```python
from discord_gateway import Intents
from discord_gateway.commands import CommandsBot

bot = CommandsBot(command_prefix='!', intents=Intents.All)

@bot.event
async def on_ready():
    print(bot.user.tag, 'is up')

@bot.command()
async def ping(ctx):
    await ctx.reply('pong!')

bot.run('TOKEN HERE', bot=True, log_level=40)  # Run the bot
```