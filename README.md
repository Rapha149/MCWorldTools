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

### Warning
Do **NOT** use these tools for a world that is currently opened (i.e. in Minecraft Singleplayer or by a Minecraft server).
Doing so may lead to unintended consequences. I do NOT take any responsibility for your Minecraft world if you do that.

### Further usage
```mcworldtools [-h] [-w WORLD] [-t TOOL] [-o OUTPUT_FILE] [-f {plain,json,yaml}] [--confirm]```

### Arguments
- `-h --help` Show the help message and exit.
- `-v --version` Show the installed version and exit.
- `-w WORLD, --world WORLD` Use a different world folder than the current working directory. You can provide this option multiple times for multiple words.
- `-t TOOL, --tool TOOL` Choose the tool to use beforehand.
- `-o OUTPUT_FILE, --output-file OUTPUT_FILE` Select a file to write the output statistics to. This option is mandatory when searching for something.
- `-f {plain,json,yaml}, --output-format {plain,json,yaml}` The output file format. May be `plain` (default), `json` or `yaml`.
- `-i INPUT_FILE, --input-file INPUT_FILE` Select a file to read input values from. See [below](#input-files) for more information.
- `--confirm` Automatically confirm any confirmation requests.

### Dimension notes
You can state dimensions in input files or when you are asked for locations when removing blocks or command blocks.  
Dimensions will be returned when finding blocks, command blocks or entities.  
A dimension may be one of `overworld`, `nether` or `end`.
Please note that when using this tool on server worlds where nether and end are in seperate folders (`world_nether` and `world_the_end`) and you are executing the script on one of these, the dimension will be `overworld` because there is no way of detecting to which dimension the world folder is belonging.  
The dimensions `nether` and `end` will only be used if the nether and end files are in a folder named `WORLD_FOLDER/DIM-1` (nether) or `WORLD_FOLDER/DIM1` (end).

### Input files
The content of the input files stated in the command have to be in valid json format.  
You don't have to specify anything in the input file, but you won't get asked for something that you specified. That is useful for automated tasks.

Here is what you can change with these input files:

#### Remove unused chunks
```json
{
  "inhabited_time": 0
}
```
- `inhabited_time` - The time for how long a player may have been in a chunk for it to be deleted (in seconds). Defaults to 0.

#### Find/remove command blocks
```json
{
  "action": 1,
  "only_executing": false
}
```
```json
{
  "action": 2,
  "locations": [
    {
      "dimension": "overworld",
      "x": 3,
      "y": 72,
      "z": 6
    },
    {
      "dimension": "nether",
      "x": 5,
      "y": 129,
      "z": 200
    }
  ]
}
```
- `action` - `1` for finding command blocks and `2` for removing command blocks.
- `only_executing` - Only used when finding command blocks. If enabled, only command blocks that are either powered or in automatic mode will be found.
- `locations` - Only used when removing command blocks. A list of locations where command blocks should be removed. For `dimension` see the [dimension notes](#dimension-notes).
