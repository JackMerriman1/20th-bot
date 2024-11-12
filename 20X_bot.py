import discord
from discord.ext import commands
import json
from Functions import *
import asyncio
import threading
import time
from secret import BOT_KEY, SERVER_ID_20TH
import os

CALENDAR_CHANNEL_ID = 843347366345441280 ###
ATTENDING_REACTION = '✅'
NOT_ATTENDING_REACTION = '❌'
MAYBE_ATTENDING_REACTION = '❓'
RECRUIT_WELCOME_CHANNEL = 680803082644226172
WELCOME_CHANNEL_ID = 851874728394489926

intents = discord.Intents.default()
intents.reactions = True
intents.members = True
intents.messages = True
intents.guilds = True  # Add this line to enable the messages intent

client = commands.Bot(command_prefix='!', intents=intents)
# guild = client.get_guild(SERVER_ID_20TH)

# if guild:
#     members = guild.members  # Access cached members directly
#     roles = guild.roles      # Access cached roles directly
#     print(f"Guild '{guild.name}' has {len(members)} members and {len(roles)} roles.")
# else:
#     print(f"Bot is not connected to the server with ID {SERVER_ID_20TH}")


#tree = app_commands.CommandTree(client)

is_server = os.path.exists('20X_BOT/service_record_data.json')

if is_server:
    BASE_PATH = '20X_BOT/'  # Path for the server
else:
    BASE_PATH = ''  # Path for local machine

SERVICE_RECORD_FILE = os.path.join(BASE_PATH, 'service_record_data.json')
SERVICE_RECORD = load_data(SERVICE_RECORD_FILE)

BANNED_FILE_PATH = os.path.join(BASE_PATH, 'banned_list.json')

ALL_EVENTS_FILE = os.path.join(BASE_PATH, 'all_events.json')
ALL_EVENTS = load_data(ALL_EVENTS_FILE)

ORBAT_IMAGE_PATH = os.path.join(BASE_PATH, '20th_ORBAT.jpg')
ORBAT_IMAGE_PATH = '20th_ORBAT.jpg'

            ###BACKUP TO EMAIL EVERY 3 DAYS###

email_thread = threading.Thread(target=run_email_scheduler)
email_thread.start()


@client.event
async def on_ready():
    await client.tree.sync()
    print(f"Logged in as {client.user}")
    await fetch_guild_and_members()
    asyncio.create_task(event_auto_reminder())

async def fetch_guild_and_members():
    global GUILD, GUILD_MEMBERS, GUILD_ROLES
    GUILD = client.get_guild(SERVER_ID_20TH)
    if GUILD:
        GUILD_MEMBERS = GUILD.members
        GUILD_ROLES = GUILD.roles
    else:
        print(f"Bot is not connected to the server with ID {SERVER_ID_20TH}")  # Add this line
    print("time")

                
                ### Event RSVP Features ###

@client.tree.command(name="create_event", description="Create an Event")
@commands.cooldown(1, 5, commands.BucketType.default)
async def create_event(interaction: discord.Interaction, event_name: str, event_description: str, event_date: str, event_time: str):
    try:
        # Defer the interaction to give more time to process
        await interaction.response.defer()

        allowed_role_list = ["MDT", "Junior NCO", "Senior NCO", "SAT"]
        user_role_list = [role.name for role in interaction.user.roles]

        if any(role in allowed_role_list for role in user_role_list):
            # Create the Embed and send it into the channel
            event_discord_timestamp, relative_timestamp, unix_timestamp = generate_unix_timestamp_and_relative(event_date, event_time)

            embed = create_embed(f"New Event Created: {event_name}", f"{event_description}", f"\nServer start: <t:{unix_timestamp}>\nBattle-Prep begins: <t:{unix_timestamp + 900}>\nStep Off: <t:{unix_timestamp + 1800}>\n\n\nEvent Begins {relative_timestamp}")
            
            await interaction.followup.send(embed=embed)
            event_message = await interaction.original_response()

            await event_message.add_reaction(ATTENDING_REACTION)
            await event_message.add_reaction(NOT_ATTENDING_REACTION)
            await event_message.add_reaction(MAYBE_ATTENDING_REACTION)

            channel_id = interaction.channel_id
            await interaction.followup.send("<@&680795785423880248> <@&680795766125887596> <@&680795741417242804> <@&680795653345116183> <@&680795516228993025> Please RSVP above")
            # Initialise entry into ALL_EVENTS dict for this event with message id as the key
            event_message_id = event_message.id
            ALL_EVENTS[event_name] = {}

            # Add keys, values into dict
            event_discord_timestamp, relative_timestamp, unix_timestamp = generate_unix_timestamp_and_relative(event_date, event_time)
            ALL_EVENTS[event_name]["event message id"] = event_message_id
            ALL_EVENTS[event_name]["event channel id"] = channel_id
            ALL_EVENTS[event_name]["event desc"] = event_description
            ALL_EVENTS[event_name]["event time"] = event_time
            ALL_EVENTS[event_name]["event date"] = event_date
            ALL_EVENTS[event_name]["discord timestamp"] = event_discord_timestamp
            ALL_EVENTS[event_name]["relative timestamp"] = relative_timestamp
            ALL_EVENTS[event_name]["unix timestamp"] = unix_timestamp

            with open(ALL_EVENTS_FILE, 'w') as f:
                json.dump(ALL_EVENTS, f)
        else:
            await interaction.response.send_message("You dont have the required roles to create events!")

    except Exception as e:
        print(e)
        try:
            await interaction.followup.send(f"**ERROR**: *{e}* Contact @boniface for support")
        except Exception as followup_exception:
            print(followup_exception)

