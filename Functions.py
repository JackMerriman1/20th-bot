import discord
import json
import pytz
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import time
import praw

members_cache = {}
cache_expiry = 60 * 5  # Cache expiry time in seconds

def generate_unix_timestamp_and_relative(date, time):
    # Combine date and time strings
    date_str = f'{date} {time}'

    # Parse the string into a datetime object
    date_format = '%d/%m/%Y %H:%M'
    dt = datetime.strptime(date_str, date_format)

    # Localize the datetime object to UTC (if needed)
    dt_utc = dt.replace(tzinfo=pytz.UTC)

    # Convert the datetime object to a Unix timestamp
    unix_timestamp = int(dt_utc.timestamp())

    # Format the timestamp for Discord
    discord_timestamp = f"<t:{unix_timestamp}>"
    relative_timestamp = f"<t:{unix_timestamp}:R>"

    return discord_timestamp, relative_timestamp, unix_timestamp

def load_data(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(e)

def save_data(filename, client):
    with open(filename, 'w') as f:
        json.dump(client.event_messages, f)

def create_embed(title, description, event_datetime=None):
    
    try:
        if event_datetime != None:
            embed = discord.Embed(title=title, description=f"{description}\nDate & Time: {event_datetime}")
        else:
            embed = discord.Embed(title=title, description=f"{description}")
        return embed
    except Exception as e:
        print(e)

def get_member_id(user, reaction=None):
    if reaction:
        guild = reaction.message.guild
        member = guild.get_member(user.id)
        member_id = str(member.id)
        return member_id

async def fetch_members(guild):
    try:
        # Check if the cache needs to be updated
        current_time = discord.utils.utcnow()
        if guild.id not in members_cache or (current_time - members_cache[guild.id]['timestamp']).total_seconds() > cache_expiry:
            # Fetching members from the cache
            members = guild.members
            # Update the cache
            members_cache[guild.id] = {
                'members': members,
                'timestamp': current_time
            }
        return members_cache[guild.id]['members']
    except Exception as e:
        print(f"An error occurred: {e}")

async def not_reacted_list(message_id, guild_id, client):
    try:
        reacted = []
        not_reacted = []
        members = []
        guild = client.get_guild(guild_id)
        members_objects = await fetch_members(guild)

        # Create a list of user nicknames who have reacted, if not nick then use name
        for key, value in client.event_messages[message_id].items():
            if isinstance(value, list) and "platoon" in key.lower():
                for member_id in value:
                    for member_object in members_objects:
                        if str(member_object.id) == str(member_id):
                            if member_object.nick:
                                reacted.append(member_object.nick)
                            else:
                                reacted.append(member_object.name)

        # Create a list of all members by nick. If no nick then use name
        for member in members_objects:
            if member.nick:
                members.append((member.nick, member.roles))
            else:
                members.append((member.name, member.roles))
                
        member_roles_allowed = ["1 Platoon", "2 Platoon", "3 Platoon", "Reserves"]
        not_reacted = [name for name, roles in members if name not in reacted and any(role.name in member_roles_allowed for role in roles)]

        return not_reacted
    except Exception as e:
        print(f"An error occurred: {e}")

async def post_rsvp_list(message_id, event_name, event_date, channel, client, guild_id):
    try:
        # Create an embed to display the RSVP list
        channel = client.get_channel(channel)
        
        not_reacted = await not_reacted_list(message_id, guild_id, client)
        embed = create_embed(f"RSVP List for {event_name}", "See event message for event details")
        embed.add_field(name="Roles", value="No RSVPs yet", inline=False)
        embed.add_field(name="Not Reacted", value="\n".join(not_reacted))

        rsvp_message = await channel.send(embed=embed)

        # Store the RSVP message ID and channel ID to update it later
        client.event_messages[message_id]['rsvp_message_id'] = rsvp_message.id
        client.event_messages[message_id]['rsvp_channel_id'] = channel.id

    except Exception as e:
        print(f"An error occurred: {e}")

async def update_rsvp_list(message_id, client, guild_id):
    try:
        # Check if RSVP message and channel IDs are available
        if 'rsvp_message_id' not in client.event_messages[message_id] or 'rsvp_channel_id' not in client.event_messages[message_id]:
            return

        channel_id = client.event_messages[message_id]['rsvp_channel_id']
        channel = client.get_channel(channel_id)
        if channel is None:
            print(f"Channel with ID {channel_id} not found.")
            return

        rsvp_message_id = client.event_messages[message_id]['rsvp_message_id']
        rsvp_message = await channel.fetch_message(rsvp_message_id)
        if rsvp_message is None:
            print(f"RSVP message with ID {rsvp_message_id} not found.")
            return

        embed = create_embed(rsvp_message.embeds[0].title, rsvp_message.embeds[0].description)

        # Fetch all members and their roles in one go
        all_members = await fetch_members(channel.guild)

        # Get all reacted member IDs
        reacted_member_ids = set()
        for role, member_ids in client.event_messages[message_id].items():
            if role in ['rsvp_message_id', 'rsvp_channel_id']:
                continue
            reacted_member_ids.update(member_ids)

        # Define roles allowed for RSVP
        member_roles_allowed = ["1 Platoon", "2 Platoon", "3 Platoon", "Reserves"]

        # Determine members who have not reacted
        not_reacted = []
        members_with_nicknames = {role: [] for role in client.event_messages[message_id] if role not in ['rsvp_message_id', 'rsvp_channel_id']}
        
        for member in all_members:
            member_id = str(member.id)
            nickname = member.nick if member.nick else member.name
            
            # Check if the member has reacted
            if member_id not in reacted_member_ids:
                if any(role.name in member_roles_allowed for role in member.roles):
                    not_reacted.append(nickname)
            else:
                # Add members to their respective roles
                for role, member_ids in client.event_messages[message_id].items():
                    if role not in ['rsvp_message_id', 'rsvp_channel_id'] and member_id in member_ids:
                        members_with_nicknames[role].append(nickname)

        # Add fields to the embed for each role
        for role, nicknames in members_with_nicknames.items():
            if nicknames:
                embed.add_field(name=f"**{role}**", value="\n".join(nicknames), inline=False)
            else:
                embed.add_field(name=role, value="No RSVPs yet", inline=False)

        if not_reacted:
            embed.add_field(name="Not Reacted", value="\n".join(not_reacted), inline=False)

        # Update the RSVP message with the new embed
        await rsvp_message.edit(embed=embed)

    except Exception as e:
        print(f"An error occurred while updating RSVP list: {e}")

def send_email_with_json(smtp_server, smtp_port, sender_email, sender_password, recipient_email, subject, body, json_file_path):
    # Create the MIME message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach the JSON file
    with open(json_file_path, 'r') as json_file:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(json_file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={json_file_path.split("/")[-1]}')

    msg.attach(part)

    # Send the email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def run_email_scheduler():
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = '20xdiscordbot@gmail.com'
    sender_password = 'oemm sreu hclw gdzm'
    recipient_email = 'jack.merriman2@gmail.com'
    subject = 'Subject: Service Records JSON File'
    body = 'Please find the attached JSON file.'
    json_file_path = 'service_record_data.json'

    while True:
        send_email_with_json(smtp_server, smtp_port, sender_email, sender_password, recipient_email, subject, body, json_file_path)
        print("Email sent. Waiting for 3 days to send the next email.")
        time.sleep(60*60*24*3)

def get_last_post_time(timestamp_file):
    if os.path.exists(timestamp_file):
        with open(timestamp_file, "r") as f:
            data = json.load(f)
            return datetime.fromisoformat(data["last_post_time"])
    return None

# Function to update the timestamp of the last post
def update_last_post_time(timestamp_file):
    with open(timestamp_file, "w") as f:
        data = {"last_post_time": datetime.now().isoformat()}
        json.dump(data, f)

# Function to check if 48 hours have passed
def can_post(timestamp_file):
    last_post_time = get_last_post_time(timestamp_file)
    if last_post_time is None:
        return True  # No record, so allow posting
    return datetime.now() >= last_post_time + timedelta(hours=48)