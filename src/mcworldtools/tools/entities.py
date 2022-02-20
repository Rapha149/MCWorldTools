import json
import re

import yaml
from nbt.region import *
from tqdm import tqdm

from ..util import *

uuid_pattern = '^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$'
actions = ['Find entities', 'Remove entities']
remove_by_possibilites = ['id', 'uuid', 'all']


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

    use_entity_id, entity_id, limit_to_dimension, limit_dimension, include_nbt, nbt_keys = None, None, None, None, \
                                                                                           None, None
    if input_data:
        print('\nLoading more input file data...')
        if 'id' in input_data:
            entity_id = input_data['id']
            if entity_id is None:
                use_entity_id = False
                print(f'Not filtering by entity id.')
            else:
                if not isinstance(entity_id, str):
                    eprint(f'"id" has to be a number but is {type(entity_id).__name__}')
                    exit(3)
                use_entity_id = True
                entity_id = strip_id(entity_id.lower())
                print(f'Using entity id "{entity_id}"')

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

        if 'nbt_keys' in input_data:
            nbt_keys = input_data['nbt_keys']
            if nbt_keys is None:
                include_nbt = False
                print(f'Not including NBT keys.')
            else:
                if not isinstance(nbt_keys, list):
                    eprint(f'"nbt_keys" has to be a list but is {type(nbt_keys).__name__}')
                    exit(3)
                include_nbt = True
                print(f'Using {len(nbt_keys)} NBT keys.')

    if use_entity_id is None:
        print('\nChoose an entity id to filter entities. Enter nothing for all entities.')
        answer = input('Entity id: ')
        if not answer:
            use_entity_id = False
        else:
            use_entity_id = True
            entity_id = strip_id(answer.lower())
            print(f'Using entity id "{entity_id}"')

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

    if include_nbt is None:
        print('\nChoose the NBT keys to be included in the output. Enter nothing once your finished.'
              '\nFor all NBT keys, enter nothing directly. Enter "---" to not include any NBT keys.'
              '\nPlease note that NBT keys are case sensitive.')
        nbt_keys = []
        while True:
            answer = input(f'{len(nbt_keys) + 1}. NBT key: ').strip()
            if not answer:
                include_nbt = True
                if nbt_keys:
                    print(f'Using {len(nbt_keys)} nbt keys.')
                else:
                    nbt_keys = None
                    print('Using all nbt keys.')
                break

            if answer == '---':
                include_nbt = False
                print('Not including any NBT keys.')
                break

            nbt_keys.append(answer)

    total_start_time = time.time()
    total_entities = 0
    worlds = {}
    for world_folder in world_folders:
        entity_folders = get_entity_folders(world_folder)
        if not entity_folders:
            print(f'\nNo entity folder was found in world "{world_folder}"')
            continue

        files = map_files(entity_folders)
        file_count = len(get_all_files(files))

        entities = []
        start_time = time.time()
        messages = []
        print(f'\nSearching for entities in world "{world_folder}"...')
        with tqdm(total=file_count * 32 * 32 if file_count > 0 else 1,
                  unit_scale=1 / 32 / 32,
                  bar_format='{percentage:.2f}% |{bar}| [{n:.0f}/{total:.0f} files]  ') as pbar:

            if file_count <= 0:
                pbar.update()

            for dimension in dimensions:
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

                            if 'Entities' not in data:
                                messages.append(f'Chunk {x} {z} (in world at {world_x} {world_z}) in the region file "'
                                                f'{region_file}" could not be read.')
                                continue

                            for entity in data['Entities']:
                                if use_entity_id and strip_id(entity['id'].value.lower()) != entity_id:
                                    continue
                                entities.append({
                                    'id': entity['id'].value,
                                    'uuid': convert_ints_to_uuid(convert_nbt(entity['UUID'])) if 'UUID' in entity else
                                    convert_least_and_most_to_uuid(entity['UUIDLeast'].value, entity['UUIDMost'].value),
                                    'loc': {
                                        'dimension': dimension,
                                        'x': entity['Pos'][0].value,
                                        'y': entity['Pos'][1].value,
                                        'z': entity['Pos'][2].value
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
                                    'nbt': '{}' if not include_nbt else json.dumps(convert_nbt(entity, keys=nbt_keys))
                                })

                            pbar.update()

        elapsed_time = int(round((time.time() - start_time) * 1000))
        human_readable_elapsed_time = format_time(elapsed_time)

        entity_count = len(entities)
        print(f'Found {entity_count} entities in world "{world_folder}". (Elapsed time: '
              f'{human_readable_elapsed_time})')

        for message in messages:
            print(message)

        total_entities += entity_count
        if output_file:
            worlds[str(world_folder.resolve())] = {
                'entities': entities,
                'elapsed_time': {
                    'raw': elapsed_time,
                    'human_readable': human_readable_elapsed_time
                }
            }

    elapsed_time = int(round((time.time() - total_start_time) * 1000))
    human_readable_elapsed_time = format_time(elapsed_time)

    if len(world_folders) > 1:
        print(f'\nTotal found entities: {total_entities}'
              f'\nTotal elapsed time: {human_readable_elapsed_time}')

    if output_file:
        data = {
            'worlds': worlds,
            'total': {
                'total_entities': total_entities,
                'elapsed_time': {
                    'raw': elapsed_time,
                    'human_readable': human_readable_elapsed_time
                }
            }
        }

        with Path(output_file).open('w') as file:
            if output_format == 'plain':
                file.write(f'--- MCWorldTools by Rapha149 ---'
                           f'\n\u00B7\u00B7\u00B7 Find entities \u00B7\u00B7\u00B7'
                           f'\n\nTotal found entities: {total_entities}'
                           f'\nTotal elapsed time: {human_readable_elapsed_time}'
                           f'\n\n[ Worlds ]')
                for world, info in worlds.items():
                    entities = info['entities']
                    entity_count = len(entities)
                    file.write(f'\n{world}'
                               f'\n    Entities found: {entity_count}'
                               f'\n    Elapsed time: {info["elapsed_time"]["human_readable"]}')
                    if entities:
                        file.write('\n    Entities:')
                        for i in range(entity_count):
                            if i > 0:
                                file.write('\n        ------------------')

                            entity = entities[i]
                            loc, chunk = entity['loc'], entity['chunk']
                            file.write(f'\n        ID: {entity["id"]}'
                                       f'\n        UUID: {entity["uuid"]}'
                                       f'\n        Dimension: {loc["dimension"].capitalize()}'
                                       f'\n        Location: {loc["x"]} {loc["y"]} {loc["z"]}'
                                       f'\n        Chunk:'
                                       f'\n            In region file: {chunk["in_region_file"]["x"]} '
                                       f'{chunk["in_region_file"]["z"]}'
                                       f'\n            In world: {chunk["in_world"]["x"]} {chunk["in_world"]["z"]}')
                            if include_nbt:
                                file.write(f'\n        NBT: {entity["nbt"]}')
                    file.write('\n')

            elif output_format == 'json':
                json.dump(data, file, indent=3)
            elif output_format == 'yaml':
                yaml.dump(data, file, indent=3)

            print(f'\nSaved output to "{output_file}"')


def remove(world_folders, output_file, output_format, input_data, confirm):
    possibilities_str = '"' + '", "'.join(remove_by_possibilites) + '"'
    remove_by, entity_id, uuid, uuid_ints, uuid_least, uuid_most = None, None, None, None, None, None
    if input_data and 'remove_by' in input_data:
        print('\nLoading more input data...')
        remove_by = input_data['remove_by']
        if not isinstance(remove_by, str):
            eprint(f'"remove_by" has to be text but is {type(remove_by).__name__}')
            exit(3)
        remove_by = remove_by.lower()
        if remove_by not in remove_by_possibilites:
            eprint(f'"remove_by" has to be one of {possibilities_str}')
            exit(3)
        print(f'Removing {"by " if remove_by != "all" else ""}{remove_by}')

    if not remove_by:
        print('\nDo you want to remove by "id", by "uuid" or remove "all" entities?')
        complete(remove_by_possibilites)
        while True:
            answer = input('Remove by: ').lower()
            if answer not in remove_by_possibilites:
                print(f'Please state one of {possibilities_str}')
                continue
            remove_by = answer
            break
        complete([])

    if input_data:
        show = 'remove_by' not in input_data
        if remove_by == 'id' and 'id' in input_data:
            if show:
                print('\nLoading more input data...')

            entity_id = input_data['id']
            if not isinstance(entity_id, str):
                eprint(f'"id" has to be a number but is {type(entity_id).__name__}')
                exit(3)
            entity_id = strip_id(entity_id.lower())
            print(f'Using entity id "{entity_id}"')

        elif remove_by == 'uuid' and 'uuid' in input_data:
            if show:
                print('\nLoading more input data...')

            uuid = input_data['uuid']
            if not isinstance(uuid, str):
                eprint(f'"uuid" has to be a number but is {type(uuid).__name__}')
                exit(3)
            if not re.match(uuid_pattern, uuid):
                eprint(f'"uuid" is not a valid uuid.')
                exit(3)
            print(f'Using uuid "{uuid}"')

    if remove_by == 'id' and not entity_id:
        print('\nChoose an entity id of which entities should be removed.')
        while True:
            answer = input('Entity id: ')
            if not answer:
                print('Please state an entity id.')
                continue

            entity_id = strip_id(answer.lower())
            print(f'Using entity id "{entity_id}"')
            break

    if remove_by == 'uuid':
        if not uuid:
            print('\nState the uuid of the entity that should be removed.')
            while True:
                answer = input('UUID: ').strip()
                if not answer:
                    print('Please state a uuid.')
                    continue
                if not re.match(uuid_pattern, answer):
                    print('Invalid uuid.')
                    continue
                uuid = answer.lower()
                break

        uuid_ints = convert_uuid_to_ints(uuid)
        uuid_least, uuid_most = convert_uuid_to_least_and_most(uuid)

    if not confirm:
        entity_specification = 'entities'
        if remove_by == 'id':
            entity_specification = 'the entities with the given id'
        elif remove_by == 'uuid':
            entity_specification = 'the entity with the given uuid'
        elif remove_by == 'all':
            entity_specification = 'ALL entities'

        print(f'\nWarning: This operation will remove {entity_specification} permanentely.'
              '\nIt is recommended to make a backup of your world beforehand.')
        print('No further confirmation requests will be made before entities are removed.')
        while True:
            answer = parse_yes_no(input('Do you want to continue? (y/N): '), default=False)
            if answer is not None:
                if not answer:
                    exit()
                break

    total_start_time = time.time()
    total_entities = 0
    worlds = {}
    for world_folder in world_folders:
        entity_folders = get_entity_folders(world_folder)
        if not entity_folders:
            print(f'\nNo entity folder was found in world "{world_folder}"')
            continue

        files = map_files(entity_folders)
        file_count = len(get_all_files(files))

        start_time = time.time()
        entity_count = 0
        messages = []
        print(f'\nRemoving entities in world "{world_folder}"...')
        with tqdm(total=file_count * 32 * 32 if file_count > 0 else 1,
                  unit_scale=1 / 32 / 32,
                  bar_format='{percentage:.2f}% |{bar}| [{n:.0f}/{total:.0f} files]  ') as pbar:

            if file_count <= 0:
                pbar.update()

            for dimension, region_files in files.items():
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

                            if 'Entities' not in data:
                                messages.append(f'Chunk {x} {z} (in world at {world_x} {world_z}) in the region file "'
                                                f'{region_file}" could not be read.')
                                continue

                            to_remove = []
                            entities = data['Entities']
                            for i in range(len(entities)):
                                entity = entities[i]
                                if remove_by == 'id':
                                    if strip_id(entity['id'].value.lower()) != entity_id:
                                        continue
                                elif remove_by == 'uuid':
                                    if 'UUID' in entity:
                                        if uuid_ints != convert_nbt(entity['UUID']):
                                            continue
                                    else:
                                        if uuid_least != entity['UUIDLeast'].value or \
                                                uuid_most != entity['UUIDMost'].value:
                                            continue
                                elif remove_by != 'all':
                                    continue
                                to_remove.append(i)

                            if to_remove:
                                entity_count += len(to_remove)
                                for i in reversed(to_remove):
                                    del entities[i]
                                region.write_chunk(x, z, chunk)

                            pbar.update()

        elapsed_time = int(round((time.time() - start_time) * 1000))
        human_readable_elapsed_time = format_time(elapsed_time)

        print(f'Removed {entity_count} entities in world "{world_folder}". (Elapsed time: '
              f'{human_readable_elapsed_time})')

        for message in messages:
            print(message)

        total_entities += entity_count
        if output_file:
            worlds[str(world_folder.resolve())] = {
                'removed_entities': entity_count,
                'elapsed_time': {
                    'raw': elapsed_time,
                    'human_readable': human_readable_elapsed_time
                }
            }

    elapsed_time = int(round((time.time() - total_start_time) * 1000))
    human_readable_elapsed_time = format_time(elapsed_time)

    if len(world_folders) > 1:
        print(f'\nTotal removed entities: {total_entities}'
              f'\nTotal elapsed time: {human_readable_elapsed_time}')

    if output_file:
        data = {
            'worlds': worlds,
            'total': {
                'total_removed_entities': total_entities,
                'elapsed_time': {
                    'raw': elapsed_time,
                    'human_readable': human_readable_elapsed_time
                }
            }
        }

        with Path(output_file).open('w') as file:
            if output_format == 'plain':
                file.write(f'--- MCWorldTools by Rapha149 ---'
                           f'\n\u00B7\u00B7\u00B7 Remove entities \u00B7\u00B7\u00B7'
                           f'\n\nTotal removed entities: {total_entities}'
                           f'\nTotal elapsed time: {human_readable_elapsed_time}'
                           f'\n\n[ Worlds ]')
                for world, info in worlds.items():
                    file.write(f'\n{world}'
                               f'\n    Removed entities: {info["removed_entities"]}'
                               f'\n    Elapsed time: {info["elapsed_time"]["human_readable"]}\n')

            elif output_format == 'json':
                json.dump(data, file, indent=3)
            elif output_format == 'yaml':
                yaml.dump(data, file, indent=3)

            print(f'\nSaved output to "{output_file}"')