# Handle user reactions
@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    for event in ALL_EVENTS:
        if payload.message_id == ALL_EVENTS[event]["event message id"]:
            channel = client.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            member = payload.member

            if str(payload.emoji) == ATTENDING_REACTION:
                await message.remove_reaction(NOT_ATTENDING_REACTION, member)
                await message.remove_reaction(MAYBE_ATTENDING_REACTION, member)
            elif str(payload.emoji) == NOT_ATTENDING_REACTION:
                await message.remove_reaction(ATTENDING_REACTION, member)
                await message.remove_reaction(MAYBE_ATTENDING_REACTION, member)
            elif str(payload.emoji) == MAYBE_ATTENDING_REACTION:
                await message.remove_reaction(ATTENDING_REACTION, member)
                await message.remove_reaction(NOT_ATTENDING_REACTION, member)


# Generate RSVP list function


@client.tree.command(name="generate_event_rsvp_list", description="generate_event_rsvp_list")
@commands.cooldown(1, 5, commands.BucketType.default)
async def generate_event_rsvp_list(interaction: discord.Interaction, event_name: str):
    role_sections = {
        "1 Platoon": ["1 Section", "2 Section", "3 Section", "HQ Section"],
        "2 Platoon": ["1 Section", "2 Section", "3 Section", "HQ Section"],
        "3 Platoon": ["1 Section", "2 Section", "3 Section", "HQ Section"]
    }
    
    try:
        message_id = int(ALL_EVENTS[event_name]["event message id"])
        channel_id = int(ALL_EVENTS[event_name]["event channel id"])

        channel = GUILD.get_channel(channel_id)
        message = await channel.fetch_message(message_id)

        # Updated allowed_role_list to include "Phase 2 Recruit"
        allowed_role_list = ["Enlisted", "Junior NCO", "Senior NCO", "Officer", "Phase 2 Trainee Rifleman"]
        
        attending_users = set()
        not_attending_users = set()
        maybe_attending_users = set()
        all_users = set()
        trainee_riflemen = set()  # Set to store Phase 2 Recruits who are attending

        for user in GUILD_MEMBERS:
            if any(role.name in allowed_role_list for role in user.roles):
                all_users.add(user)

        # Iterate over reactions
        for reaction in message.reactions:
            if reaction.emoji == ATTENDING_REACTION:
                attending_users = set([user async for user in reaction.users() if user in all_users])
            elif reaction.emoji == NOT_ATTENDING_REACTION:
                not_attending_users = set([user async for user in reaction.users() if user in all_users])
            elif reaction.emoji == MAYBE_ATTENDING_REACTION:
                maybe_attending_users = set([user async for user in reaction.users() if user in all_users])
        
        not_reacted_users = all_users - (attending_users | not_attending_users | maybe_attending_users)

        # Create an embed
        embed = discord.Embed(title=f"RSVP List for {event_name}", color=discord.Color.blue())

        # Categorize attending members based on their roles
        categorized_members = {platoon: {section: [] for section in sections} for platoon, sections in role_sections.items()}

        for user in attending_users:
            if any(role.name == "Phase 2 Trainee Rifleman" for role in user.roles):
                # Add user to phase_2_recruits if they have the "Phase 2 Recruit" role
                trainee_riflemen.add(user.nick if user.nick else user.name)
            else:
                for role in user.roles:
                    for platoon, sections in role_sections.items():
                        if role.name == platoon:
                            for section in sections:
                                if section in [r.name for r in user.roles]:
                                    categorized_members[platoon][section].append(user.nick if user.nick else user.name)

        # Add fields to the embed for each role (attending members)
        for platoon, sections in categorized_members.items():
            for section, members in sections.items():
                if members:
                    embed.add_field(name=f"{platoon} - {section}", value="\n".join(members), inline=False)

        # Add field for Phase 2 Recruits
        if trainee_riflemen:
            embed.add_field(name="Trainee Riflemen", value="\n".join(trainee_riflemen), inline=False)
        
        maybe_attending_nicks = [user.nick if user.nick else user.name for user in maybe_attending_users]
        if maybe_attending_nicks:
            embed.add_field(name="Maybe", value="\n".join(maybe_attending_nicks), inline=False)

        # Add field for not attending members
        not_attending_nicks = [user.nick if user.nick else user.name for user in not_attending_users]
        if not_attending_nicks:
            embed.add_field(name="Not Attending", value="\n".join(not_attending_nicks), inline=False)

        # Add field for members who haven't reacted
        not_reacted_nicks = [user.nick if user.nick else user.name for user in not_reacted_users]
        if not_reacted_nicks:
            embed.add_field(name="No Response", value="\n".join(not_reacted_nicks), inline=False)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}")
                ### LIST EVENTS ###

@client.tree.command(name="list_events", 
              description="lists all upcoming events")
