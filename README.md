# Splatlogger
A PID/PNID grabber and match logger for Splatoon using TCPGecko, written in Python.

## Prerequisites
You'll need a modded Wii U running either the Tiramisu or Aroma environment, as well as Python 3.11 or newer installed on your system (on Android devices you can use Termux).

On Tiramisu, use [TCPGecko](https://github.com/BullyWiiPlaza/tcpgecko) (Geckiine or SDGeckiine will work as well).

On Aroma, install the [TCPGecko Aroma plugin](https://github.com/spoongaming61/TCPGeckoAroma).

## Installation
Install the package from PyPI:
```
python -m pip install Splatlogger
```

Or download and install the latest release from GitHub:
```
python -m pip install /path/to/Splatlogger-1.x.zip
```

Alternatively, you can skip the installation and instead run the module directly from the source code.

## Usage
Run Splatlogger with:
```
python -m splatlogger -ip IP [options]
```
where `IP` is your Wii U's LAN IP address
(if you have your scripts directory in your PATH, you can also run `splatlogger -ip IP [options]`).

Options:
- `-log-level [option]` - Set how much data should be logged.
  - `none` - Don't create a log file (default).
  - `basic` - Log only basic player information (name, PID, PNID, region).
  - `full` - Log all player information (basic + team, level, rank, appearance, gear, weapons).
  - `stats` - Log all player information and player stats (points, kills, deaths). Requires the match to end to finish logging.

- `-auto [option]` - Enable auto logging. When enabled will automatically log every match you play (log level must be at least `basic`).
  - `all` - Save a log of all matches you play (default).
  - `latest` - Save a log of only the latest match

- `-aroma` - Enable Aroma mode.

- `-silent` - Disable printing logs to the console.

Logs are saved in `/[User]/Documents/Splatlogger/logs/[Date]`.

To always run with the same IP and options, create an `args.txt` file in `/[User]/Documents/Splatlogger` and put all the arguments in there.
Afterward run without any arguments.

Only one program can be connected to TCPGecko at a time. If you have something else connected, disconnect it beforehand.

## Credits
- [pyGecko](https://github.com/wiiudev/pyGecko) authors for most of `tcpgecko.py`.

- Everyone who contributed to [PNIDGrab](https://github.com/JerrySM64/PNIDGrab) and other similar PID grabbers as those were used as a reference.
