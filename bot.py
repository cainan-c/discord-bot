import discord
from discord.ext import commands
import toml

# Load configuration from config.toml
config = toml.load("config.toml")

# Replace 'YOUR_TOKEN_HERE' with your bot token
TOKEN = config["bot"]["token"]

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    guild_id = config["server"]["guild_id"]
    guild = bot.get_guild(int(guild_id))
    channel = guild.get_channel(int(config["server"]["channel_id"]))
    command_channel = guild.get_channel(int(config["server"]["command_channel_id"]))
    log_channel = guild.get_channel(int(config["server"]["log_channel_id"]))
    role = guild.get_role(int(config["server"]["role_id"]))
    print(f"Bot is connected to server: {guild.name}")
    print(f"Monitoring channel: {channel.name}")
    print(f"Commands channel: {command_channel.name}")
    print(f"Log channel: {log_channel.name}")        
    print(f"Assigning role: {role.name}")
    # Setting `Watching ` status
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="over this Discord server."))

@bot.event
async def on_member_join(member):
    guild_id = config["server"]["guild_id"]
    guild = bot.get_guild(int(guild_id))
    channel = guild.get_channel(int(config["server"]["channel_id"]))
    role = guild.get_role(int(config["server"]["role_id"]))
    welcome_message = f"Hello, {member.mention}. Welcome to {member.guild.name}!\nIntroduce yourself in {channel.mention} to get the {role.name} role and access to the rest of the server."
    await member.send(welcome_message)

# Function to check if a user ID is blacklisted
def is_user_blacklisted(user_id):
    with open(config["bot"]["blacklist_file_path"], 'r') as file:
        blacklisted_users = file.readlines()
        blacklisted_users = [x.strip() for x in blacklisted_users]
        return user_id in blacklisted_users

# Remove the default help command
bot.remove_command('help')

@bot.command()
async def help(ctx):
    if ctx.channel.id == int(config["server"]["command_channel_id"]):
        channel = bot.get_channel(int(config["server"]["channel_id"]))
        command_channel = bot.get_channel(int(config["server"]["command_channel_id"]))
        log_channel = bot.get_channel(int(config["server"]["log_channel_id"]))
        await ctx.send(f'Hello! I am <@1223361485904809994>. My Job is to help automate server joining.\nWhenever a new user sends a message in {channel.mention}, I will automatically assign them a role!\n\nThe following commands can be used:\n`!blacklist user_id <reason>` - This will add a user to our blacklist.\n`!unblacklist user_id <reason>` - this will remove a user from our blacklist.\n\nCommands will only be read from {command_channel.mention}\nAll logs will be sent to {log_channel.mention}')
    else:
        print(f"Cannot use command outside of designated channel.")

@bot.command()
async def blacklist(ctx, user_id, *, reason="No reason provided"):
    if ctx.channel.id == int(config["server"]["command_channel_id"]):
        if not is_user_blacklisted(user_id):
            with open(config["bot"]["blacklist_file_path"], 'a') as file:
                file.write(user_id + '\n')
            log_channel = bot.get_channel(int(config["server"]["log_channel_id"]))
            await log_channel.send(f"<@{user_id}> has been added to the blacklist. Reason: {reason}")
            await ctx.send(f"User <@{user_id}> has been added to the blacklist.")
        else:
            await ctx.send(f"User <@{user_id}> is already blacklisted.")

@bot.command()
async def unblacklist(ctx, user_id, *, reason="No reason provided"):
    if ctx.channel.id == int(config["server"]["command_channel_id"]):
        if is_user_blacklisted(user_id):
            with open(config["bot"]["blacklist_file_path"], 'r') as file:
                lines = file.readlines()
            with open(config["bot"]["blacklist_file_path"], 'w') as file:
                for line in lines:
                    if line.strip().split(" - ")[0] != user_id:
                        file.write(line)
            log_channel = bot.get_channel(int(config["server"]["log_channel_id"]))
            await log_channel.send(f"<@{user_id}> has been removed from the blacklist. Reason: {reason}")
            await ctx.send(f"User <@{user_id}> has been removed from the blacklist")
        else:
            await ctx.send(f"User <@{user_id}> is not blacklisted.")

@bot.event
async def on_message(message):
    if len(message.content) < 15:
        await message.author.send("Introduction too short. Please try again.")
        return
    
    await bot.process_commands(message)
    # Check if the message is in the specified channel
    if message.channel.id == int(config["server"]["channel_id"]):
        guild_id = config["server"]["guild_id"]
        guild = bot.get_guild(int(guild_id))
        role = guild.get_role(int(config["server"]["role_id"]))
        user_id = str(message.author.id)
        if not is_user_blacklisted(user_id):
            try:
                await message.author.add_roles(role)
                print(f"{message.author.mention} has been assigned the role {role.name}.")
                log_channel = guild.get_channel(int(config["server"]["log_channel_id"]))
                await log_channel.send(f"User {message.author.mention} has been assigned the role {role.name}.")
            except discord.Forbidden:
                print("Bot doesn't have permission to assign roles.")
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            print(f"{message.author.mention} is blacklisted and cannot be assigned the role.")
            log_channel = guild.get_channel(int(config["server"]["log_channel_id"]))
            await log_channel.send(f"Blacklisted user {message.author.mention} tried to join.")

bot.run(TOKEN)
