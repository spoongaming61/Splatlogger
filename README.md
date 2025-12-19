# Splatlogger
Python tool for logging the info of players you've played with in Splatoon matches using TCPGecko.

To use run ```python /Splatlogger/main.py x.x.x.x args``` where "x.x.x.x" is your Wii U's LAN IP address and "args" are any additional arguments.

Running without any arguments will simply print basic player information to the console.

Additional arguments:

* ```log``` - Write full match log to file.

* ```silent``` - Enable silent logging (don't print logs to console).

* ```stats``` - Enable logging of player stats (points, kills, deaths, win/loss). Requires the match to complete to finish logging, also makes logging slower.

* ```auto``` - Enable auto logging. When enabled will automatically log every match you play.

Notes:

* Only Python 3.11 and newer has been tested.

* This will likely only work with regular TCPGecko as I did not account for different memory offsets.

* Only one program can be connected to TCPGecko at a time.

## Credits
[pyGecko](https://github.com/wiiudev/pyGecko) authors - tcpgecko.py and common.py

Everyone who contributed to [PNIDGrab](https://github.com/JerrySM64/PNIDGrab) and other similar PID grabbing tools as this is partly based on those.
