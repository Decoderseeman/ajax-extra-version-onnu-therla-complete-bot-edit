import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
from info import ADMINS, LOG_CHANNEL
from database.ia_filterdb import save_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import temp
import re
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lock = asyncio.Lock()


@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    if query.data.startswith('index_cancel'):
        temp.CANCEL = True
        return await query.answer("ᴄᴀɴᴄᴇʟʟɪɴɢ ɪɴᴅᴇxɪɴɢ")
    _, raju, chat, lst_msg_id, from_user = query.data.split("#")
    if raju == 'reject':
        await query.message.delete()
        await bot.send_message(int(from_user),
                               f'**ʏᴏᴜʀ sᴜʙᴍɪssɪᴏɴ ғᴏʀ ɪɴᴅᴇxɪɴɢ** {chat} **ʜᴀs ʙᴇᴇɴ ᴅᴇᴄʟɪᴇɴᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs.**',
                               reply_to_message_id=int(lst_msg_id))
        return

    if lock.locked():
        return await query.answer('ᴡᴀɪᴛ ᴜɴᴛɪʟ ᴘʀᴇᴠɪᴏᴜs ᴘʀᴏᴄᴇss ᴄᴏᴍᴘʟᴇᴛᴇ.', show_alert=True)
    msg = query.message

    await query.answer('ᴘʀᴏᴄᴇssɪɴɢ...⏳', show_alert=True)
    if int(from_user) not in ADMINS:
        await bot.send_message(int(from_user),
                               f'**ʏᴏᴜʀ sᴜʙᴍɪssɪᴏɴ ғᴏʀ ɪɴᴅᴇxɪɴɢ** {chat} **ʜᴀs ʙᴇᴇɴ ᴀᴄᴄᴇᴘᴛᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴀɴᴅ ᴡɪʟʟ ʙᴇ ᴀᴅᴅᴇᴅ sᴏᴏɴ.**',
                               reply_to_message_id=int(lst_msg_id))
    await msg.edit(
        "**sᴛᴀʀᴛɪɴɢ ɪɴᴅᴇxɪɴɢ**",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('ᴄᴀɴᴄᴇʟ', callback_data='index_cancel')]]
        )
    )
    try:
        chat = int(chat)
    except:
        chat = chat
    await index_files_to_db(int(lst_msg_id), chat, msg, bot)


