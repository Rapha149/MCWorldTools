import json
import re

import yaml
from nbt.region import *
from tqdm import tqdm

from ..util import *

actions = ['Find command blocks', 'Remove command blocks']
types = ['minecraft:command_block', 'Control']


def start(world_folders, output_file, output_format, input_data, confirm):
    action_count = len(actions)
    action = None
    if input_data and 'action' in input_data:
        print('\nLoading input file data...')
        action = input_data['action']
        if not isinstance(action, int):
            eprint(f'"action" has to be a number but is {type(action).__name__}')
            exit(3)
        if action < 1 or action > action_count:
            eprint(f'"action" has to be one of {", ".join(str(i) for i in range(1, len(actions) + 1))}')
            exit(3)
        print(f'Using action "{actions[action - 1]}"')

    if not action:
        print('\nChoose what you want to do.')
        for i in range(action_count):
            print(f'{i + 1}. {actions[i]}')

        while True:
            answer = input(f'Select an action (1-{action_count}): ')
            if not answer.isnumeric():
                print('Please state a number.')
                continue

            action = int(answer)
            if action < 1 or action > action_count:
                print(f'Please state a number between 1 and {action_count}.')
                continue
            break
        print(f'Using action "{actions[action - 1]}"')

    if action == 1:
        find(world_folders, output_file, output_format, input_data)
    elif action == 2:
        remove(world_folders, output_file, output_format, input_data, confirm)