@commands.cooldown(1, 5, commands.BucketType.default)
async def list_events(interaction: discord.Interaction):
    try:
        all_events = []

        current_timestamp = int(time.time())

        for event_name in ALL_EVENTS:
            if int(ALL_EVENTS[event_name]["unix timestamp"]) > current_timestamp:
                datetime = ALL_EVENTS[event_name]["discord timestamp"]
                relative_datetime = ALL_EVENTS[event_name]["relative timestamp"]
                channel_id = ALL_EVENTS[event_name]["event channel id"]
                message_id = ALL_EVENTS[event_name]["event message id"]

                full_string = f"{event_name}: {datetime} starts {relative_datetime}: RSVP here - https://discord.com/channels/{SERVER_ID_20TH}/{channel_id}/{message_id}"
                all_events.append(full_string)

        embed = create_embed("All upcoming events", "List of all events")
        embed.add_field(name="events", value="\n".join(all_events))

        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(e)

async def event_auto_reminder():
    print("Starting event_auto_reminder task.")
    await client.wait_until_ready()

    while True:
        try:
            current_timestamp = int(time.time())
            for event_name in ALL_EVENTS:
                event_timestamp = int(ALL_EVENTS[event_name]["unix timestamp"])
                event_relative_timestamp = ALL_EVENTS[event_name]["relative timestamp"]
                channel_id = ALL_EVENTS[event_name]["event channel id"]
                message_id = ALL_EVENTS[event_name]["event message id"]
                channel = client.get_channel(channel_id)

                if event_timestamp - 21600 < current_timestamp < event_timestamp - 18000:
                    await channel.send(f"@everyone REMINDER: Event {event_name} tonight starting {event_relative_timestamp}\n- Make sure your modpack is up to date\n- if you haven't already RSVP here: https://discord.com/channels/{SERVER_ID_20TH}/{channel_id}/{message_id}\nThanks :).")

                else:
                    continue

            await asyncio.sleep(60*60)
            
        except Exception as e:
            print(f"Error in event_auto_reminder: {e}")
            await asyncio.sleep(60*60)

                ### Recruit handling Features ###

@client.event
async def on_member_join(member):
    time.sleep(30)
    try:
        channel = client.get_channel(WELCOME_CHANNEL_ID)
        await channel.send(f"Welcome to the 20th ABCT MilSim discord {member.mention}.\nIf you are interested in joining as a member then please go to <#1292493814858252299> for information about the unit and how to join.\nIf you prefer to speak with a recruiter then just create a thread there, tag <@&680795063684694063> and someone will respond as soon as they are available.\nFor representatives of other clans/units, please speak with <@140372016476848128> for any further assistance.\n\n Thanks!")
    except Exception as e:
        await channel.send(f"ERROR WITH NEW USER JOIN HANDLING FEATURE: {e}")


@client.tree.command(name="add_recruit", 
              description="Assigns a user with platoon and section roles\nif reserves = yes leave platoon and section empty")
@commands.cooldown(1, 5, commands.BucketType.default)
async def add_recruit(interaction: discord.Interaction, user: str, platoon: str, section: str = None, reserves: str = "no"):
    
    try:
        welcome_channel = GUILD.get_channel(RECRUIT_WELCOME_CHANNEL)
        platoon_str = ""
        section_str = ""
        response_message = ""
        
        allowed_role_list = ["RRT", "SAT"]
        user_role_list = [role.name for role in interaction.user.roles]
        
        allowed_channels = {"G1 Personnel Admin Channel": 701267972475584525, "Bot Test": 1246848431092138075}
        if interaction.channel.id in allowed_channels.values():

            if any(role in allowed_role_list for role in user_role_list):
                for member in GUILD_MEMBERS:
                    if member.name == user:
                        if reserves.lower() == "no":
                            platoon_str = f"{platoon} Platoon"
                            section_str = f"{section} Section"
                            platoon_role = discord.utils.get(GUILD_ROLES, name=platoon_str)
                            section_role = discord.utils.get(GUILD_ROLES, name=section_str)
                            recruit_role = discord.utils.get(GUILD_ROLES, name="Phase 1 Recruit")
                            if platoon_role and section_role:
                                await member.add_roles(platoon_role, section_role, recruit_role)
                                response_message = f"Added roles {platoon_role.name} and {section_role.name} to {user}."
                                await welcome_channel.send(f"@everyone please welcome our newest recruit <@{member.id}>, they have been placed into {platoon_str}, {section_str}")
                            else:
                                response_message = "One or more roles not found."
                        elif reserves.lower() == "yes":
                            platoon_str = f"{platoon} Platoon"
                            platoon_role = discord.utils.get(GUILD_ROLES, name=platoon_str)
                            role_str = "Reserves"
                            role = discord.utils.get(GUILD_ROLES, name=role_str)
                            if role:
                                await member.add_roles(role, platoon_role)
                                response_message = f"Added role {role.name} to {user}."
                                await welcome_channel.send(f"@everyone please welcome our newest recruit <@{member.id}> to the unit, they have been placed into our reserves")
                            else:
                                response_message = "Role 'Reserves' not found."
                        else:
                            response_message = f"User {user} not found, check your spelling and try again, please use their discord name and not their server nickname"
                        break

                await interaction.response.send_message(response_message)
                
            else:
                await interaction.response.send_message("You dont have the required roles to add recruits!")
        else:
            await interaction.response.send_message("This command is only available in G1 Personnel admin channel!")
    except Exception as e:
        await interaction.response.send_message(f"ERROR: {e}")


