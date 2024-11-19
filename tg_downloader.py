import asyncio
import logging
import os
import sys
import time
from asyncio import Task, Queue
from pathlib import Path
import pyroaddon
from pyrogram import Client, filters
from pyrogram.errors import MessageNotModified
from pyrogram.methods.utilities.idle import idle
from pyrogram.raw.functions.bots import SetBotCommands
from pyrogram.raw.types import BotCommand, BotCommandScopeDefault
from pyrogram.types import Message, Photo, Voice, Video, Animation, InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery, Audio, Document
from pyrogram.enums import ParseMode, MessageMediaType

from modules.ConfigManager import ConfigManager
from modules.helpers import get_config_from_user
from modules.models.ConfigFile import ConfigFile

GITHUB_LINK: str = "https://github.com/LightDestory/TG_MediaDownloader"
DONATION_LINK: str = "https://ko-fi.com/lightdestory"

config_manager: ConfigManager = ConfigManager(Path(os.environ.get("CONFIG_PATH", "./config.json")))
queue: Queue = asyncio.Queue()
tasks: list[Task] = []
workers: list[Task] = []

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("tg_downloader.log", mode="w+"),
        logging.StreamHandler(sys.stdout)
    ]
)


def init() -> Client | None:
    """
    This function initializes the Pyrogram client
    :return: A Pyrogram's client instance
    """
    config: ConfigFile
    if not config_manager.load_config_from_file():
        config = get_config_from_user()
        if config_manager.validate_config(config):
            config_manager.load_config(config)
            if not config_manager.save_config_to_file():
                exit(-1)
        else:
            exit(-1)
    else:
        config = config_manager.get_config()
    generate_workers(config.TG_MAX_PARALLEL)
    return Client(config.TG_SESSION, config.TG_API_ID, config.TG_API_HASH,
                  bot_token=config.TG_BOT_TOKEN, parse_mode=ParseMode.DEFAULT)


async def main() -> None:
    """
    Entrypoint of the bot runtime
    """
    try:
        logging.info("Bot is starting...")
        await app.start()
        logging.info("Settings Bot commands list...")
        await app.invoke(SetBotCommands(scope=BotCommandScopeDefault(), lang_code='', commands=get_command_list()))
        await idle()
        logging.info("Bot is stopping...")
        await app.stop()
        logging.info("Bot stopped!")
    except Exception as ex:
        logging.error(f"Unable to start Pyrogram client, error:\n {ex}")
    finally:
        await abort(kill_workers=True)


def generate_workers(quantity: int) -> None:
    loop = asyncio.get_event_loop_policy().get_event_loop()
    for i in range(quantity):
        workers.append(loop.create_task(worker()))


def get_command_list() -> list[BotCommand]:
    """
    This function returns the list of the implemented bot commands
    :return: A list of BotCommands
    """
    return [
        BotCommand(command="start", description="Initial command (invoked by Telegram) when you start the chat with "
                                                "the bot for the first time."),
        BotCommand(command="help", description="Gives you the available commands list."),
        BotCommand(command="about", description="Gives you information about the project."),
        BotCommand(command="abort", description="Cancel all the pending downloads."),
        BotCommand(command="status", description="Gives you the current configuration."),
        BotCommand(command="usage", description="Gives you the usage instructions."),
        BotCommand(command="set_download_dir", description="Sets a new download dir"),
        BotCommand(command="set_max_parallel_dl", description="Sets the number of max parallel downloads"),
    ]


def get_extension(media_type: MessageMediaType, media: Photo | Voice | Video | Animation | Audio | Document) -> str:
    """
    This function returns the most probable file extension based on the media type
    :param media_type: The media_type property of a message
    :param media: The media object of a message
    :return: A string corresponding to the file extension
    """
    if media_type == MessageMediaType.PHOTO:
        return "jpg"
    else:
        default = "unknown"
        if media_type in [MessageMediaType.VOICE, MessageMediaType.AUDIO]:
            default = "mp3"
        elif media_type in [MessageMediaType.ANIMATION, MessageMediaType.VIDEO]:
            default = "mp4"
        return default if not media.mime_type else media.mime_type.split("/")[1]


