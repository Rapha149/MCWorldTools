import json
import signal
from argparse import ArgumentParser
from json import JSONDecodeError
from pathlib import Path

from nbt.nbt import *

from .util import *
from .tools import remove_unused_chunks, find_blocks, find_command_blocks, find_entities

available_tools = ('Remove unused chunks', 'Remove/Find blocks', 'Remove/Find command blocks', 'Remove/Find entities')


def sigint_handler():
    print("\n\nAborted.")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, lambda s, frame: sigint_handler())

    parser = ArgumentParser(prog='mcworldtools',
                            description='MCWorldTools by Rapha149',
                            allow_abbrev=False)
    parser.add_argument('-w', '--world', action='append',
                        help='Use a different world folder than the current working directory.'
                             '\nYou can provide this option multiple times for multiple words')
    parser.add_argument('-t', '--tool', type=int, choices=range(1, len(available_tools) + 1),
                        help='Choose the tool you want to use beforehand')
    parser.add_argument('-o', '--output_file', help='Select a file to write the output statistics to.'
                                                    '\nThis option is mandatory when using tools that search for something.')
    parser.add_argument('-f', '--output-format', choices=['plain', 'json', 'yaml'], default='plain',
                        help='The output file format. May be "plain" (default), "json" or "yaml"')
    parser.add_argument('-i', '--input-file', help='Select a file to read input values from.'
                                                   '\nSee the Github page for more information: https://github.com/Rapha149/MCWorldTools#input-files')
    parser.add_argument('--confirm', action='store_true', help='Automatically confirm any confirmation requests')
    args = parser.parse_args()

    if not args.world:
        world_folders = [Path.cwd()]
    else:
        world_folders, absolute_folders = [], []
        for world in args.world:
            world_folder = Path(world)
            if not world_folder.is_dir():
                eprint(f'The folder "{world_folder}" does not exist.')
                exit(1)

            absolute_folder = world_folder.resolve()
            if absolute_folder in absolute_folders:
                eprint(f'The folder "{world_folder}" was stated multiple times.')
                exit(1)
            world_folders.append(world_folder)
            absolute_folders.append(absolute_folder)

    for world_folder in world_folders:
        level_dat = Path(world_folder, 'level.dat')
        if not level_dat.is_file():
            if args.world:
                eprint(f'"{world_folder}" is not a world folder.')
            else:
                eprint('Please run in a world folder or use the option "--world".')
            exit(2)

        level = NBTFile(fileobj=level_dat.open('rb'))
        try:
            data = level['Data']
            version = f'Version: {data["Version"]["Name"]}, ' if 'Version' in data else ''
            print(f'Detected world: "{data["LevelName"]}" ({version}World folder: "{world_folder}")')
        except KeyError:
            eprint(f'"{world_folder}" is not a valid world folder.')
            exit(2)

    output_file = None
    if args.output_file:
        output_file = Path(args.output_file)
        if output_file.is_dir():
            eprint(f'The output file "{output_file}" is a folder.')
            exit(1)

    input_data = None
    if args.input_file:
        input_file = Path(args.input_file)
        if not input_file.is_file():
            eprint(f'The input file "{input_file}" does not exist or is a folder.')
            exit(1)
        with input_file.open('r') as file:
            try:
                input_data = json.load(file)
            except JSONDecodeError:
                eprint(f'The input file "{input_file}" does not have valid json content.')
                exit(1)

    print()
    tool = args.tool
    if not tool:
        print('Select which tool you want to use.'
              '\n1. Remove unused chunks'
              '\n2. Find blocks'
              '\n3. Find command blocks'
              '\n4. Find entities'
              '\nc. Cancel')

        while True:
            answer = input('Select a tool (1-4, c): ')
            if answer == 'c':
                print('Exiting')
                exit()

            if not answer.isnumeric():
                print('Please state a number.')
                continue

            tool = int(answer)
            if tool < 1 or tool > 4:
                print('Please state a number between 1 and 4.')
                continue
            break
    print(f'Using tool "{available_tools[tool - 1]}"')

    if tool == 1:
        remove_unused_chunks.start(world_folders, output_file, args.output_format, input_data, args.confirm)
    elif tool == 2:
        find_blocks.start(world_folders, output_file, args.output_format, input_data, args.confirm)
    elif tool == 3:
        find_command_blocks.start(world_folders, output_file, args.output_format, input_data, args.confirm)
    elif tool == 4:
        find_entities.start(world_folders, output_file, args.output_format, input_data, args.confirm)


if __name__ == '__main__':
    main()