### NEEDS TESTING ###
@client.tree.command(name="phase_1_complete", 
                     description="Assigns user with correct roles, adds service record and send congrats message")
@commands.cooldown(1, 5, commands.BucketType.default)
async def add_recruit(interaction: discord.Interaction, user: str, platoon: str, service_number: str, zap_number: str, application_date: str, verified_forces: str= None):

    try:
        allowed_role_list = ["RTT", "SAT", "Officer"]
        user_role_list = [role.name for role in interaction.user.roles]
        welcome_channel = GUILD.get_channel(RECRUIT_WELCOME_CHANNEL)


        member = discord.utils.get(GUILD_MEMBERS, name=user)
        member_id = member.id

        if any(role in allowed_role_list for role in user_role_list):

            if member_id in SERVICE_RECORD:
                await interaction.response.send_message(f"Service record for {user} already exists")
            else:
                SERVICE_RECORD[member_id] = {}
                SERVICE_RECORD[member_id]["name"] = user
                SERVICE_RECORD[member_id]["rank"] = "Trainee Rifleman"
                SERVICE_RECORD[member_id]["service number"] = service_number
                SERVICE_RECORD[member_id]["zap number"] = zap_number
                SERVICE_RECORD[member_id]["application date"] = application_date
                SERVICE_RECORD[member_id]["verified forces"] = verified_forces

                SERVICE_RECORD[member_id]["qualifications"] = []
                SERVICE_RECORD[member_id]["operations attended"] = []
                SERVICE_RECORD[member_id]["staff roles"] = []
                SERVICE_RECORD[member_id]["enlistment history"] = []
                SERVICE_RECORD[member_id]["assignment history"] = []

                roles = member.roles[1:]  # Exclude @everyone role
                await member.remove_roles(*roles)

                platoon_str = f"{platoon} Platoon"
                platoon_role = discord.utils.get(GUILD_ROLES, name=platoon_str)
                rank_role = discord.utils.get(GUILD_ROLES, name="Phase 2 Trainee Rifleman")
                await member.add_roles(platoon_role, rank_role)
                await interaction.response.send_message(f"Service record for {user} created! {platoon_str} and {rank_role} roles assigned!")
                await welcome_channel.send(f"Congratulations to <@{member.id}> for completing the Phase 1 section of their CIC, Well done!")

                with open(SERVICE_RECORD_FILE, 'w') as f:
                    json.dump(SERVICE_RECORD, f)
        else:
            await interaction.response.send_message(f"ERROR: You do not have the required roles")
    except Exception as e:
        await interaction.response.send_message(f"ERROR: {e}")


                ### Goblin Features ###


@client.tree.command(name="goblin", 
              description="Special command for Rfn Goblin")
@commands.cooldown(1, 5, commands.BucketType.default)
async def view_events(interaction=discord.Interaction):
    
    try:
        
        allowed_role_list = ["Officer", "Junior NCO", "Senior NCO", "SAT"]
        user_role_list = [role.name for role in interaction.user.roles]
        
        if any(role in allowed_role_list for role in user_role_list):
            calendar_channel_id = 843347366345441280
            await interaction.response.send_message(f"Click it: <#{calendar_channel_id}>")

        else:
            await interaction.response.send_message("You dont have the required roles!")
    except Exception as e:
        print(e)
                ### Service Records Features ###

            
            ###SERVICE RECORD FEATURES###


@client.tree.command(name = "add_service_record",
              description = "add service record entry, qualifications and operations(optional)= list separated by commas")
@commands.cooldown(1, 5, commands.BucketType.default)
async def add_service_record(interaction:discord.Interaction, user: str, rank: str, 
                             service_number: str, zap_number: str, application_date: str, 
                             verified_forces: str= None, qualifications: str= None, operations: str= None, 
                             staff_roles: str= None, enlistment_history:str= None, assignment_history:str= None):
    try:
        
        allowed_role_list = ["PAT", "SAT"]
        user_role_list = [role.name for role in interaction.user.roles]
        
        allowed_channels = {"G1 Personnel Admin Channel": 701267972475584525, 
                            "Bot Test": 1246848431092138075, 
                            "Platoon Channel": 680803082644226172}
        
        if interaction.channel.id in allowed_channels.values():

            if any(role in allowed_role_list for role in user_role_list):

                member = discord.utils.get(GUILD_MEMBERS, name=user)
                member_id = member.id


                if member_id in SERVICE_RECORD:
                    await interaction.response.send_message(f"Service record for {user} already exists")

                else:
                    # add service record
                    SERVICE_RECORD[member_id] = {}
                    SERVICE_RECORD[member_id]["name"] = user
                    SERVICE_RECORD[member_id]["rank"] = rank
                    SERVICE_RECORD[member_id]["service number"] = service_number
                    SERVICE_RECORD[member_id]["zap number"] = zap_number
                    SERVICE_RECORD[member_id]["application date"] = application_date
                    SERVICE_RECORD[member_id]["verified forces"] = verified_forces

                    SERVICE_RECORD[member_id]["attendance"] = []

                    if verified_forces == None:
                        SERVICE_RECORD[member_id]["verified forces"] = "none"
                    else:
                        SERVICE_RECORD[member_id]["verified forces"] = verified_forces

                    if qualifications == None:
                        SERVICE_RECORD[member_id]["qualifications"] = []
                    else:
                        qualifications = qualifications.split(",")
                        SERVICE_RECORD[member_id]["qualifications"] = qualifications

                    if operations == None:
                        SERVICE_RECORD[member_id]["operations attended"] = []
                    else:
                        operations = operations.split(",")
                        SERVICE_RECORD[member_id]["operations attended"] = operations

                    if staff_roles == None:
                        SERVICE_RECORD[member_id]["staff roles"] = []
                    else:
                        staff_roles = staff_roles.split(",")
                        SERVICE_RECORD[member_id]["staff roles"] = staff_roles

                    if enlistment_history == None:
                        SERVICE_RECORD[member_id]["enlistment history"] = []
                    else:
                        enlistment_history = enlistment_history.split(",")
                        SERVICE_RECORD[member_id]["enlistment history"] = enlistment_history

                    if assignment_history == None:
                        SERVICE_RECORD[member_id]["assignment history"] = []
                    else:
                        assignment_history = assignment_history.split(",")
                        SERVICE_RECORD[member_id]["assignment history"] = assignment_history

                    



                    await interaction.response.send_message(f"Service record added for {user}")
                with open(SERVICE_RECORD_FILE, 'w') as f:
                    json.dump(SERVICE_RECORD, f)   
            else:
                await interaction.response.send_message("You dont have the required roles!")
        else:
            await interaction.response.send_message("This command is only available in G1 Personnel admin channel!")
    except Exception as e:
                print(e)

