import sys


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