@Client.on_message((filters.forwarded | (filters.regex("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")) & filters.text ) & filters.private & filters.incoming)
async def send_for_index(bot, message):
    if message.text:
        regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(message.text)
        if not match:
            return await message.reply('Invalid link')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id  = int(("-100" + chat_id))
    elif message.forward_from_chat.type == 'channel':
        last_msg_id = message.forward_from_message_id
        chat_id = message.forward_from_chat.username or message.forward_from_chat.id
    else:
        return
    try:
        await bot.get_chat(chat_id)
    except ChannelInvalid:
        return await message.reply('**ᴛʜɪs ᴍᴀʏ ʙᴇ ᴀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟ / ɢʀᴏᴜᴘ. ᴍᴀᴋᴇ ᴍᴇ ᴀɴ ᴀᴅᴍɪɴ ᴏᴠᴇʀ ᴛʜᴇʀᴇ ᴛᴏ ɪɴᴅᴇx ᴛʜᴇ ғɪʟᴇs.**')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('**ɪɴᴠᴀʟɪᴅ ʟɪɴᴋ sᴘᴇᴄɪғɪᴇᴅ.**')
    except Exception as e:
        logger.exception(e)
        return await message.reply(f'Errors - {e}')
    try:
        k = await bot.get_messages(chat_id, last_msg_id)
    except:
        return await message.reply('**ᴍᴀᴋᴇ sᴜʀᴇ ᴛʜᴀᴛ ɪᴀᴍ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ, ɪғ ᴄʜᴀɴɴᴇʟ ɪs ᴘʀɪᴠᴀᴛᴇ**')
    if k.empty:
        return await message.reply('**ᴛʜɪs ᴍᴀʏ ʙᴇ ɢʀᴏᴜᴘ ᴀɴᴅ ɪᴀᴍ ɴᴏᴛ ᴀ ᴀᴅᴍɪɴ ᴏғ ᴛʜᴇ ɢʀᴏᴜᴘ.**')

    if message.from_user.id in ADMINS:
        buttons = [
            [
                InlineKeyboardButton('ʏᴇs',
                                     callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')
            ],
            [
                InlineKeyboardButton('ᴄʟᴏsᴇ', callback_data='close_data'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        return await message.reply(
            f'**ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɪɴᴅᴇx ᴛʜɪs ᴄʜᴀɴɴᴇʟ/ ɢʀᴏᴜᴘ ?**\n\n**ᴄʜᴀᴛ ɪᴅ**/ **ᴜsᴇʀɴᴀᴍᴇ** : <code>{chat_id}</code>\n**ʟᴀsᴛ ᴍᴇssᴀɢᴇ ɪᴅ**: <code>{last_msg_id}</code>',
            reply_markup=reply_markup)

    if type(chat_id) is int:
        try:
            link = (await bot.create_chat_invite_link(chat_id)).invite_link
        except ChatAdminRequired:
            return await message.reply('**ᴍᴀᴋᴇ sᴜʀᴇ ɪᴀᴍ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ ᴀɴᴅ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ɪɴᴠɪᴛᴇ ᴜsᴇʀs.**')
    else:
        link = f"@{message.forward_from_chat.username}"
    buttons = [
        [
            InlineKeyboardButton('ᴀᴄᴄᴇᴘᴛ ɪɴᴅᴇx',
                                 callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')
        ],
        [
            InlineKeyboardButton('ʀᴇᴊᴇᴄᴛ ɪɴᴅᴇx',
                                 callback_data=f'index#reject#{chat_id}#{message.message_id}#{message.from_user.id}'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await bot.send_message(LOG_CHANNEL,
                           f'**#ɪɴᴅᴇx ʀᴇϙᴜᴇsᴛ** \n\n**ʙʏ**: {message.from_user.mention} **(**<code>{message.from_user.id}</code>**)**\n**ᴄʜᴀᴛ ɪᴅ/ᴜsᴇʀ ɴᴀᴍᴇ -** <code> {chat_id}</code>\n**ʟᴀsᴛ ᴍᴇssᴀɢᴇ ɪᴅ -** <code>{last_msg_id}</code>\n**ɪɴᴠɪᴛᴇ ʟɪɴᴋ -** {link}',
                           reply_markup=reply_markup)
    await message.reply('**ᴛʜᴀɴᴋʏᴏᴜ ғᴏʀ ᴛʜᴇ ᴄᴏɴᴛʀɪʙᴜᴛɪᴏɴ, ᴡᴀɪᴛ ғᴏʀ ᴍʏ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴛᴏ ᴠᴇʀɪғʏ ᴛʜᴇ ғɪʟᴇs.**')


@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def set_skip_number(bot, message):
    if ' ' in message.text:
        _, skip = message.text.split(" ")
        try:
            skip = int(skip)
        except:
            return await message.reply("**sᴋɪᴘ ɴᴜᴍʙᴇʀ sʜᴏᴜʟᴅ ʙᴇ ᴀɴ ɪɴᴛᴇɢᴇʀ.**")
        await message.reply(f"**sᴜᴄᴄᴇsғᴜʟʟʏ sᴇᴛ sᴋɪᴘ ɴᴜᴍʙᴇʀ ᴀs** {skip}")
        temp.CURRENT = int(skip)
    else:
        await message.reply("**ɢɪᴠᴇ ᴍᴇ ᴀ sᴋɪᴘ ɴᴜᴍʙᴇʀ**")


async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    async with lock:
        try:
            total = lst_msg_id + 1
            current = temp.CURRENT
            temp.CANCEL = False
            while current < total:
                if temp.CANCEL:
                    await msg.edit("**sᴜᴄᴄᴇssғᴜʟʟʏ ᴄᴀɴᴄᴇʟʟᴇᴅ**")
                    break
                try:
                    message = await bot.get_messages(chat_id=chat, message_ids=current, replies=0)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    message = await bot.get_messages(
                        chat,
                        current,
                        replies=0
                    )
                except Exception as e:
                    logger.exception(e)
                try:
                    for file_type in ("document", "video", "audio"):
                        media = getattr(message, file_type, None)
                        if media is not None:
                            break
                        else:
                            continue
                    media.file_type = file_type
                    media.caption = message.caption
                    aynav, vnay = await save_file(media)
                    if aynav:
                        total_files += 1
                    elif vnay == 0:
                        duplicate += 1
                    elif vnay == 2:
                        errors += 1
                except Exception as e:
                    if "NoneType" in str(e):
                        if message.empty:
                            deleted += 1
                        elif not media:
                            no_media += 1
                        logger.warning("Skipping deleted / Non-Media messages (if this continues for long, use /setskip to set a skip number)")     
                    else:
                        logger.exception(e)
                current += 1
                if current % 20 == 0:
                    can = [[InlineKeyboardButton('ᴄᴀɴᴄᴇʟ', callback_data='index_cancel')]]
                    reply = InlineKeyboardMarkup(can)
                    await msg.edit_text(
                        text=f"**ᴛᴏᴛᴀʟ ᴍᴇssᴀɢᴇs ғᴇᴛᴄʜᴇᴅ** **:** <code>{current}</code>\n**ᴛᴏᴛᴀʟ ᴍᴇssᴀɢᴇs sᴀᴠᴇᴅ** **:** <code>{total_files}</code>\n**ᴅᴜᴘʟɪᴄᴀᴛᴇ ғɪʟᴇs sᴋɪᴘᴘᴇᴅ** **:** <code>{duplicate}</code>\n**ᴅᴇʟᴇᴛᴇᴅ ᴍᴇssᴀɢᴇs sᴋɪᴘᴘᴇᴅ** **:** <code>{deleted}</code>\n**ɴᴏɴ-ᴍᴇᴅɪᴀ ᴍᴇssᴀɢᴇs sᴋɪᴘᴘᴇᴅ** **:** <code>{no_media}</code>\n**ᴇʀʀᴏʀs ᴏᴄᴄᴜʀʀᴇᴅ** **:** <code>{errors}</code>",
                        reply_markup=reply)
        except Exception as e:
            logger.exception(e)
            await msg.edit(f'Error: {e}')
        else:
            await msg.edit(f'**sᴜᴄᴄᴇssғᴜʟʟʏ sᴀᴠᴇᴅ** <code>{total_files}</code> **ғɪʟᴇs ᴛᴏ ᴅᴀᴛᴀʙᴀsᴇ !**\n**ᴅᴜᴘʟɪᴄᴀᴛᴇ ғɪʟᴇs sᴋɪᴘᴘᴇᴅ** **:** <code>{duplicate}</code>\n**ᴅᴇʟᴇᴛᴇᴅ ᴍᴇssᴀɢᴇs sᴋɪᴘᴘᴇᴅ** **:** <code>{deleted}</code>\n**ɴᴏɴ-ᴍᴇᴅɪᴀ ᴍᴇssᴀɢᴇs sᴋɪᴘᴘᴇᴅ** **:** <code>{no_media}</code>\n**ᴇʀʀᴏʀs ᴏᴄᴄᴜʀʀᴇᴅ** **:** <code>{errors}</code>')