@client.tree.command(name="get_service_record", description="Retrieve a user's service record")
@commands.cooldown(1, 5, commands.BucketType.default)
async def get_service_record(interaction: discord.Interaction, user: str):
    
    try:
        allowed_role_list = ["1 Platoon", "Reserves", "SAT"]
        user_role_list = [role.name for role in interaction.user.roles]
        
        allowed_channels = {"1 Platoon General": 680803082644226172, 
                            "7 Platoon General": 822221048320753695, 
                            "G1 Personnel Admin Channel": 701267972475584525, 
                            "Bot Test": 1246848431092138075}
        
        if interaction.channel.id in allowed_channels.values():
            if any(role in allowed_role_list for role in user_role_list):
                SERVICE_RECORD = load_data(SERVICE_RECORD_FILE)
                # Get member by name
                member = discord.utils.get(GUILD_MEMBERS, name=user)
            
                if member is None:
                    await interaction.response.send_message(f"User {user} not found.", ephemeral=True)
                    return

                member_id = str(member.id)
                records = [id for id in SERVICE_RECORD]

                if member_id in records:
                    record = SERVICE_RECORD[member_id]
                    name = record["name"]
                    rank = record["rank"]
                    service_number = record["service number"]
                    zap_number = record["zap number"]
                    application_date = record["application date"]
                    verified_forces = record["verified forces"]

                    qualifications = record["qualifications"]
                    operations = record["operations attended"]
                    staff_roles = record["staff roles"]
                    enlistment_history = record["enlistment history"]
                    assignment_history = record["assignment history"]

                    embed = create_embed(f"{name}", description="Service Record")
                    embed.add_field(name="Rank", value=rank, inline=False)
                    embed.add_field(name="Service Number", value=service_number)
                    embed.add_field(name="Zap Number", value=zap_number)
                    embed.add_field(name="Application date", value=application_date)
                    embed.add_field(name="Verified forces", value=verified_forces)

                    
                    embed.add_field(name="Enlistment History", value="\n".join(enlistment_history))
                    embed.add_field(name="Assignment History", value="\n".join(assignment_history))
                    embed.add_field(name="Operations Attended", value="\n".join(operations))
                    embed.add_field(name="Qualifications", value="\n".join(qualifications), inline=False)
                    embed.add_field(name="Staff Roles", value="\n".join(staff_roles))
                    

                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message("No Service Record Found", ephemeral=True)
                
            else:
                await interaction.response.send_message("You dont have the required roles!")
        else:
            await interaction.response.send_message("This command is only available in Platoon general channels!")
    except Exception as e:
                print(f"An unexpected error occurred: {e}")

