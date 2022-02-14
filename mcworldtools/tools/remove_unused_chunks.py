import json
import yaml
from pathlib import Path

from nbt.region import *
from tqdm import tqdm

possible_region_folders = ('region', 'DIM-1/region', 'DIM1/region')


def list_files(folders):
    files = []
    for folder in folders:
        for file in folder.iterdir():
            if file.is_file() and file.name.endswith('.mca'):
                files.append(file)
    return files


def get_size(files):
    return sum(file.stat().st_size for file in files)


def format_time(input_time):
    seconds = int(input_time / 1000)
    minutes = int(seconds / 60)
    seconds %= 60
    return f'{minutes}m {seconds}s'


def format_freed_space(raw_freed_space):
    freed_space_unit = 'kB'
    freed_space = raw_freed_space / 1000
    if freed_space >= 1000:
        freed_space /= 1000
        freed_space_unit = 'MB'
    if freed_space >= 1000:
        freed_space /= 1000
        freed_space_unit = 'GB'
    return freed_space, freed_space_unit


def start(world_folders, output_file, output_format, confirm):
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
        world = world_folder.name
        region_folders = [region_folder for region_folder in
                          [Path(world_folder, folder) for folder in possible_region_folders] if region_folder.is_dir()]
        if not region_folders:
            print(f'\nNo region folder was found in world "{world}"')
            continue

        files = list_files(region_folders)
        size = get_size(files)

        count, total = 0, 0
        start_time = time.time()
        print(f'\nRemoving unused chunks of world "{world}"...')
        with tqdm(total=len(files) * 32 * 32 * 2,
                  unit_scale=1 / 32 / 32 / 2,
                  bar_format='{percentage:.2f}% |{bar}| [{n:.0f}/{total:.0f} files]  ') as pbar:

            for region_file in files:
                with region_file.open('r+b') as file:
                    region = RegionFile(fileobj=file)

                    chunk_count = region.chunk_count()
                    total += chunk_count
                    pbar.update(32 * 32 * 2 - chunk_count * 2)

                    delete = []
                    for chunk in region.iter_chunks():
                        if (chunk['Level'] if 'Level' in chunk else chunk)['InhabitedTime'].value == 0:
                            delete.append((chunk.loc.x, chunk.loc.z))
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

        print(f'Removed {count}/{total} ({count / total * 100:0.2f}%) chunks of world "{world}". '
              f'(Elapsed time: {human_readable_elapsed_time}; Freed space: {human_readable_freed_space})')

        if output_file:
            total_freed_space += raw_freed_space
            worlds[world] = {
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

    if output_file:
        elapsed_time = int(round((time.time() - total_start_time) * 1000))
        freed_space, freed_space_unit = format_freed_space(total_freed_space)

        data = {
            'worlds': worlds,
            'total': {
                'elapsed_time': {
                    'raw': elapsed_time,
                    'human_readable': format_time(elapsed_time)
                },
                'freed_space': {
                    'raw': total_freed_space,
                    'human_readable': f'{freed_space:.2f}{freed_space_unit}'
                }
            }
        }

        with output_file.open('w') as file:
            if output_format == 'json':
                json.dump(data, file, indent=3)
            elif output_format == 'yaml':
                yaml.dump(data, file, indent=3)
            print(f'\nSaved output to "{output_file.name}"')
