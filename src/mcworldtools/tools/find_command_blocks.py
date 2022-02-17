import json
import yaml
from pathlib import Path

from nbt.region import *
from tqdm import tqdm
from ..util import *

old_type = 'Control'
known_types = {
    'normal': 'command_block',
    'repeating': 'repeating_command_block',
    'chain': 'chain_command_block'
}


def start(world_folders, output_file, output_format, input_data, confirm):
    types, only_powered, loc = None, None, None
    if input_data:
        print('\nLoading input file data...')
        if 'types' in input_data:
            types = input_data['types']
            if type(types) is not list:
                eprint(f'"types" has to be a list but is {type(types).__name__}')
                exit(3)
            if not types:
                eprint('You have to specify at least one type.')
                exit(3)
            for t in types:
                if t not in known_types:
                    eprint(f'Unknown type "{t}"')
                    exit(3)

        if 'only_powered' in input_data:
            only_powered = input_data['only_powered']
            if type(only_powered) is not bool:
                eprint(f'"only_powered" has to be bool (true/false) but is {type(only_powered).__name__}')
                exit(3)

        if 'loc' in input_data:
            location = input_data['loc']
            if type(location) is not dict:
                eprint(f'"loc" has to contain keys but is {type(location).__name__}')
                exit(3)
            values = {}
            for key in ('x', 'y', 'z'):
                if key not in location:
                    eprint(f'"{key}" is not in "loc"')
                    exit(3)
                value = location[key]
                if type(value) is not int:
                    eprint(f'"{key}" in "loc" has to be a number but is {type(value).__name__}')
                    exit(3)
                values[key] = value
            loc = Location(x=values['x'], y=values['y'], z=values['z'])

    if not types:
        print('\nChoose the command block types to look for. Seperate by commas or leave empty for all.'
              '\nOnly supported in 1.11+')
        while True:
            answer = input('Command block types: ')
            if answer:
                stated_types = [stated_type.strip() for stated_type in answer.split(',')]
                for stated_type in stated_types:
                    if stated_type not in known_types:
                        print(f'Unknown type: "{stated_type}"')
                        continue
                types = stated_types
            break

    if not only_powered:
        print('\nDo you want to only look for powered command blocks? Only supported in 1.9+')
        while True:
            answer = parse_yes_no(input('Only look for powered command blocks? (y/N): '), default=False)