@client.tree.command(name="update_service_record", description="update a user's service record")
@commands.cooldown(1, 5, commands.BucketType.default)
async def update_service_record(interaction:discord.Interaction, user: str, rank: str= None, 
                                service_number: str=None, zap_number: str= None, application_date: str= None, 
                                verified_forces: str= None, qualifications: str= None, operations: str= None, 
                                staff_roles: str= None, enlistment_history: str= None, assignment_history: str= None):
    
    try:
        allowed_role_list = ["PAT", "SAT"]
        user_role_list = [role.name for role in interaction.user.roles]
        
        allowed_channels = {"G1 Personnel Admin Channel": 1292418540544069652, "Bot Test": 1246848431092138075}
        
        if interaction.channel.id in allowed_channels.values():

            if any(role in allowed_role_list for role in user_role_list):
                SERVICE_RECORD = load_data(SERVICE_RECORD_FILE)

                member = discord.utils.get(GUILD_MEMBERS, name=user)
                if member is None:
                    await interaction.response.send_message("User not found in this server.", ephemeral=True)
                    return
                member_id = str(member.id)

                records = [id for id in SERVICE_RECORD]

                if member_id in records:
                    record = SERVICE_RECORD[member_id]

                    record["name"] = user

                    if rank != None:
                        record["rank"] = rank

                    if service_number != None:
                        record["service number"] = service_number

                    if zap_number != None:
                        record["zap number"] = zap_number

                    if application_date != None:
                        record["application date"] = application_date

                    if verified_forces != None:
                        record["verified forces"] = verified_forces

                    if qualifications != None:
                        qualifications = qualifications.split(",")
                        for qualification in qualifications:
                            record["qualifications"].append(qualification)

                    if operations != None:
                        operations = operations.split(",")
                        for operation in operations:
                            record["operations attended"].append(operation)

                    if staff_roles != None:
                        staff_roles = staff_roles.split(",")
                        for staff_role in staff_roles:
                            record["staff roles"].append(staff_role)

                    if enlistment_history != None:
                        enlistment_history = enlistment_history.split(",")
                        for event in enlistment_history:
                            record["enlistment history"].append(event)

                    if assignment_history != None:
                        assignment_history = assignment_history.split(",")
                        for assignment in assignment_history:
                            record["assignment history"].append(assignment)

                    await interaction.response.send_message(f"Service Record for {user} updated", ephemeral=True)
                else:
                    await interaction.response.send_message("No Service Record Found", ephemeral=True)

                with open(SERVICE_RECORD_FILE, 'w') as f:
                    json.dump(SERVICE_RECORD, f)
                
            else:
                await interaction.response.send_message("You dont have the required roles!")
        else:
            await interaction.response.send_message("This command is only available in G1 Personnel admin channel!")
    except Exception as e:
                print(f"An unexpected error occurred: {e}")

@client.tree.command(name="add_operation_attendance", description="update all users service record who attended the op")
@commands.cooldown(1, 5, commands.BucketType.default)
async def add_operation_attendance(interaction:discord.Interaction, op_name: str, users: str):
    
    try:
        allowed_role_list = ["PAT", "SAT"]
        user_role_list = [role.name for role in interaction.user.roles]
        
        if any(role in allowed_role_list for role in user_role_list):
            SERVICE_RECORD = load_data(SERVICE_RECORD_FILE)

            users = users.split(",")
            users_in_record = []
            user_not_found = []

            for member_id in SERVICE_RECORD:
                users_in_record.append(SERVICE_RECORD[member_id]["name"])

            for user in users:
                if user in users_in_record:
                    for member_id in SERVICE_RECORD:
                        if SERVICE_RECORD[member_id]["name"] == user:
                            SERVICE_RECORD[member_id]["operations attended"].append(op_name)
                else:
                    user_not_found.append(user)

            # Debug: Check the state of SERVICE_RECORD after updates
            print("Updated SERVICE_RECORD:", SERVICE_RECORD)
            if len(user_not_found) > 0:
                users_not_found_string = ",".join(user_not_found)
                await interaction.response.send_message(f"Service records updated, the following users could not be found {users_not_found_string}", ephemeral=True)
            else:
                await interaction.response.send_message("Service records updated", ephemeral=True)

            with open(SERVICE_RECORD_FILE, 'w') as f:
                json.dump(SERVICE_RECORD, f)
            
        else:
            await interaction.response.send_message("You dont have the required roles!")
    except Exception as e:
            print(f"An unexpected error occurred: {e}")

@client.tree.command(name="add_qualification_completed", description="update all users service record who attended the op")
@commands.cooldown(1, 5, commands.BucketType.default)
async def add_qualification_completed(interaction:discord.Interaction, qualification_name: str, users: str):
    
    
    try:
        allowed_role_list = ["PAT", "RTT Head Instructor","RTT Staff", "SAT"]
        user_role_list = [role.name for role in interaction.user.roles]
        
        if any(role in allowed_role_list for role in user_role_list):
            SERVICE_RECORD = load_data(SERVICE_RECORD_FILE)

            # Debug: Check initial state of SERVICE_RECORD
            print("Initial SERVICE_RECORD:", SERVICE_RECORD)

            users = users.split(",")
            users_in_record = []
            user_not_found = []

            for member_id in SERVICE_RECORD:
                users_in_record.append(SERVICE_RECORD[member_id]["name"])

            for user in users:
                if user in users_in_record:
                    for member_id in SERVICE_RECORD:
                        if SERVICE_RECORD[member_id]["name"] == user:
                            # Debug: Check which user is being updated
                            print(f"Updating {user}'s record with qualification: {qualification_name}")

                            SERVICE_RECORD[member_id]["qualifications"].append(qualification_name)
                            # Debug: Verify that the operation has been added
                            print(f"{user}'s updated qualifications: {SERVICE_RECORD[member_id]['operations attended']}")
                else:
                    user_not_found.append(user)

            # Debug: Check the state of SERVICE_RECORD after updates
            print("Updated SERVICE_RECORD:", SERVICE_RECORD)
            if len(user_not_found) > 0:
                users_not_found_string = ",".join(user_not_found)
                await interaction.response.send_message(f"Service records updated, the following users could not be found {users_not_found_string}", ephemeral=True)
            else:
                await interaction.response.send_message("Service records updated", ephemeral=True)

            with open(SERVICE_RECORD_FILE, 'w') as f:
                json.dump(SERVICE_RECORD, f)

        else:
            await interaction.response.send_message("You dont have the required roles!")
    except Exception as e:
            print(f"An unexpected error occurred: {e}")

            ### IMPORTANT CHANNELS ###