async def abort(kill_workers: bool = False) -> None:
    """
    This function abort all the current tasks, and kills workers if needed
    :param kill_workers: A control flag to kill all the workers
    """
    if tasks or not queue.empty():
        logging.info("Aborting all the pending jobs")
        for t in tasks:
            t.cancel()
        for _ in range(queue.qsize()):
            queue_item = queue.get_nowait()
            reply: Message = queue_item[1]
            await reply.edit("Aborted")
            queue.task_done()
    if kill_workers:
        logging.info("Killing all the workers")
        for w in workers:
            w.cancel()


# Enqueue a job
async def enqueue_job(message: Message, file_name: str) -> None:
    logging.info(f'Enqueueing media: {message.media} - {file_name}')
    reply = await message.reply_text("In queue", quote=True)
    queue.put_nowait([message, reply, file_name])


# Update download status
async def worker_progress(current, total, reply: list[Message]) -> None:
    status = int(current * 100 / total)
    message = reply[0]
    if status != 0 and status % 5 == 0 and str(status) not in message.text:
        reply[0] = await message.edit(f'Downloading: {status}%')


# Parallel worker to download media files
async def worker() -> None:
    while True:
        # Get a "work item" out of the queue.
        queue_item = await queue.get()
        message: Message = queue_item[0]
        reply: Message = queue_item[1]
        file_name: str = queue_item[2]
        file_path = os.path.join(config_manager.get_config().TG_DOWNLOAD_PATH, file_name)
        try:
            logging.info(f'{file_name} - Download started')
            reply = await reply.edit('Downloading:  0%')
            task = asyncio.get_event_loop().create_task(
                message.download(file_path, progress=worker_progress, progress_args=([reply],)))
            tasks.append(task)
            await asyncio.wait_for(task, timeout=config_manager.get_config().TG_DL_TIMEOUT)
            logging.info(f'{file_name} - Successfully downloaded')
            await reply.edit(f'Finished at {time.strftime("%H:%M", time.localtime())}')
        except MessageNotModified:
            pass
        except asyncio.CancelledError:
            logging.warning(f'{file_name} - Aborted')
            await reply.edit("Aborted")
        except asyncio.TimeoutError:
            logging.error(f'{file_name} - TIMEOUT ERROR')
            await reply.edit('**ERROR:** __Timeout reached downloading this file__')
        except Exception as e:
            logging.error(f'{file_name} - {str(e)}')
            await reply.edit(
                f'**ERROR:** Exception {(e.__class__.__name__, str(e))} raised downloading this file: {file_name}')

        # Notify the queue that the "work item" has been processed.
        queue.task_done()


app = init()


# On_Message Decorators
@app.on_message(
    filters.private & filters.user(users=config_manager.get_config().TG_AUTHORIZED_USER_ID) & filters.command("start"))
async def start_command(_, message: Message) -> None:
    logging.info("Executing command /start")
    await message.reply('**Greetings!** 👋\n'
                        'You have successfully set up the bot.\n' +
                        'I will download any supported media you send to me 😊\n\n' +
                        'To get help press /help'
                        )


@app.on_message(
    filters.private & filters.user(users=config_manager.get_config().TG_AUTHORIZED_USER_ID) & filters.command("help"))
async def help_command(_, message: Message) -> None:
    logging.info("Executing command /help")
    text: str = "**You can use the following commands:**\n\n"
    for command in get_command_list():
        text = text + f'/{command.command} -> __{command.description}__\n'
    await message.reply_text(text)


@app.on_message(
    filters.private & filters.user(users=config_manager.get_config().TG_AUTHORIZED_USER_ID) & filters.command("usage"))
async def usage_command(_, message: Message) -> None:
    logging.info("Executing command /usage")
    await message.reply_text(
        '**Usage:**\n\n'
        '__Forward to the bot any message containing a supported media file, it will be downloaded on the selected '
        'folder.__\n\n'
        '**Make sure to have TGCRYPTO module installed to get faster downloads!**'
    )


@app.on_message(
    filters.private & filters.user(users=config_manager.get_config().TG_AUTHORIZED_USER_ID) & filters.command("about"))
async def about_command(_, message: Message) -> None:
    logging.info("Executing command /about")
    await message.reply_text("This bot is free, but donations are accepted, and open source.\nIt is developed by "
                             "@LightDestory",
                             reply_markup=InlineKeyboardMarkup(
                                 [[
                                     InlineKeyboardButton("GitHub Repo", url=GITHUB_LINK),
                                     InlineKeyboardButton("Make a Donation!", url=DONATION_LINK)
                                 ]]
                             ))


