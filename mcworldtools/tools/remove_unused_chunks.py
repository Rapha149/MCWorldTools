import time
from tqdm import tqdm
from chunk import Chunk
from pathlib import Path
from nbt.region import *
from nbt.nbt import *

def list_files(dir):
   return [file for file in dir.iterdir() if file.is_file() and file.name.endswith('.mca')]

def get_size(files):
   return sum(file.stat().st_size for file in files)

def start(world_folder):
   region_folder = Path(world_folder, 'region')
   if not region_folder.is_dir():
      print('No region folder was found.')
      exit(3)

   print('\nWarning: This operation will delete all chunks in which no player was present.'
         '\nTherefore, chunks with changed blocks may be deleted since players can change blocks even if they are not in the chunk.'
         '\nIt is recommended to make a backup of your world beforehand.'
         '\nNo further confirmation requests will be made before chunks are deleted.')
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

   elapsed_seconds = int(time.time() - start_time)
   elapsed_minutes = int(elapsed_seconds / 60)
   elapsed_seconds %= 60

   new_size = get_size(list_files(region_folder))
   freed_space_unit = 'kB'
   freed_space = (size - new_size) / 1000
   if freed_space >= 1000:
      freed_space /= 1000
      freed_space_unit = 'MB'
   if freed_space >= 1000:
      freed_space /= 1000
      freed_space_unit = 'GB'

   print(f'\nDeleted {count}/{total} chunks. (Elapsed time: {elapsed_minutes}m {elapsed_seconds}s; Freed space: {freed_space:.2f}{freed_space_unit})')