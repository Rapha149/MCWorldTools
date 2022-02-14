import time
import json, yaml
from tqdm import tqdm
from chunk import Chunk
from pathlib import Path
from nbt.region import *
from nbt.nbt import *

def list_files(dir):
   return [file for file in dir.iterdir() if file.is_file() and file.name.endswith('.mca')]

def get_size(files):
   return sum(file.stat().st_size for file in files)

def start(world_folder, output_file, output_format, confirm):
   region_folder = Path(world_folder, 'region')
   if not region_folder.is_dir():
      print('No region folder was found.')
      exit(3)

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

   files = list_files(region_folder)
   size = get_size(files)

   count, total = 0, 0
   start_time = time.time()
   print('\nRemoving unused chunks...')
   with tqdm(total = len(files) * 32 * 32 * 2,
             unit_scale = 1 / 32 / 32 / 2,
             bar_format = '{percentage:.2f}% |{bar}| [{n:.0f}/{total:.0f} files]  ') as pbar:

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
   elapsed_seconds = int(elapsed_time / 1000)
   elapsed_minutes = int(elapsed_seconds / 60)
   elapsed_seconds %= 60
   human_readable_elapsed_time = f'{elapsed_minutes}m {elapsed_seconds}s'

   new_size = get_size(list_files(region_folder))
   freed_space_unit = 'kB'
   raw_freed_space = size - new_size
   freed_space = raw_freed_space / 1000
   if freed_space >= 1000:
      freed_space /= 1000
      freed_space_unit = 'MB'
   if freed_space >= 1000:
      freed_space /= 1000
      freed_space_unit = 'GB'
   human_readable_freed_space = f'{freed_space:.2f}{freed_space_unit}'

   print(f'\nRemoved {count}/{total} ({count/total*100:0.2f}%) chunks. (Elapsed time: {human_readable_elapsed_time}; Freed space: {human_readable_freed_space})')

   if output_file:
      data = {
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
      with output_file.open('w') as file:
         if output_format == 'json':
            json.dump(data, file, indent=3)
         elif output_format == 'yaml':
            yaml.dump(data, file, indent=3)
         print(f'\nSaved output to "{output_file.name}"')