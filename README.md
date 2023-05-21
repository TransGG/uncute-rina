# Uncute Rina

TransPlace's somewhat random bot with a lot of interesting and funky additions for the server.
It is also in the Transonance server.

I've recently (2023-01-18) decided to update the readme to actually tell you how to use this program lol.

## Installation

- Copy the GitHub (basically: download all the files)
- Install python 3.11.3 (or newer, maybe) (https://www.python.org/downloads/)

Also run the following commands to install the modules of the most recent discord.py version (v2.0) and pymongo for the online database

You will need a mongo database to use this bot. For more info, look at https://mongodb.com/

[//]: # (- pip install -U git+https://github.com/Rapptz/discord.py/)
[//]: # (i likely won't be using the latest version anymore: only the stables)
- `pip install discord pymongo motor pandas apscheduler matplotlib requests`

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

Direct yourself to the right directory/folder (in a terminal; or so I'd like to run it) (cd C:\Users\USER\x\) and run the main file using `py Uncute-Rina.py`

## Support

DM MysticMia in the server

## Roadmap

There are no real future plans for now. Whatever I want to add usually gets added within the first week after thinking about it or getting it suggested to me. Potential long-term issues or ideas can be found in the GitHub Issues tab.

## Contributing

It is not possible to contribute with writing the code. You can give suggestions for ideas or code by contacting me though, or using /developer-request in one of the servers with Rina. That might work.

## Authors and acknowledgment
Thank you to whoever is keeping up the discord.py framework (and the other installed pip modules)

## License
Feel free to use whatever. Feel free to cite me as source if you want. Would be cool to have recognition from some random person on the internet.

## Project status
(last updated 2023-05-22): This project is being somewhat maintained by whichever requests and suggestions I get from people.