@client.tree.command(name="important_channels", description="Lists and links important channels")
@commands.cooldown(1, 5, commands.BucketType.default)
async def important_channels(interaction:discord.Interaction):
    try:
        important_channels = {"calendar": (843347366345441280, "Where all events and RSVP lists are posted"),
                              "teamspeak, server and mods": (1292117684279971922, "Where all Teamspeak, ArmA server and Mods info is found"),
                              "general docs and info": (1292117378100105246, "Where all documents and info for enlisted personnel can be found"),
                              "organisation": (1292123506846466131, "Unit Organisational info"),
                              "training and cadre info": (1292428757264629790, "Information about different trainings and cadres available"),
                              "1 platoon general": (680803082644226172, "General Channel for 1 Platoon"),
                              "role request": (1292426637454872666, "Forum to use if you want to request a specific role"),
                              "7 platoon general": (822221048320753695, "General Channel for 7 Platoon(Reserves)"),
                              "phase 1 and 2 training forum": (1292430453428719677, "Forum for everything regarding phase 1 and phase 2 training")}
        

        strings_list = []
        for name, info in important_channels.items():
            full_string = f"<#{info[0]}>: {info[1]}"
            strings_list.append(full_string)

        embed = create_embed(title="Important Channels", description="List of important channels and description")
        embed.add_field(name="Channels", value="\n".join(strings_list))

        await interaction.response.send_message(embed=embed)


    except Exception as e:
        print(e)

@client.tree.command(name="update_attendance", description="update attendance for all users")
@commands.cooldown(1, 5, commands.BucketType.default)
async def update_attendance(interaction: discord.Interaction, attendees: str):
    try:
        
        allowed_role_list = ["SAT"]
        user_role_list = [role.name for role in interaction.user.roles]

        if any(role in allowed_role_list for role in user_role_list):
            SERVICE_RECORD = load_data(SERVICE_RECORD_FILE)
            attended_users = attendees.split(",")

            for id, record in SERVICE_RECORD.items():
                if "attendance" not in record:
                    record["attendance"] = []
                
                if record["name"] in attended_users and record["attendance"]:
                    record["attendance"].append(1)  # Attended
                elif record["name"] in attended_users:
                    record["attendance"] = [1]  # First attendance
                elif record["name"] not in attended_users and record["attendance"]:
                    record["attendance"].append(0)  # Did not attend, previously attended
                elif record["name"] not in attended_users:
                    record["attendance"] = [0] # Did not attend

        else:
            await interaction.response.send_message("You dont have the required roles!")


        with open(SERVICE_RECORD_FILE, 'w') as f:
                json.dump(SERVICE_RECORD, f)
        
        await interaction.response.send_message(f"attendance updated")

    except Exception as e:
        print(e)


@client.tree.command(name="no_shows", description="list those who didnt come when they said they would")
@commands.cooldown(1, 5, commands.BucketType.default)
async def no_shows(interaction: discord.Interaction, no_shows: str):
    try:
        
        allowed_role_list = ["SAT"]
        user_role_list = [role.name for role in interaction.user.roles]

        if any(role in allowed_role_list for role in user_role_list):
            SERVICE_RECORD = load_data(SERVICE_RECORD_FILE)
            users = no_shows.split(",")

            for id, record in SERVICE_RECORD.items():
                
                if record["name"] in users:
                    # Ensure "no shows" key exists
                    if "no shows" not in record:
                        record["no shows"] = 0
                    
                    # Increment or set the no-show count
                    SERVICE_RECORD[id]["no shows"] += 1

        else:
            await interaction.response.send_message("You dont have the required roles!")


        with open(SERVICE_RECORD_FILE, 'w') as f:
                json.dump(SERVICE_RECORD, f)
        
        await interaction.response.send_message("no shows updated")

    except Exception as e:
        print(f"ERROR: {e}")


@client.tree.command(name="view_no_shows", description="view no_shows for a user")
@commands.cooldown(1, 5, commands.BucketType.default)
async def view_no_shows(interaction: discord.Interaction, user: str):
    try:
        
        allowed_role_list = ["Junior NCO", "Senior NCO", "Officer"]
        user_role_list = [role.name for role in interaction.user.roles]

        if any(role in allowed_role_list for role in user_role_list):
            SERVICE_RECORD = load_data(SERVICE_RECORD_FILE)
            
            # Check if user exists in SERVICE_RECORD
            user_record = None
            for record_key, record_value in SERVICE_RECORD.items():
                if record_value["name"] == user:
                    user_record = record_value
                    break
            
            if user_record:

                await interaction.response.send_message(f"No shows for {user}: {SERVICE_RECORD[record_key]['no shows']}")
            else:
                await interaction.response.send_message(f"No attendance record found for {user}.")
        
        else:
            await interaction.response.send_message("You don't have the required roles!")


    except Exception as e:
        print(e)


