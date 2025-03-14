# Uncute Rina

TransPlace's somewhat random bot with a lot of interesting and funky additions for the server.
It is also in the Transonance and EnbyPlace servers.

## Installation

- Copy the GitHub (basically: download all the files)
- Install python 3.12.4 (or newer, maybe) (https://www.python.org/downloads/)

Also run the following commands to install the modules of the most recent discord.py version (v2.0) and pymongo for the online database

You will need a mongo database to use this bot. For more info, look at https://mongodb.com/

[//]: # (- pip install -U git+https://github.com/Rapptz/discord.py/)
[//]: # (I likely won't be using the latest version anymore: only the stables)
[//]: # (`pip install -r requirements.txt` or add `--upgrade` and/or `--force-reinstall`)
- `pip install -r requirements.txt --upgrade`

## Usage

Add an api_keys.json file in the same folder as the program, in which you add your API tokens:

```
{
    "Discord"             : "",
    "MongoDB"             : "",
    "Open Exchange Rates" : "",
    "Wolfram Alpha"       : ""
}
```

Put the discord token, the MongoDB connection string from your databasem, and potential other API keys you might want to use into this file. API keys don't have to have a value (an empty string), but they do have to be added to the file. Missing keys will give descriptive errors upon program startup.

Some IDs are still hardcoded. This should be reworked at some point in the future (2024-07-17). Some of the IDs can be found in the Bot class (resources/customs/bot.py). The key names may be descriptive enough. There are some in the EnabledServers class (resources/customs/utils.py) and FunAddons.on_message (extensions/addons.py). If you need help, reach out to me following the details in the Support section.

Note: The bot automatically checks if it's in the main server in the setup_hook function (in main.py). If it isn't, it will set the variable running_in_production of the Bot client instance (resources/customs/bot.py) to False. You may need to change the IDs of all instances of "client.fetch_channel(...)" and "client.fetch_guild(...)" if you're running the bot in an entirely different environment.

Direct yourself to the right directory/folder (in a terminal; or so I'd like to run it) (cd C:\Users\USER\x\) and run the main file using `python main.py`

## Support

DM MysticMia in the TransPlace server. You may have to pass through a verification system but the verifiers will surely let you dm me. Join TransPlace with https://discord.gg/transplace

## Roadmap

There are no real future plans for now. Whatever I want to add usually gets added within the first week after thinking about it or getting it suggested to me. Potential long-term issues or ideas can be found in the GitHub Issues tab.

## Contributing

To contribute, you must first be part of the TransPlace Bot Development team. However, you can still give suggestions for ideas or code by contacting me (see the Support section) or by using /developer-request in one of the servers with Rina.

## Authors and acknowledgment

Thank you to whoever is keeping up the discord.py framework (and the other installed pip modules)

## License

Feel free to use whatever. Feel free to cite me as source if you want. Would be cool to have recognition from some random person on the internet :).

## Project status
(last updated 2024-07-10): This project is being somewhat maintained by whichever requests and suggestions I get from people.
