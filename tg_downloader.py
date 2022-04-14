import asyncio
import logging
import os
import sys
import time
from asyncio import Task
from typing import Union

from pyromod import listen
from pyrogram import Client, filters
from pyrogram.methods.utilities.idle import idle
from pyrogram.raw.types import BotCommand, BotCommandScopeDefault
from pyrogram.raw.functions.bots import SetBotCommands
from pyrogram.types import Message, Photo, Voice, Video, Animation, InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery, Audio, Document
from pyrogram.errors import MessageNotModified

GITHUB_LINK = "https://github.com/LightDestory/TG_MediaDownloader"
DONATION_LINK = "https://coindrop.to/lightdestory"
download_path = ""
parallel_downloads = 0
download_timeout = 0
authorized_users = []
queue = asyncio.Queue()
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


# Helper function to get missing env variables
def get_env(name: str, message: str, cast=str) -> Union[int, str]:
    if name in os.environ:
        return os.environ[name]
    while True:
        try:
            return cast(input(message))
        except KeyboardInterrupt:
            print("\n")
            logging.info("Invoked interrupt during input request, closing process...")
            exit(0)
        except ValueError as e:
            logging.error(e)
            time.sleep(1)


# Check env-vars and initialize the client
def init() -> Client:
    global download_path, parallel_downloads, download_timeout, authorized_users
    session = os.environ.get('TG_SESSION', 'tg_downloader')
    api_id = get_env('TG_API_ID', 'Enter your API ID: ', int)
    api_hash = get_env('TG_API_HASH', 'Enter your API hash: ')
    bot_token = get_env('TG_BOT_TOKEN', 'Enter your Telegram BOT token: ')
    download_path = get_env('TG_DOWNLOAD_PATH', 'Enter full path to downloads directory: ')
    parallel_downloads = int(os.environ.get('TG_MAX_PARALLEL', 4))
    download_timeout = int(os.environ.get('TG_DL_TIMEOUT', 5400))
    while True:
        authorized_users = get_env('TG_AUTHORIZED_USER_ID',
                                   "Enter the list authorized users' id (separated by comma, can't be empty): ")
        authorized_users = [int(user_id) for user_id in authorized_users.split(",")] if authorized_users else []
        if authorized_users:
            break
    # Setting up job queue and workers
    for i in range(parallel_downloads):
        loop = asyncio.get_event_loop()
        workers.append(loop.create_task(worker()))

    return Client(session, api_id, api_hash, bot_token=bot_token, parse_mode="combined")


# Returns the list of BotCommand
def get_command_list() -> list[BotCommand]:
    return [
        BotCommand(command="start", description="Initial command (invoked by Telegram) when you start the chat with "
                                                "the bot for the first time."),
        BotCommand(command="help", description="Gives you the available commands list."),
        BotCommand(command="about", description="Gives you information about the project."),
        BotCommand(command="abort", description="Cancel all the pending downloads."),
        BotCommand(command="status", description="Gives you the current configuration."),
        BotCommand(command="usage", description="Gives you the usage instructions."),
    ]


# Returns the most probable file extension
def get_extension(media_type: str, media: Union[Photo, Voice, Video, Animation, Audio, Document]) -> str:
    if media_type == "photo":
        return "jpg"
    else:
        default = "unknown"
        if media_type in ['voice', "audio"]:
            default = "mp3"
        elif media_type in ['animation', 'video']:
            default = "mp4"
        return default if not media.mime_type else media.mime_type.split("/")[1]


# Clean-up helper to remove workers and pending jobs
async def abort(kill_workers: bool = False) -> None:
    if tasks or not queue.empty():
        logging.info("Aborting all the pending jobs")
        for t in tasks:
            t.cancel()
        for _ in range(queue.qsize()):
            queue.get_nowait()
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
        file_path = os.path.join(download_path, file_name)
        try:
            logging.info(f'{file_name} - Download started')
            reply = await reply.edit('Downloading:  0%')
            task = asyncio.get_event_loop().create_task(
                message.download(file_path, progress=worker_progress, progress_args=([reply],)))
            tasks.append(task)
            await asyncio.wait_for(task, timeout=download_timeout)
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


async def main() -> None:
    logging.info("Bot is starting...")
    await app.start()
    # Setting commands
    logging.info("Settings Bot commands list...")
    await app.send(SetBotCommands(scope=BotCommandScopeDefault(), lang_code='', commands=get_command_list()))
    await idle()
    logging.info("Bot is stopping...")
    await abort(kill_workers=True)
    await app.stop()
    logging.info("Bot stopped!")


app = init()


