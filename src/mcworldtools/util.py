import sys
from itertools import chain
from pathlib import Path

possible_region_folders = {
    'DIM1/region': 'end',
    'DIM-1/region': 'nether',
    'region': 'overworld'
}


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def parse_yes_no(answer, default=None):
    if not answer:
        return default
    if answer.lower() == "y":
        return True
    if answer.lower() == "n":
        return False
    print("Please state \"y\" or \"n\"")
    return None


def get_region_folders(world_folder):
    return [region_folder for region_folder in [Path(world_folder, folder) for folder in possible_region_folders.keys()] if
            region_folder.is_dir()]


def list_files(folders):
    files = []
    for folder in folders:
        for file in folder.iterdir():
            if __name__ == '__main__':
                if file.is_file() and file.name.endswith('.mca'):
                    files.append(file)
    return files


def map_files(folders):
    files = {}
    for folder in folders:
        folder_str = str(folder)
        dimension = None
        for region_folder, dim in possible_region_folders.items():
            if folder_str.endswith(region_folder):
                dimension = dim
                break

        if not dimension:
            continue

        files_in_folder = []
        for file in folder.iterdir():
            if file.is_file() and file.name.endswith('.mca'):
                files_in_folder.append(file)
        if files_in_folder:
            files[dimension] = files_in_folder
    return files


def get_all_files(mapped_files):
    return list(chain.from_iterable(list(mapped_files.values())))


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
