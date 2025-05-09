from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, PeerFloodError, UserAlreadyParticipantError
from telethon.tl.functions.messages import AddChatUserRequest
import asyncio
import random
import logging
from telethon.sessions import StringSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_id = 6067591
api_hash = "94e17044c2393f43fda31d3afe77b26b"

client = TelegramClient('scraper_session', api_id, api_hash)

bot_token = "7758255754:AAH0wvr7nwSzEDq49UxhDi0hv0oVQvuRe_s"
source_group = None
target_group = None
logged_in = False
user_phone = None
members_added = 0

async def start_login(phone_number=+919680530736):
    global logged_in, user_phone

    if not phone_number:
        return

    user_phone = phone_number
    await client.connect()

    if not await client.is_user_authorized():
        await client.send_code_request(user_phone)
        logged_in = False
        logger.info("OTP sent. Waiting for code...")


@client.on(events.NewMessage(pattern='/setsource'))
async def set_source(event):
    global source_group

    if logged_in:
        group = event.message.text.split(" ", 1)
        if len(group) > 1:
            source_group = group[1]
            await event.respond(f"Source group set to {source_group}")
        else:
            await event.respond("Please provide the source group name or link.")
    else:
        await event.respond("You need to log in first using /login.")


@client.on(events.NewMessage(pattern='/settarget'))
async def set_target(event):
    global target_group

    if logged_in:
        group = event.message.text.split(" ", 1)
        if len(group) > 1:
            target_group = group[1]
            await event.respond(f"Target group set to {target_group}")
        else:
            await event.respond("Please provide the target group name or link.")
    else:
        await event.respond("You need to log in first using /login.")


async def add_member_with_delay(participant, target_group_entity, event):
    global members_added

    try:
        await client(AddChatUserRequest(
            target_group_entity, participant.id, fwd_limit=10
        ))

        members_added += 1
        logger.info(f"Added member {participant.id} to the target group. Total added: {members_added}")

        if members_added >= 150:
            wait_time = 3600
            logger.info(f"Flood limit reached. Waiting for {wait_time/60} minutes.")
            await asyncio.sleep(wait_time)
        elif members_added >= 30:
            wait_time = 600
            logger.info(f"Flood limit reached. Waiting for {wait_time/60} minutes.")
            await asyncio.sleep(wait_time)
        else:
            wait_time = random.uniform(30, 90)
            logger.info(f"Waiting for {wait_time:.2f} seconds before adding the next member.")
            await asyncio.sleep(wait_time)

        await event.respond(f"Added {participant.id} to the target group!")

    except PeerFloodError:
        await event.respond("Flood error encountered. Try again later.")
    except UserAlreadyParticipantError:
        await event.respond(f"{participant.id} is already a member.")
    except Exception as e:
        await event.respond(f"An error occurred while adding {participant.id}: {str(e)}")
        logger.error(f"Error adding member {participant.id}: {str(e)}")


@client.on(events.NewMessage(pattern='/scrap'))
async def scrap_members(event):
    global source_group, target_group

    if logged_in:
        if source_group and target_group:
            source_group_entity = await client.get_entity(source_group)
            target_group_entity = await client.get_entity(target_group)

            try:
                participants = await client.get_participants(source_group_entity)
                for participant in participants:
                    await add_member_with_delay(participant, target_group_entity, event)
            except Exception as e:
                await event.respond(f"An error occurred: {str(e)}")
        else:
            await event.respond("Please set both source and target groups using /setsource and /settarget.")
    else:
        await event.respond("You need to log in first using /login.")


async def start_bot():
    await client.start(bot_token=bot_token)
    print("Bot is running...")
    await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(start_bot())
    
