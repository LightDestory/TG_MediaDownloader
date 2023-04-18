<a name="readme-top"></a>

<!-- Presentation Block -->
<br />

<div align="center">

  <a href="https://github.com/LightDestory/TG_MediaDownloader">
    <img src="https://raw.githubusercontent.com/LightDestory/TG_MediaDownloader/master/.github/assets/images/presentation_image.gif" alt="Preview" width="90%">
  </a>

  <h2 align="center">TG Media Downloader Bot 🤖</h2>
  
  <p align="center">
A simple MTProto-based bot that can download various types of media (>10MB) on a local storage
  </p>
  
  <br />
  <br />

</div>

<!-- ToC -->

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#book-about-the-project">📖 About The Project</a>
      <ul>
        <li><a href="#why-should-i-use-a-mtproto-bot-">Why should I use a MTProto bot?</a></li>
      </ul>
    </li>
    <li>
      <a href="#gear-getting-started">⚙️ Getting Started</a>
      <ul>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#usage">Usage</a></li>
        <li><a href="#generating-telegram-api-keys">Generating Telegram API keys</a></li>
        <li><a href="#creating-a-telegram-bot">Creating a Telegram Bot</a></li>
        <li><a href="#to-do">TO-DO</a></li>
      </ul>
    </li>
    <li><a href="#dizzy-contributing">💫 Contributing</a></li>
    <li><a href="#handshake-support">🤝 Support</a></li>
    <li><a href="#warning-license">⚠️ License</a></li>
    <li><a href="#hammer_and_wrench-built-with">🛠️ Built With</a></li>
  </ol>
</details>

<!-- About Block -->

## :book: About The Project

