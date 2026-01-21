# Splatlogger
CLI Python program for logging the info of players you've played with in Splatoon matches using TCPGecko.

## Usage

You'll need a modded Wii U running either [TCPGecko](https://github.com/BullyWiiPlaza/tcpgecko) (Geckiine or SDGeckiine will work as well) or the [TCPGecko Aroma plugin](https://github.com/spoongaming61/TCPGeckoAroma), as well as Python 3.11 or newer installed on your system.

Run `python /path/to/Splatlogger/main.py IP [options]` where `IP` is your Wii U's LAN IP address.

Options:

* ```log``` - Write full match log to file.

* ```silent``` - Don't print logs to the console.

* ```stats``` - Enable logging of player stats (points, kills, deaths, win/loss). Requires the match to complete to finish logging, also makes logging slower.

* ```auto``` - Enable auto logging. When enabled will automatically log every match you play.

* ```auto-latest``` - Same as above but will save only the latest match you played.

* ```aroma``` - Enable Aroma mode.

Running with just the IP address will print player PIDs, PNIDs and names to the console without logging.

Only one program can be connected to TCPGecko at a time. If you have something else connected, disconnect it before running Splatlogger.

## Credits
[pyGecko](https://github.com/wiiudev/pyGecko) authors - tcpgecko.py

Everyone who contributed to [PNIDGrab](https://github.com/JerrySM64/PNIDGrab) and other similar PID grabbers as this is partly based on those.
