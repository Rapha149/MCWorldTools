# MCWorldTools

[![PyPi Version](https://img.shields.io/pypi/v/mcworldtools.svg?style=flat-square)](https://pypi.org/project/mcworldtools/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/mcworldtools.svg?style=flat-square)](https://pypi.org/project/mcworldtools/)
[![GitHub stars](https://img.shields.io/github/stars/Rapha149/MCWorldTools.svg?style=flat-square&logo=github&label=Stars&logoColor=white)](https://github.com/Rapha149/MCWorldTools/)
[![PyPi downloads](https://img.shields.io/pypi/dm/mcworldtools.svg?style=flat-square)](https://pypistats.org/packages/mcworldtools/)

Useful tools for Minecraft worlds such as removing unused chunks and finding blocks, command blocks or entities.  
Tested from `1.7.10` up to `1.18.1`.

## Installation
```pip install mcworldtools```

## Usage
You can simply run the command `mcworldtools` in a Minecraft world folder.  
The script will tell you the name of your Minecraft world and - if possible, it may not be in older versions - the Minecraft version of your world.  
After that you can choose which tool you want to use by stating the number of the tool.

### Further usage
```mcworldtools [-h] [-w WORLD] [-t TOOL] [-o OUTPUT_FILE] [-f {plain,json,yaml}] [--confirm]```

**Arguments:**
- `-h --help` Show the help message and exit
- `-w WORLD, --world WORLD` Use a different world folder than the current working directory. You can provide this option multiple times for multiple words.
- `-t TOOL, --tool TOOL` Choose the tool to use beforehand.
- `-o OUTPUT_FILE, --output-file OUTPUT_FILE` Select a file to write the output statistics to.
- `-f {plain,json,yaml}, --output-format {plain,json,yaml}` The output file format. May be `plain` (default), `json` or `yaml`.
- `--confirm` Automatically confirm any confirmation requests.

### Warning
Do **NOT** use these tools for a world that is currently opened (i.e. in Minecraft Singleplayer or by a Minecraft server).
Doing so may lead to unintended consequences. I do NOT take any responsibility for your Minecraft world if you do that.