A telegram bot based on [Pyrogram](https://github.com/pyrogram/pyrogram) that downloads on a local storage the following
media files: _animation, audio, document, photo, video, voice_.

_The bot is inspired from the [Telethon-based](https://github.com/rodriguezst/telethon_downloader) bot
by [rodriguezst](https://github.com/rodriguezst)._

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Why should I use a MTProto bot?

MTProto clients connect directly to Telegram’s servers, which means there is no HTTP connection, no “polling” or “web hooks”. This means less overhead, since the protocol used between you and the server is much more compact than HTTP requests with responses in wasteful JSON.

Since there is a direct connection to Telegram’s servers, even if their Bot API endpoint is down, you can still have connection to Telegram directly.

Using a MTProto client, you are also not limited to the public API that they expose, and instead, you have full control of what your bot can do.

HTTP Bots can't download file bigger than 10mb meanwhile MTProto can download files of 1.5~4GB!

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- Setup Block -->

## :gear: Getting Started

The bot requires the following parameters to work:

| Parameter                  | Role                                                                                                                                                               |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| __TG_API_ID__                  | Telegram API ID obtained via developer settings (see [here](#generating-telegram-api-keys))                                                                        |
| __TG_API_HASH__                | Telegram API HASH obtained via developer settings (see [here](#generating-telegram-api-keys))                                                                      |
| __TG_BOT_TOKEN__               | Telegram Bot Token obtained via BotFather (see [here](#creating-a-telegram-bot))                                                                                   |
| __TG_MAX_PARALLEL__ [OPTIONAL] | Maximum number of parallel downloads allowed (default: 4) <br>_A big number can cause flood blocks_                                                                 |
| __TG_DL_TIMEOUT__ [OPTIONAL]   | Maximum time (in seconds) to wait for a download to complete (default: 5400)<br>_In case of timeout the download is aborted and a error is triggered_              |
| __TG_DOWNLOAD_PATH__           | Download folder on the local storage/docker mount where the files will be downloaded<br>_The files will appear inside the folder only after download completation_ |
| __TG_AUTHORIZED_USER_ID__      | List separated by comma of authorized users' id, you can get them using the [userinfobot](https://github.com/nadam/userinfobot) <br>_It can't be empty_            |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Installation

The bot can be executed inside a Docker container or directly on your PC/Server OS.

<details>
      <summary>Docker</summary>
        To dockerize the bot, just pull or build the image and provide the required parameters.<br/><br>
        An official GitHub Package is
        available <a href="https://github.com/LightDestory/TG_MediaDownloader/pkgs/container/        tg_mediadownloader">here</a>.<br/><br/>
        <i>Make sure that the download path is a mounted as a volume to allow the host system to access the downloaded files.</i>
</details>

<details>
      <summary>Barebone</summary>
        To run the bot directly on your PC/Server OS, do the following steps:

  
1) Make sure to have Python 3.10+ installed on your system;
2) Create a folder anywhere on your pc and clone the repository there:

   `git clone https://github.com/LightDestory/TG_MediaDownloader`

3) Install the requirements (create a `venv` if you don't want to dirty the system packages): 

   `pip install -r requirements.txt`

4) Execute the bot and follow the wizard to provide the requires parameters:

   `python ./tg_downloader.py`
   
</details>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Usage

After the setting up process, the bot is ready to use. Send/forward any supported media to the bot to start the download on your local storage.

The bot supports the following commands:
| Command | Role |
| --------- | ---------------------------------------------------------------------------------------------- |
| `/start`  | Initial command (invoked by Telegram) when you start the chat with the bot for the first time. |
| `/help`   | Gives you the available commands list. |
| `/about`  | Gives you information about the project. |
| `/abort`  | Cancel all the pending downloads. |
| `/status` | Gives you the current configuration. |
| `/usage`  | Gives you the usage instructions. |
| `/set_download_dir`  | Sets a new download dir. |
| `/set_max_parallel_dl`  | Sets the number of max parallel downloads. |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Generating Telegram API keys

To make the bot work you must provide your own API ID and hash:

1. Go to [My Telegram](https://my.telegram.org/) and login with your phone number;
2. Click under API Development tools;
3. A _Create new application_ window will appear. Fill in your application details. There is no need to enter any _URL_,
   and only the first two fields (_App title_ and _Short name_) can currently be changed later;
4. Click on _Create application_ at the end. Remember that your __API ID and API Hash are secrets__ and Telegram won't
   let you revoke it. __Don't post it anywhere!__

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Creating a Telegram Bot

1. Open a conversation with [@BotFather](https://telegram.me/botfather) in Telegram
2. Use the /newbot command to create a new bot. The BotFather will ask you for a name and username, then it will generate an
   authorization token for your new bot.

    * The name of your bot is displayed in contact details and elsewhere.
    * The Username is a short name, to be used in mentions and telegram.me links. Usernames are 5-32 characters long and
      are case-insensitive, but may only include Latin characters, numbers, and underscores. Your bot`s username must
      end in ‘bot’, e.g. ‘tetris_bot’ or ‘TetrisBot’.
    * The token is a string along the lines of 110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw that is required to
      authorize the bot and send requests to the Bot API. Keep your token secure and store it safely, it can be used by
      anyone to control your bot.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### TO-DO

- [x] It runs
- [x] It downloads supported media
- [x] Use a fallback for missing metadata
- [x] Allow custom names for un-named files instead of file_unique_id
- [x] On the fly configuration changes
- [ ] Improve error handling related to Telegram's service

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- Contribute Block -->

## :dizzy: Contributing

If you are interested in contributing, please refer to [Contributing Guidelines](.github/CONTRIBUTING.md) for more information and take a look at open issues. Ask any questions you may have and you will be provided guidance on how to get started.

Thank you for considering contributing.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- Support Block -->

## :handshake: Support

If you find value in my work, please consider making a donation to help me create, and improve my projects.

Your donation will go a long way in helping me continue to create free software that can benefit people around the world.

<p align="center">
<a href='https://ko-fi.com/M4M6KC01A' target='_blank'><img src='https://raw.githubusercontent.com/LightDestory/TG_MediaDownloader/master/.github/assets/images/support.png' alt='Buy Me a Hot Chocolate at ko-fi.com' width="45%" /></a>
</p>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- License Block -->

## :warning: License

The content of this repository is distributed under the GNU GPL-3.0 License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- Built With Block -->

## :hammer_and_wrench: Built With

- [Python](https://www.python.org/)
- [Pyrogram](https://github.com/pyrogram/pyrogram)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
