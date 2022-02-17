import json
import re
from pathlib import Path

import yaml
from nbt.region import *
from tqdm import tqdm

from ..util import *

possible_region_folders = ('region', 'DIM-1/region', 'DIM1/region')


def start(world_folders, output_file, output_format, input_data, confirm):
    inhabited_time = None
    if input_data and 'inhabited_time' in input_data:
        print('\nLoading input file data...')
        inhabited_time = input_data['inhabited_time']
        if type(inhabited_time) is not int:
            eprint(f'Inhabited time has to be a number but is "{inhabited_time}".')
            exit(3)
        print(f'Using {inhabited_time} seconds as inhabited time.')

    if not inhabited_time:
        print('\nSelect how long a player may have been in a chunk for it to be deleted in seconds. (Defaults to 0, leave empty for default)')
        while True:
            answer = input('Maximal inhabited time: ')
            if not answer:
                break

            if answer.isnumeric():
                inhabited_time = int(answer)
                if inhabited_time >= 0:
                    break
                else:
                    print('Please state a positive number.')
            else:
                print('Please state a number.')
    inhabited_time = inhabited_time * 20 if inhabited_time else 0

    if not confirm:
        print('\nWarning: This operation will remove all chunks in which no player was present.'
              '\nTherefore, chunks with changed blocks may be removed since players can change blocks even if they are not in the chunk.'
              '\nIt is recommended to make a backup of your world beforehand.'
              '\nNo further confirmation requests will be made before chunks are removed.')
        while True:
            answer = input('Do you want to continue? (y/N): ')
            if not answer or answer.lower() == 'n':
                exit()
            elif answer.lower() != 'y':
                print('Please state "y" or "n".')
            else:
                break

    total_start_time = time.time()
    total_freed_space = 0
    worlds = {}
    for world_folder in world_folders:
        region_folders = [region_folder for region_folder in
                          [Path(world_folder, folder) for folder in possible_region_folders] if region_folder.is_dir()]
        if not region_folders:
            print(f'\nNo region folder was found in world "{world_folder}"')
            continue

        files = list_files(region_folders)
        file_count = len(files)
        size = get_size(files)

        count, total = 0, 0
        start_time = time.time()
        messages = []
        print(f'\nRemoving unused chunks of world "{world_folder}"...')
        with tqdm(total=file_count * 32 * 32 * 2 if file_count > 0 else 1,
                  unit_scale=1 / 32 / 32 / 2,
                  bar_format='{percentage:.2f}% |{bar}| [{n:.0f}/{total:.0f} files]  ') as pbar:

            if file_count <= 0:
                pbar.update(1)

            for region_file in files:
                with region_file.open('r+b') as file:
                    region = RegionFile(fileobj=file)
                    result = re.match('r\\.(-?\\d+)\\.(-?\\d+)\\.mca', region_file.name)
                    if result:
                        region.loc = Location(x=int(result.group(1)), z=int(result.group(2)))

                    chunk_count = region.chunk_count()

                    total += chunk_count
                    pbar.update(32 * 32 * 2 - chunk_count * 2)

                    delete = []
                    for coords in region.get_chunk_coords():
                        x, z, = coords['x'], coords['z']
                        chunk = region.get_chunk(x, z)
                        data = chunk['Level'] if 'Level' in chunk else chunk

                        if 'InhabitedTime' not in data:
                            messages.append(
                                f'Chunk {x} {z} (in world at {chunk.loc.x} {chunk.loc.z}) in the region file "{region_file.name}" could not be read.')
                            continue

                        if data['InhabitedTime'].value <= inhabited_time:
                            delete.append((x, z))
                            pbar.update()
                        else:
                            pbar.update(2)

                    delete_count = len(delete)
                    if delete_count < chunk_count:
                        for chunk in delete:
                            region.unlink_chunk(chunk[0], chunk[1])
                            pbar.update()

                count += delete_count
                if delete_count >= chunk_count:
                    region_file.unlink()
                    pbar.update(delete_count)

        elapsed_time = int(round((time.time() - start_time) * 1000))
        human_readable_elapsed_time = format_time(elapsed_time)

        raw_freed_space = size - get_size(list_files(region_folders))
        freed_space, freed_space_unit = format_freed_space(raw_freed_space)
        human_readable_freed_space = f'{freed_space:.2f}{freed_space_unit}'

        print(
            f'Removed {count}/{total} ({count / total * 100 if total > 0 else 0:0.2f}%) chunks of world "{world_folder}". '
            f'(Elapsed time: {human_readable_elapsed_time}; Freed space: {human_readable_freed_space})')

        for message in messages:
            print(message)

        if output_file:
            total_freed_space += raw_freed_space
            worlds[str(world_folder.resolve())] = {
                'chunks': {
                    'removed': count,
                    'total': total
                },
                'elapsed_time': {
                    'raw': elapsed_time,
                    'human_readable': human_readable_elapsed_time
                },
                'freed_space': {
                    'raw': raw_freed_space,
                    'human_readable': human_readable_freed_space
                }
            }

    elapsed_time = int(round((time.time() - total_start_time) * 1000))
    human_readable_elapsed_time = format_time(elapsed_time)
    freed_space, freed_space_unit = format_freed_space(total_freed_space)
    human_readable_freed_space = f'{freed_space:.2f}{freed_space_unit}'

    if len(world_folders) > 1:
        print(f'\nTotal elapsed time: {human_readable_elapsed_time}'
              f'\nTotal freed space: {human_readable_freed_space}')

    if output_file:
        data = {
            'worlds': worlds,
            'total': {
                'elapsed_time': {
                    'raw': elapsed_time,
                    'human_readable': human_readable_elapsed_time
                },
                'freed_space': {
                    'raw': total_freed_space,
                    'human_readable': human_readable_freed_space
                }
            }
        }

        with Path(output_file).open('w') as file:
            if output_format == 'plain':
                file.write(f'--- MCWorldTools by Rapha149 ---'
                           f'\n\u00B7\u00B7\u00B7 Remove unused chunks \u00B7\u00B7\u00B7'
                           f'\n\nTotal elapsed time: {human_readable_elapsed_time}'
                           f'\nTotal freed space: {human_readable_freed_space}'
                           f'\n\n[ Worlds ]' +
                           ('\n'.join([f'\n{world}'
                                       f'\n    Chunks'
                                       f'\n        Removed: {info["chunks"]["removed"]}'
                                       f'\n        Total: {info["chunks"]["total"]}'
                                       f'\n    Elapsed time: {info["elapsed_time"]["human_readable"]}'
                                       f'\n    Freed space: {info["freed_space"]["human_readable"]}'
                                       for world, info in worlds.items()])))
            elif output_format == 'json':
                json.dump(data, file, indent=3)
            elif output_format == 'yaml':
                yaml.dump(data, file, indent=3)
            print(f'\nSaved output to "{output_file}"')
