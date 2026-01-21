<a href="https://github.com/stngularity"><img src="https://img.shields.io/badge/-stngularity's%20project-%2379a051"></a>
<a href="https://github.com/stngularity/befri"><img src="https://img.shields.io/badge/version-v0.0.1a-%2379a051"></a>
<br>
<a href="https://github.com/stngularity/befri/issues"><img src="https://img.shields.io/github/issues/stngularity/befri?color=%2379a051&label=issues"></a>
<a href="https://github.com/stngularity/befri/pulls"><img alt="pull_requests" src="https://img.shields.io/github/issues-pr/stngularity/befri?label=pull%20requests&color=%2379a051"></a>
<a href="https://github.com/stngularity/befri"><img src="https://img.shields.io/github/license/stngularity/befri?color=%2379a051&label=license"></a>

## Notification
This project was created as an experiment. Basically, I'm just "training" my programming skills.

My code may look scary, unreadable, or inefficient. If you notice anything like that, please let me know, and I'll try to fix it.

Thank you for reading this note.
Yours, still nameless, stngularity.

## What it is?
`Befri` is a bot for Discord. According to the plan, it will have a lot of features *(any that come to mind, to be more precise)*.

You **can** use it as a basis for your own bots if you want, but I strongly advise against doing so. I don't know myself whether something in it will break at some point.

You can see the development plans in [TODO.md](/TODO.md).

## How to start
**[Python 3.11](https://www.python.org/downloads/) or higher is required**

###### 1. Copy, create venv & install requirements
To start the bot, first run these commands:
```ps1
$ git clone https://github.com/stngularity/befri.git
$ cd befri
$ python -m venv .venv --upgrade-deps
$ & ".venv\Scripts\Activate.ps1"
$ pip install -U -r requirements.txt
```

###### 2. Token
After completing these commands, create an application (if you don't have one) on the [developer portal](https://discord.com/developers/applications). Then open the `Bot` tab for the application. There, click on the `Reset Token` button and copy the token you receive.

Then create a `.env` file in the root directory of the bot with the following content:
```ini
BOT_TOKEN=<token_of_bot_from_developers_portal>
```
> Instead of creating a file, you can simply create a variable with the same name and value in the environment.

###### 3. Configure
After specifying the token, open the bot configuration (`config.yml`) and configure everything as desired.

###### 4. Start
Finally, execute this command while in the Python virtual environment:
```ps1
$ python src
```

## License
This project is distributed under the `MIT` license. You can learn more from the [LICENSE](/LICENSE) file.

```
Made with ❤ and 🍵 by stngularity for everyone!
```