@app.on_message(
    filters.private & filters.user(users=config_manager.get_config().TG_AUTHORIZED_USER_ID)
    & filters.command("set_download_dir"))
async def set_dl_path_command(_, message: Message) -> None:
    logging.info("Executing command /set_download_dir")
    await message.reply_text("Do you want to change the current download directory?",
                             reply_markup=InlineKeyboardMarkup(
                                 [[
                                     InlineKeyboardButton("Yes", callback_data="set_download_dir/yes"),
                                     InlineKeyboardButton("No", callback_data="set_download_dir/no")
                                 ]]
                             ))


@app.on_message(
    filters.private & filters.user(users=config_manager.get_config().TG_AUTHORIZED_USER_ID)
    & filters.command("set_max_parallel_dl"))
async def set_max_parallel_dl_command(_, message: Message) -> None:
    logging.info("Executing command /set_max_parallel_dl")
    await message.reply_text("To change the max parallel downloads all current tasks must be aborted, do you want to continue?",
                             reply_markup=InlineKeyboardMarkup(
                                 [[
                                     InlineKeyboardButton("Yes", callback_data="set_max_parallel_dl/yes"),
                                     InlineKeyboardButton("No", callback_data="set_max_parallel_dl/no")
                                 ]]
                             ))


@app.on_message(
    filters.private & filters.user(users=config_manager.get_config().TG_AUTHORIZED_USER_ID) & filters.command("abort"))
async def abort_command(_, message: Message) -> None:
    logging.info("Executing command /abort")
    await message.reply_text("Do you want to abort all the pending jobs?",
                             reply_markup=InlineKeyboardMarkup(
                                 [[
                                     InlineKeyboardButton("Yes", callback_data="abort/yes"),
                                     InlineKeyboardButton("No", callback_data="abort/no")
                                 ]]
                             ))


@app.on_message(
    filters.private & filters.user(users=config_manager.get_config().TG_AUTHORIZED_USER_ID) & filters.command("status"))
async def status_command(_, message: Message) -> None:
    logging.info("Executing command /status")
    await message.reply_text(
        '**Current configuration:**\n\n'
        f'**Download Path:** __{config_manager.get_config().TG_DOWNLOAD_PATH}__\n'
        f'**Concurrent Downloads:** {config_manager.get_config().TG_MAX_PARALLEL}\n'
        f'**Allowed Users:** {config_manager.get_config().TG_AUTHORIZED_USER_ID}\n\n'
    )


@app.on_message(filters.private & ~filters.user(users=config_manager.get_config().TG_AUTHORIZED_USER_ID))
async def no_auth_message(_, message: Message) -> None:
    logging.warning(f'Received message from unauthorized user ({message.from_user.id})')
    await message.reply_text("User is not allowed to use this bot!")


@app.on_message(filters.private & filters.user(users=config_manager.get_config().TG_AUTHORIZED_USER_ID) & filters.media)
async def media_message(_, message: Message) -> None:
    unsupported_types = [MessageMediaType.STICKER, MessageMediaType.CONTACT, MessageMediaType.LOCATION,
                         MessageMediaType.VENUE, MessageMediaType.POLL, MessageMediaType.WEB_PAGE,
                         MessageMediaType.DICE, MessageMediaType.GAME, MessageMediaType.VIDEO_NOTE]
    if message.media in unsupported_types:
        logging.warning(f'Received invalid media: {message.id} - {message.media}')
        await message.reply_text("This media is not supported!", quote=True)
    else:
        r_text = "This file does not have a file name. Do you want to use a custom file name instead of file_id?"
        r_markup = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("Yes", callback_data="media_rename/yes"),
                InlineKeyboardButton("No", callback_data="media_rename/no")
            ]]
        )
        if message.media in [MessageMediaType.PHOTO, MessageMediaType.VOICE]:
            await message.reply_text(r_text, quote=True, reply_markup=r_markup)
        elif message.media in [MessageMediaType.ANIMATION, MessageMediaType.AUDIO, MessageMediaType.VIDEO,
                               MessageMediaType.DOCUMENT]:
            media: Video | Animation | Audio | Document = getattr(message, message.media.value)
            if not media.file_name:
                await message.reply_text(r_text, quote=True, reply_markup=r_markup)
            else:
                await enqueue_job(message, media.file_name)