# On_Message Decorators
@app.on_message(filters.private & filters.user(users=authorized_users) & filters.command("start"))
async def start_command(_, message: Message) -> None:
    logging.info("Executing command /start")
    await message.reply('**Greetings!** 👋\n'
                        'You have successfully set up the bot.\n' +
                        'I will download any supported media you send to me 😊\n\n' +
                        'To get help press /help'
                        )


@app.on_message(filters.private & filters.user(users=authorized_users) & filters.command("usage"))
async def usage_command(_, message: Message) -> None:
    logging.info("Executing command /usage")
    await message.reply_text(
        '**Usage:**\n\n'
        '__Forward to the bot any message containing a supported media file, it will be downloaded on the selected '
        'folder.__\n\n'
        '**Make sure to have TGCRYPTO module installed to get faster downloads!**'
    )


@app.on_message(filters.private & filters.user(users=authorized_users) & filters.command("about"))
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


@app.on_message(filters.private & filters.user(users=authorized_users) & filters.command("abort"))
async def abort_command(_, message: Message) -> None:
    logging.info("Executing command /abort")
    await message.reply_text("Do you want to abort all the pending jobs?",
                             reply_markup=InlineKeyboardMarkup(
                                 [[
                                     InlineKeyboardButton("Yes", callback_data="abort/yes"),
                                     InlineKeyboardButton("No", callback_data="abort/no")
                                 ]]
                             ))


@app.on_message(filters.private & filters.user(users=authorized_users) & filters.command("status"))
async def status_command(_, message: Message) -> None:
    logging.info("Executing command /status")
    await message.reply_text(
        '**Current configuration:**\n\n'
        f'**Download Path:** __{download_path}__\n'
        f'**Concurrent Downloads:** {parallel_downloads}\n'
        f'**Allowed Users:** {authorized_users}\n\n'
        '__Currently on-the-fly configuration changes are not supported!__'
    )


@app.on_message(filters.private & filters.user(users=authorized_users) & filters.command("help"))
async def help_command(_, message: Message) -> None:
    logging.info("Executing command /help")
    text: str = "**You can use the following commands:**\n\n"
    for command in get_command_list():
        text = text + f'/{command.command} -> __{command.description}__\n'
    await message.reply_text(text)


@app.on_message(filters.private & ~filters.user(users=authorized_users))
async def no_auth_message(_, message: Message) -> None:
    logging.warning(f'Received message from unauthorized user ({message.from_user.id})')
    await message.reply_text("User is not allowed to use this bot!")


@app.on_message(filters.private & filters.user(users=authorized_users) & filters.media)
async def media_message(_, message: Message) -> None:
    unsupported_types = ['sticker', 'contact', 'location', 'venue', 'poll', 'web_page', 'dice', 'game', 'video_note']
    if message.media in unsupported_types:
        logging.warning(f'Received invalid media: {message.message_id} - {message.media}')
        await message.reply_text("This media is not supported!", quote=True)
    else:
        r_text = "This file does not have a file name. Do you want to use a custom file name instead of file_id?"
        r_markup = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("Yes", callback_data="media_rename/yes"),
                InlineKeyboardButton("No", callback_data="media_rename/no")
            ]]
        )
        if message.media in ["photo", 'voice']:
            await message.reply_text(r_text, quote=True, reply_markup=r_markup)
        elif message.media in ['animation', "audio", 'video', 'document']:
            media: Union[Video, Animation, Audio, Document] = getattr(message, message.media)
            if not media.file_name:
                await message.reply_text(r_text, quote=True, reply_markup=r_markup)
            else:
                await enqueue_job(message, media.file_name)


# On Callback decorators
@app.on_callback_query(filters.user(users=authorized_users) & filters.regex(r"^abort/.+"))
async def abort_callback(_, callback_query: CallbackQuery) -> None:
    answer: str = callback_query.data.split("/")[1]
    if answer == "yes":
        reply: str = "There are not jobs pending!"
        if tasks:
            await abort()
            reply = "All pending jobs have been terminated."
        await callback_query.edit_message_reply_markup()
        await callback_query.edit_message_text(reply)
    else:
        await callback_query.edit_message_reply_markup()
        await callback_query.edit_message_text("Operation cancelled")


@app.on_callback_query(filters.user(users=authorized_users) & filters.regex(r"^media_rename/.+"))
async def media_rename_callback(client: Client, callback_query: CallbackQuery) -> None:
    message = callback_query.message.reply_to_message
    if message:
        answer: str = callback_query.data.split("/")[1]
        media: Union[Photo, Voice, Video, Animation, Audio, Document] = getattr(message, message.media)
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