def find(world_folders, output_file, output_format, input_data):
    if not output_file:
        print(f'\nFor this action you have to state an output file as command argument (-o).')
        exit(4)

    limit_to_dimension, limit_dimension, only_executing = None, None, None
    if input_data:
        print('\nLoading more input file data...')
        if 'only_executing' in input_data:
            only_executing = input_data['only_executing']
            if not isinstance(only_executing, bool):
                eprint(f'"only_executing" has to be bool (true/false) but is {type(only_executing).__name__}')
                exit(3)
            print(f'The script will {"" if only_executing else "not"} only look for executing command blocks.')

        if 'dimension' in input_data:
            limit_dimension = input_data['dimension']
            if limit_dimension is None:
                limit_to_dimension = False
                print(f'Not limiting to one dimension.')
            else:
                if not isinstance(limit_dimension, str):
                    eprint(f'"dimension" has to be text but is {type(limit_dimension).__name__}')
                    exit(3)
                limit_to_dimension = True
                limit_dimension = limit_dimension.lower()
                if limit_dimension not in dimensions:
                    eprint(f'Unknown dimension "{limit_dimension}"')
                    exit(3)
                print(f'Limiting to dimension "{limit_dimension}"')

    if only_executing is None:
        print('\nDo you want to only search for executing command blocks? (i.e. either powered or auto)'
              '\nOnly supported in 1.9+')
        only_executing = parse_yes_no(input('Only search for executing command blocks? (y/N): '), default=False)

    if limit_to_dimension is None:
        dimensions_str = '"' + '", "'.join(dimensions) + '"'
        print('\nChoose a dimension where entities should be searched. Enter nothing for all dimensions.'
              f'\nIt can be one of {dimensions_str}')
        complete(dimensions, case_insensitive=True)
        while True:
            answer = input('Dimension: ')
            if not answer:
                limit_to_dimension = False
                break
            else:
                answer = answer.strip().lower()
                if answer not in dimensions:
                    print('Unknown dimension.')
                    continue
                limit_to_dimension = True
                limit_dimension = answer
                break
        complete([])

    total_start_time = time.time()
    total_command_blocks = 0
    worlds = {}
    for world_folder in world_folders:
        region_folders = get_region_folders(world_folder)
        if not region_folders:
            print(f'\nNo region folder was found in world "{world_folder}"')
            continue

        files = map_files(region_folders)
        file_count = len(get_all_files(files))

        command_blocks = []
        start_time = time.time()
        messages = []
        print(f'\nSearching for command blocks in world "{world_folder}"...')
        with tqdm(total=file_count * 32 * 32 if file_count > 0 else 1,
                  unit_scale=1 / 32 / 32,
                  bar_format='{percentage:.2f}% |{bar}| [{n:.0f}/{total:.0f} files]  ') as pbar:

            if file_count <= 0:
                pbar.update()

            for dimension in dimensions:
                if dimension not in files:
                    continue

                region_files = files[dimension]
                if limit_to_dimension and dimension != limit_dimension:
                    pbar.update(32 * 32 * len(region_files))
                    continue

                for region_file in region_files:
                    with region_file.open('rb') as file:
                        region = RegionFile(fileobj=file)
                        match = re.match('r\\.(-?\\d+)\\.(-?\\d+)\\.mca', region_file.name)
                        if match:
                            region.loc = Location(x=int(match.group(1)), z=int(match.group(2)))

                        pbar.update(32 * 32 - region.chunk_count())
                        for coords in region.get_chunk_coords():
                            x, z = coords['x'], coords['z']
                            chunk = region.get_chunk(x, z)
                            world_x, world_z = chunk.loc.x, chunk.loc.z
                            data = chunk['Level'] if 'Level' in chunk else chunk

                            if 'block_entities' in data:
                                block_entities = data['block_entities']
                            elif 'TileEntities' in data:
                                block_entities = data['TileEntities']
                            else:
                                messages.append(f'Chunk {x} {z} (in world at {world_x} {world_z}) in the region file "'
                                                f'{region_file}" could not be read.')
                                continue

                            for command_block in block_entities:
                                if command_block['id'].value not in types:
                                    continue
                                powered = (True if command_block['powered'].value == 1 else False) \
                                    if 'powered' in command_block else None
                                auto = (True if command_block['auto'].value == 1 else False) \
                                    if 'auto' in command_block else None
                                if only_executing and not powered and not auto:
                                    continue
                                command_blocks.append({
                                    'custom_name': command_block['CustomName'].value,
                                    'loc': {
                                        'dimension': dimension,
                                        'x': command_block['x'].value,
                                        'y': command_block['y'].value,
                                        'z': command_block['z'].value
                                    },
                                    'chunk': {
                                        'in_region_file': {
                                            'x': coords['x'],
                                            'z': coords['z']
                                        },
                                        'in_world': {
                                            'x': world_x,
                                            'z': world_z
                                        }
                                    },
                                    'powered': powered,
                                    'auto': auto,
                                    'command': command_block['Command'].value
                                })

                            pbar.update()

        elapsed_time = int(round((time.time() - start_time) * 1000))
        human_readable_elapsed_time = format_time(elapsed_time)

        command_block_count = len(command_blocks)
        print(f'Found {command_block_count} command blocks in world "{world_folder}". (Elapsed time: '
              f'{human_readable_elapsed_time})')

        for message in messages:
            print(message)

        total_command_blocks += command_block_count
        if output_file:
            worlds[str(world_folder.resolve())] = {
                'command_blocks': command_blocks,
                'elapsed_time': {
                    'raw': elapsed_time,
                    'human_readable': human_readable_elapsed_time
                }
            }

    elapsed_time = int(round((time.time() - total_start_time) * 1000))
    human_readable_elapsed_time = format_time(elapsed_time)

    if len(world_folders) > 1:
        print(f'\nTotal found command blocks: {total_command_blocks}'
              f'\nTotal elapsed time: {human_readable_elapsed_time}')

    if output_file:
        data = {
            'worlds': worlds,
            'total': {
                'total_command_blocks': total_command_blocks,
                'elapsed_time': {
                    'raw': elapsed_time,
                    'human_readable': human_readable_elapsed_time
                }
            }
        }

        with Path(output_file).open('w') as file:
            if output_format == 'plain':
                file.write(f'--- MCWorldTools by Rapha149 ---'
                           f'\n\u00B7\u00B7\u00B7 Find command blocks \u00B7\u00B7\u00B7'
                           f'\n\nTotal found command blocks: {total_command_blocks}'
                           f'\nTotal elapsed time: {human_readable_elapsed_time}'
                           f'\n\n[ Worlds ]')
                for world, info in worlds.items():
                    command_blocks = info['command_blocks']
                    command_block_count = len(command_blocks)
                    file.write(f'\n{world}'
                               f'\n    Command blocks found: {command_block_count}'
                               f'\n    Elapsed time: {info["elapsed_time"]["human_readable"]}')
                    if command_blocks:
                        file.write('\n    Command blocks:')
                        for i in range(command_block_count):
                            if i > 0:
                                file.write('\n        ------------------')

                            command_block = command_blocks[i]
                            loc, chunk = command_block['loc'], command_block['chunk']
                            powered, auto = command_block['powered'], command_block['auto']
                            # noinspection PyUnresolvedReferences
                            file.write(f'\n        Custom Name: {command_block["custom_name"]}'
                                       f'\n        Dimension: {loc["dimension"].capitalize()}'
                                       f'\n        Location: {loc["x"]} {loc["y"]} {loc["z"]}'
                                       f'\n        Chunk:'
                                       f'\n            In region file: {chunk["in_region_file"]["x"]} '
                                       f'{chunk["in_region_file"]["z"]}'
                                       f'\n            In world: {chunk["in_world"]["x"]} {chunk["in_world"]["z"]}'
                                       f'\n        Command: {command_block["command"]}'
                                       f'\n        Powered: '
                                       f'{("Yes" if powered else "No") if powered is not None else "Unknown"}'
                                       f'\n        Auto: '
                                       f'{("Yes" if auto else "No") if auto is not None else "Unknown"}')
                    file.write('\n')

            elif output_format == 'json':
                json.dump(data, file, indent=3)
            elif output_format == 'yaml':
                yaml.dump(data, file, indent=3)

            print(f'\nSaved output to "{output_file}"')