# On Callback decorators
@app.on_callback_query(
    filters.user(users=config_manager.get_config().TG_AUTHORIZED_USER_ID) & filters.regex(r"^abort/.+"))
async def abort_callback(_, callback_query: CallbackQuery) -> None:
    answer: str = callback_query.data.split("/")[1]
    await callback_query.edit_message_reply_markup()
    if answer == "yes":
        reply: str = "There are not jobs pending!"
        if tasks:
            await abort()
            reply = "All pending jobs have been terminated."
        await callback_query.edit_message_text(reply)
    else:
        await callback_query.edit_message_text("Operation cancelled")


@app.on_callback_query(
    filters.user(users=config_manager.get_config().TG_AUTHORIZED_USER_ID) & filters.regex(r"^set_download_dir/.+"))
async def set_dl_path_callback(client: Client, callback_query: CallbackQuery) -> None:
    message = callback_query.message
    answer: str = callback_query.data.split("/")[1]
    await callback_query.edit_message_reply_markup()
    if answer == "no":
        await callback_query.edit_message_text("Operation cancelled")
    else:
        await callback_query.edit_message_text("Enter the new download path in 60 seconds: ")
        try:
            response = await client.listen(message.chat.id, filters.text, timeout=60)
            reply_str: str
            if config_manager.change_download_path(response.text):
                reply_str = "The download dir has been changed successfully, new downloads will be redirected there"
            else:
                reply_str = "An error occurred while changing the download dir, please check logs!"
            await client.send_message(message.chat.id, text=reply_str)
        except asyncio.TimeoutError:
            await callback_query.edit_message_text("Operation cancelled")


@app.on_callback_query(
    filters.user(users=config_manager.get_config().TG_AUTHORIZED_USER_ID) & filters.regex(r"^set_max_parallel_dl/.+"))
async def set_max_parallel_dl_callback(client: Client, callback_query: CallbackQuery) -> None:
    message = callback_query.message
    answer: str = callback_query.data.split("/")[1]
    await callback_query.edit_message_reply_markup()
    if answer == "no":
        await callback_query.edit_message_text("Operation cancelled")
    else:
        await callback_query.edit_message_text("Enter the new max parallel downloads in 30 seconds: ")
        try:
            response = await client.listen(message.chat.id, filters.text, timeout=30)
            if config_manager.change_max_parallel_downloads(response.text):
                await abort(kill_workers=True)
                generate_workers(config_manager.get_config().TG_MAX_PARALLEL)
                reply_str = "The max parallel downloads has been changed successfully"
            else:
                reply_str = "An error occurred while changing the download dir, please check logs!"
            await client.send_message(message.chat.id, text=reply_str)
        except asyncio.TimeoutError:
            await callback_query.edit_message_text("Operation cancelled")


@app.on_callback_query(
    filters.user(users=config_manager.get_config().TG_AUTHORIZED_USER_ID) & filters.regex(r"^media_rename/.+"))
async def media_rename_callback(client: Client, callback_query: CallbackQuery) -> None:
    message = callback_query.message.reply_to_message
    if message:
        answer: str = callback_query.data.split("/")[1]
        media: Photo | Voice | Video | Animation | Audio | Document = getattr(message, message.media.value)
        ext: str = get_extension(message.media, media)
        if answer == "no":
            file_name = f'{media.file_unique_id}.{ext}'
            await callback_query.message.delete()
            await enqueue_job(message, file_name)
        else:
            await callback_query.edit_message_reply_markup()
            await callback_query.edit_message_text("Enter the name in 15 seconds or it will downloading using file_id.")
            try:
                response = await client.listen(message.chat.id, filters.text, timeout=15)
                file_name = f'{response.text}.{ext}'
                await callback_query.message.delete()
                await enqueue_job(message, file_name)
            except asyncio.TimeoutError:
                file_name = f'{media.file_unique_id}.{ext}'
                await callback_query.message.delete()
                await enqueue_job(message, file_name)
    else:
        await callback_query.edit_message_reply_markup()
        await callback_query.edit_message_text("The media's message is not available anymore (too long since input?")


app.run(main())
