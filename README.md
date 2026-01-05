# Splatlogger
CLI Python program for logging the info of players you've played with in Splatoon matches using TCPGecko.

To use run ```python /path/to/Splatlogger/main.py x.x.x.x args``` where "x.x.x.x" is your Wii U's LAN IP address and "args" are any additional arguments.

Running with just the IP address will print player PIDs, PNIDs and names to the console without logging.

Additional arguments:

* ```log``` - Write full match log to file.

* ```silent``` - Enable silent logging (don't print logs to console).

* ```stats``` - Enable logging of player stats (points, kills, deaths, win/loss). Requires the match to complete to finish logging, also makes logging slower.

* ```auto``` - Enable auto logging. When enabled will automatically log every match you play.

* ```auto-latest``` - Same as above but will save only the latest match you played.

* ```aroma``` - Enable aroma mode. Compatible with [TCPGeckoAroma](https://github.com/Teotia444/TCPGeckoAroma).

Notes:

* Only Python 3.11 and newer has been tested.

* Only one program can be connected to TCPGecko at a time.

* Aroma support hasn't been thoroughly tested yet and should be considered experimental.

## Credits
[pyGecko](https://github.com/wiiudev/pyGecko) authors - tcpgecko.py

Everyone who contributed to [PNIDGrab](https://github.com/JerrySM64/PNIDGrab) and other similar PID grabbers as this is partly based on those.
