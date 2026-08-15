# Uncute Rina

TransPlace's somewhat random bot with a lot of interesting and funky additions for the server.
It is also in the Transonance and EnbyPlace servers.

## Installation

- Copy/clone the GitHub Repo (basically: download all the files)
- Install python 3.14.7 (or newer, maybe) (https://www.python.org/downloads/)

Also run the following commands to install the modules of the most recent discord.py version (v2.7?) and pymongo for the online database

[//]: # (- pip install -U git+https://github.com/Rapptz/discord.py/)
[//]: # (I likely won't be using the latest version anymore: only the stables)
[//]: # (`pip install -r requirements.txt` or add `--upgrade` and/or `--force-reinstall`)
- `pip install -r requirements.txt --upgrade`

You will need a mongo database to use this bot. For more info, look at https://mongodb.com/

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

Put the discord token, the MongoDB connection string from your database,
and potential other API keys you might want to use into this file.
API keys don't have to have a value (an empty string), but they do have to be added to the file.
Missing keys will give descriptive errors upon program startup.

Some IDs are still hardcoded. This has been mostly reworked by now (2026-08-15),
but IDs can still be found in main.py, funaddons, otheraddons, and crashhandeling.
The easiest way to find them it by using this RegEx query: `[0-9]{17,20}`.
If you need help, reach out to me following the details in the Support section.

Direct yourself to the right directory/folder
(in a terminal; or so I'd like to run it) (`cd C:\Users\USER\x\` or `cd /home/usr/USER/x/`)
and run the main file using `python main.py`.

To (re)load all the commands, you will want to run the `/update` command.
Since this command does not yet exist if you run the bot for the first time,
you will have to put the contents of the function into
`main.py`'s `on_ready()` function: `await itx.client.tree.sync()`.
(I don't have it in there by default, to prevent it unnecessarily updating every time the bot starts up).

## Support

DM MysticMia in the TransPlace server. You may have to pass through a verification system
but the verifiers will surely let you dm me.
Join TransPlace with https://discord.gg/transplace

## Roadmap

There are no real future plans for now.
Whatever I want to add usually gets added within the first week after thinking about it or getting it suggested to me.
Potential long-term issues or ideas can be found in the GitHub Issues tab.

## Contributing

To contribute, you must first be part of the TransPlace Bot Development team.
However, you can still give suggestions for ideas or code
by contacting me (see the Support section) or by using /developer-request in one of the servers with Rina.

## Authors and acknowledgment

Thank you to whoever is keeping up the discord.py framework (and the other installed pip modules)

## License

Feel free to use whatever. Feel free to cite me as source if you want.
Would be cool to have recognition from some random person on the internet :).

## Project status
(last updated 2026-08-15): This project is being somewhat maintained by whichever requests and suggestions I get from people.
