from itertools import chain
from pathlib import Path
from nbt.nbt import *
import readline

dimensions = ['overworld', 'nether', 'end']
possible_region_folders = {
    'DIM1/region': 'end',
    'DIM-1/region': 'nether',
    'region': 'overworld'
}
possible_entity_folders = {
    'DIM1/entities': 'end',
    'DIM-1/entities': 'nether',
    'entities': 'overworld',
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
    return [region_folder for region_folder in [Path(world_folder, folder) for folder in possible_region_folders.keys()]
            if region_folder.is_dir()]


def get_entity_folders(world_folder):
    entity_folders = {}
    for folder, dimension in possible_entity_folders.items():
        if dimension not in entity_folders.values():
            entity_folder = Path(world_folder, folder)
            if entity_folder.is_dir():
                entity_folders[entity_folder] = dimension
    return entity_folders.keys()


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
        for region_folder, dim in possible_entity_folders.items():
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


def strip_id(minecraft_id):
    return minecraft_id[(len('minecraft:') if minecraft_id.lower().startswith('minecraft:') else 0):]


def _int_to_hex(val, nbits):
    return hex((val + (1 << nbits)) % (1 << nbits)).lstrip('0x')


def _hex_to_int(val, nbits):
    i = int(val, 16)
    if i >= 2 ** (nbits - 1):
        i -= 2 ** nbits
    return i


def convert_ints_to_uuid(uuid_ints):
    uuid = ""
    for i in uuid_ints:
        uuid += _int_to_hex(i, 32)
    uuid = f'{uuid[:20]}-{uuid[20:]}'
    uuid = f'{uuid[:16]}-{uuid[16:]}'
    uuid = f'{uuid[:12]}-{uuid[12:]}'
    uuid = f'{uuid[:8]}-{uuid[8:]}'
    return uuid


def convert_least_and_most_to_uuid(uuid_least, uuid_most):
    uuid = _int_to_hex(uuid_least, 64) + _int_to_hex(uuid_most, 64)
    uuid = f'{uuid[:20]}-{uuid[20:]}'
    uuid = f'{uuid[:16]}-{uuid[16:]}'
    uuid = f'{uuid[:12]}-{uuid[12:]}'
    uuid = f'{uuid[:8]}-{uuid[8:]}'
    return uuid


def convert_uuid_to_ints(uuid):
    uuid = uuid.replace('-', '')
    ints = []
    for part in [uuid[i:i + 8] for i in range(0, len(uuid), 8)]:
        ints.append(_hex_to_int(part, 32))
    return ints


def convert_uuid_to_least_and_most(uuid):
    uuid = uuid.replace('-', '')
    return _hex_to_int(uuid[:16], 64), _hex_to_int(uuid[16:], 64)


def convert_nbt(nbt, keys=None):
    if isinstance(nbt, TAG_Compound):
        data = {}
        for name, tag in nbt.iteritems():
            if keys and name not in keys:
                continue
            data[name] = convert_nbt(tag)
        return data
    elif isinstance(nbt, TAG_List):
        data = []
        for tag in nbt:
            data.append(convert_nbt(tag))
        return data
    else:
        return nbt.value


class SimpleCompleter(object):  # Custom completer

    def __init__(self, options, case_insensitive):
        self.matches = None
        self.options = sorted(options)
        self.case_insensitive = case_insensitive

    def complete(self, text, state):
        if state == 0:  # on first trigger, build possible matches
            if text:  # cache matches (entries that start with entered text)
                if self.case_insensitive:
                    self.matches = [s for s in self.options
                                    if s and s.lower().startswith(text.lower())]
                else:
                    self.matches = [s for s in self.options
                                    if s and s.startswith(text)]
            else:  # no text entered, all matches possible
                self.matches = self.options[:]

        # return match indexed by state
        try:
            return self.matches[state]
        except IndexError:
            return None


def complete(completions, case_insensitive=False):
    completer = SimpleCompleter(completions, case_insensitive)
    readline.set_completer(completer.complete)
    readline.parse_and_bind('tab: complete')
