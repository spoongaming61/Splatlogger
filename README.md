# Splatlogger
A PID/PNID grabber and match logger for Splatoon using TCPGecko.

## Usage
You'll need a modded Wii U running either [TCPGecko](https://github.com/BullyWiiPlaza/tcpgecko) (Geckiine or SDGeckiine will work as well) or the [TCPGecko Aroma plugin](https://github.com/spoongaming61/TCPGeckoAroma), as well as Python 3.11 or newer installed on your system.

Download the latest release and install it. `python -m pip install path/to/Splatlogger-1.x.zip`

Then run `splatlogger -ip IP [options]` where `IP` is your Wii U's LAN IP address.

Options:
- `-log-level [option]` - Set how much data should be logged.
  - `none` - Don't create a log file (default).
  - `basic` - Log only basic player information (name, PID, PNID, region).
  - `full` - Log all player information (basic + team, level, rank, appearance, gear, weapons).
  - `stats` - Log all player information and player stats (points, kills, deaths).

- `-auto [option]` - Enable auto logging. When enabled will automatically log every match you play (log level must be at least `basic`).
  - `all` - Save a log of all matches you play (default).
  - `latest` - Save a log of only the latest match

- `-aroma` - Enable Aroma mode.

- `-silent` - Disable printing logs to the console.

Logs are saved within your documents folder in `Splatlogger/logs/[date]`.

To always run with the same IP and options, create an `args.txt` file in the Splatlogger directory and put all the arguments in there.
Afterward run `splatlogger` without any arguments.

Only one program can be connected to TCPGecko at a time. If you have something else connected, disconnect it before running Splatlogger.

## Credits
[pyGecko](https://github.com/wiiudev/pyGecko) authors - tcpgecko.py

Everyone who contributed to [PNIDGrab](https://github.com/JerrySM64/PNIDGrab) and other similar PID grabbers as this is partly based on those.