@client.tree.command(name="view_attendance", description="view attendance for a user")
@commands.cooldown(1, 5, commands.BucketType.default)
async def view_attendance(interaction: discord.Interaction, user: str):
    try:
        
        allowed_role_list = ["Junior NCO", "Senior NCO", "Officer"]
        user_role_list = [role.name for role in interaction.user.roles]

        if any(role in allowed_role_list for role in user_role_list):
            SERVICE_RECORD = load_data(SERVICE_RECORD_FILE)
            
            # Check if user exists in SERVICE_RECORD
            user_record = None
            for record_key, record_value in SERVICE_RECORD.items():
                if record_value["name"] == user:
                    user_record = record_value
                    break
            
            if user_record:
                overall_ops = len(user_record["attendance"])
                overall_attended = sum(user_record["attendance"])

                if overall_ops > 0: 
                    attendance_percentage = (overall_attended / overall_ops) * 100
                else:
                    attendance_percentage = 0

                await interaction.response.send_message(f"Attendance for {user}: {attendance_percentage:.2f}%")
            else:
                await interaction.response.send_message(f"No attendance record found for {user}.")
        
        else:
            await interaction.response.send_message("You don't have the required roles!")


    except Exception as e:
        print(e)
        
		### VIEW ORBAT COMMAND ###

@client.tree.command(name="lates", description="list those who didnt come when they said they would")
@commands.cooldown(1, 5, commands.BucketType.default)
async def lates(interaction: discord.Interaction, lates: str):
    try:
        
        allowed_role_list = ["SAT"]
        user_role_list = [role.name for role in interaction.user.roles]

        if any(role in allowed_role_list for role in user_role_list):
            SERVICE_RECORD = load_data(SERVICE_RECORD_FILE)
            users = lates.split(",")

            for id, record in SERVICE_RECORD.items():
                
                if record["name"] in users:
                    # Ensure "no shows" key exists
                    if "lates" not in record:
                        record["lates"] = 0
                    
                    # Increment or set the no-show count
                    SERVICE_RECORD[id]["lates"] += 1

        else:
            await interaction.response.send_message("You dont have the required roles!")


        with open(SERVICE_RECORD_FILE, 'w') as f:
                json.dump(SERVICE_RECORD, f)
        
        await interaction.response.send_message("lates updated")

    except Exception as e:
        print(f"ERROR: {e}")

@client.tree.command(name="view_lates", description="view lates for a user")
@commands.cooldown(1, 5, commands.BucketType.default)
async def view_lates(interaction: discord.Interaction, user: str):
    try:
        
        allowed_role_list = ["Junior NCO", "Senior NCO", "Officer"]
        user_role_list = [role.name for role in interaction.user.roles]

        if any(role in allowed_role_list for role in user_role_list):
            SERVICE_RECORD = load_data(SERVICE_RECORD_FILE)
            
            # Check if user exists in SERVICE_RECORD
            user_record = None
            for record_key, record_value in SERVICE_RECORD.items():
                if record_value["name"] == user:
                    user_record = record_value
                    break
            
            if user_record:

                await interaction.response.send_message(f"lates for {user}: {SERVICE_RECORD[record_key]['lates']}")
            else:
                await interaction.response.send_message(f"No attendance record found for {user}.")
        
        else:
            await interaction.response.send_message("You don't have the required roles!")


    except Exception as e:
        print(e)

@client.tree.command(name="ban", description="add people to the ban list")
@commands.cooldown(1, 5, commands.BucketType.default)
async def ban(interaction: discord.Interaction, steam64id: str):
    try:
        
        allowed_role_list = [ "Officer", "SAT"]
        user_role_list = [role.name for role in interaction.user.roles]

        if any(role in allowed_role_list for role in user_role_list):
            BANNED_LIST = load_data(BANNED_FILE_PATH)

            if steam64id not in BANNED_LIST["banned"]:
                BANNED_LIST["banned"].append(steam64id)
                await interaction.response.send_message(f"steam64 ID: **{steam64id}** added to banned list")
                with open(BANNED_FILE_PATH, 'w') as f:
                    json.dump(BANNED_LIST, f)

            else:
                await interaction.response.send_message(f"steam64 ID: **{steam64id}** already in banned list")

    except Exception as e:
        await interaction.response.send_message(f"ERROR: {e}\nplease screenshot this and sent it to boniface")

@client.tree.command(name="check_banned", description="add people to the ban list")
@commands.cooldown(1, 5, commands.BucketType.default)
async def check_banned(interaction: discord.Interaction, steam64id: str):
    try:
        
        allowed_role_list = [ "Officer", "SAT"]
        user_role_list = [role.name for role in interaction.user.roles]

        if any(role in allowed_role_list for role in user_role_list):
            BANNED_LIST = load_data(BANNED_FILE_PATH)

            if steam64id not in BANNED_LIST["banned"]:
                await interaction.response.send_message(f"steam64 ID: **{steam64id}** Is NOT banned")
                with open(BANNED_FILE_PATH, 'w') as f:
                    json.dump(BANNED_LIST, f)

            else:
                await interaction.response.send_message(f"steam64 ID: **{steam64id}** is in banned list, consult Keown immediately!")

    except Exception as e:
        await interaction.response.send_message(f"ERROR: {e}\nplease screenshot this and sent it to boniface")


@client.tree.command(
    name="view_orbat",
    description="view the ORBAT"
)
async def view_orbat(interaction=discord.Interaction):
    try:
        await interaction.channel.send(file=discord.File(ORBAT_IMAGE_PATH))
    except Exception as e:
        print(e)


client.run(BOT_KEY) # 20x Bot