def remove(world_folders, output_file, output_format, input_data, confirm):
    locations = None
    if input_data and 'locations' in input_data:
        print('\nLoading more input data...')
        loc_list = input_data['locations']
        if not isinstance(loc_list, list):
            eprint(f'"locations" has to be a list but is {type(loc_list).__name__}')
            exit(3)

        locations = []
        for i in range(len(loc_list)):
            loc = loc_list[i]
            if not isinstance(loc, dict):
                eprint(f'{i + 1}. item in "locations" has to contain keys but is {type(loc).__name__}')
                exit(3)

            for key in ('x', 'y', 'z'):
                if key not in loc:
                    eprint(f'"{key}" is not in {i + 1}. item of "locations"')
                    exit(3)
                value = loc[key]
                if not isinstance(value, int):
                    eprint(
                        f'"{key}" in {i + 1}. item of "locations" has to be a number but is '
                        f'{type(value).__name__}')
                    exit(3)
            if 'dimension' not in loc:
                eprint(f'"dimension" is not in {i + 1}. item of "locations"')
                exit(3)
            dimension = loc['dimension']
            if not isinstance(dimension, str):
                eprint(f'"dimension" in {i + 1}. item of "locations" has to be text but is {type(dimension).__name__}')
                exit(3)
            dimension = dimension.lower()
            if dimension not in dimensions:
                eprint(f'Unknown dimension "{dimension}" in {i + 1}. item of "locations"')
                exit(3)

            locations.append({
                'dimension': dimension,
                'x': loc['x'],
                'y': loc['y'],
                'z': loc['z']
            })

        location_count = len(locations)
        print(f'Using {location_count} location{"s" if location_count != 1 else ""} to look for.')

    if not locations:
        dimensions_str = '"' + '", "'.join(dimensions) + '"'
        print('\nChoose locations where command blocks should be removed. Enter nothing once your finished.'
              '\nUse the following format for locations: "DIMENSION: X Y Z" (e.g. "overworld: 12 71 8";'
              f' dimension can be one of {dimensions_str})')

        locations = []
        while True:
            answer = input(f'{len(locations) + 1}. Location: ')
            if not answer:
                if locations:
                    break
                else:
                    print('State at least 1 location.')
                    continue

            match = re.match('(\\w+): (-?\\d+) (-?\\d+) (-?\\d+)', answer)
            if not match:
                print('Invalid location.')
                continue

            dimension = match.group(1).lower()
            if dimension not in dimensions:
                print('Unknown dimension.')
                continue

            locations.append({
                'dimension': dimension,
                'x': int(match.group(2)),
                'y': int(match.group(3)),
                'z': int(match.group(4))
            })
    used_dimensions = [loc['dimension'] for loc in locations]

    if not confirm:
        print('\nWarning: This operation will remove the command blocks at the given locations permanently.'
              '\nIt is recommended to make a backup of your world beforehand.')
        if len(world_folders) > 1:
            print('This action is NOT recommended for use in multiple worlds at the same time.')
        print('No further confirmation requests will be made before command blocks are removed.')
        while True:
            answer = parse_yes_no(input('Do you want to continue? (y/N): '), default=False)
            if answer is not None:
                if not answer:
                    exit()
                break

    total_start_time = time.time()
    total_command_blocks = 0
    worlds = {}
    for world_folder in world_folders:
        region_folders = get_region_folders(world_folder)
        if not region_folders:
            print(f'\nNo region folder was found in world "{world_folder}"')
            continue

        files = map_files(region_folders)
        file_count = len(get_all_files(files))

        start_time = time.time()
        command_blocks = []
        messages = []
        print(f'\nRemoving command blocks in world "{world_folder}"...')
        with tqdm(total=file_count * 32 * 32 if file_count > 0 else 1,
                  unit_scale=1 / 32 / 32,
                  bar_format='{percentage:.2f}% |{bar}| [{n:.0f}/{total:.0f} files]  ') as pbar:

            if file_count <= 0:
                pbar.update()

            for dimension, region_files in files.items():
                if dimension not in used_dimensions:
                    pbar.update(32 * 32 * len(region_files))
                    continue

                for region_file in region_files:
                    with region_file.open('r+b') as file:
                        region = RegionFile(fileobj=file)
                        match = re.match('r\\.(-?\\d+)\\.(-?\\d+)\\.mca', region_file.name)
                        if match:
                            region.loc = Location(x=int(match.group(1)), z=int(match.group(2)))

                        pbar.update(32 * 32 - region.chunk_count())
                        for coords in region.get_chunk_coords():
                            x, z = coords['x'], coords['z']
                            chunk = region.get_chunk(x, z)
                            world_x, world_z = chunk.loc.x, chunk.loc.z
                            data = chunk['Level'] if 'Level' in chunk else chunk

                            if 'block_entities' in data:
                                block_entities = data['block_entities']
                            elif 'TileEntities' in data:
                                block_entities = data['TileEntities']
                            else:
                                messages.append(f'Chunk {x} {z} (in world at {world_x} {world_z}) in the region file "'
                                                f'{region_file}" could not be read.')
                                continue

                            to_remove = []
                            for i in range(len(block_entities)):
                                command_block = block_entities[i]
                                if command_block['id'].value not in types:
                                    continue
                                block_x = command_block['x'].value
                                block_y = command_block['y'].value
                                block_z = command_block['z'].value
                                loc = {
                                    'dimension': dimension,
                                    'x': block_x,
                                    'y': block_y,
                                    'z': block_z
                                }

                                if loc in locations:
                                    command_blocks.append(loc)
                                    to_remove.append(i)

                            if to_remove:
                                for i in reversed(to_remove):
                                    del block_entities[i]
                                region.write_chunk(x, z, chunk)

                            pbar.update()

        elapsed_time = int(round((time.time() - start_time) * 1000))
        human_readable_elapsed_time = format_time(elapsed_time)

        command_block_count = len(command_blocks)
        print(f'Removed {command_block_count} command blocks in world "{world_folder}". (Elapsed time: '
              f'{human_readable_elapsed_time})')

        for message in messages:
            print(message)

        locations_without_command_block = []
        for loc in locations:
            if loc not in command_blocks:
                locations_without_command_block.append(loc.copy())
                print(f'There is no command block at the location "{loc["dimension"].capitalize()}: {loc["x"]} '
                      f'{loc["y"]} {loc["z"]}"')

        total_command_blocks += command_block_count
        if output_file:
            worlds[str(world_folder.resolve())] = {
                'removed_command_blocks': command_block_count,
                'locations_without_command_block': locations_without_command_block,
                'elapsed_time': {
                    'raw': elapsed_time,
                    'human_readable': human_readable_elapsed_time
                }
            }

    elapsed_time = int(round((time.time() - total_start_time) * 1000))
    human_readable_elapsed_time = format_time(elapsed_time)

    if len(world_folders) > 1:
        print(f'\nTotal removed command blocks: {total_command_blocks}'
              f'\nTotal elapsed time: {human_readable_elapsed_time}')

    if output_file:
        data = {
            'worlds': worlds,
            'total': {
                'total_removed_command_blocks': total_command_blocks,
                'elapsed_time': {
                    'raw': elapsed_time,
                    'human_readable': human_readable_elapsed_time
                }
            }
        }

        with Path(output_file).open('w') as file:
            if output_format == 'plain':
                file.write(f'--- MCWorldTools by Rapha149 ---'
                           f'\n\u00B7\u00B7\u00B7 Remove command blocks \u00B7\u00B7\u00B7'
                           f'\n\nTotal removed command blocks: {total_command_blocks}'
                           f'\nTotal elapsed time: {human_readable_elapsed_time}'
                           f'\n\n[ Worlds ]')
                for world, info in worlds.items():
                    locations_without_command_block = info["locations_without_command_block"]
                    file.write(f'\n{world}'
                               f'\n    Removed command blocks: {info["removed_command_blocks"]}'
                               f'\n    Locations without command blocks:')
                    if locations_without_command_block:
                        for i in range(len(locations_without_command_block)):
                            if i > 0:
                                file.write('\n        ------------------')

                            loc = locations_without_command_block[i]
                            file.write(f'\n        Dimension: {loc["dimension"].capitalize()}'
                                       f'\n        Location: {loc["x"]} {loc["y"]} {loc["z"]}')
                    else:
                        file.write(' ---')
                    file.write(f'\n    Elapsed time: {info["elapsed_time"]["human_readable"]}\n')

            elif output_format == 'json':
                json.dump(data, file, indent=3)
            elif output_format == 'yaml':
                yaml.dump(data, file, indent=3)

            print(f'\nSaved output to "{output_file}"')
