import sys
from pathlib import Path
from nbt.nbt import *

from tools import remove_unused_chunks, find_blocks, find_command_blocks, find_entities

def main():
   world_folder = Path.cwd()
   if len(sys.argv) >= 2:
      world_folder = Path(sys.argv[1])
      if not world_folder.is_dir():
         print(f'The folder "{sys.argv[1]}" does not exist.')
         exit(1)

   level_dat = Path(world_folder, 'level.dat')
   if not level_dat.is_file():
      if len(sys.argv) >= 2:
         print('That is not a world folder.')
      else:
         print('Please run in a world folder or state a world folder as argument.')
      exit(2)
   
   level = NBTFile(fileobj=level_dat.open('rb'))
   try:
      data = level['Data']
      version = f' (Version: {data["Version"]["Name"]})' if 'Version' in data else ''
      print(f'Detected world: "{data["LevelName"]}"{version}')
   except KeyError:
      print('This is not a valid world folder.')
      exit(2)

   print('Select which tool you want to use.'
      '\n1. Remove unused chunks'
      '\n2. Find blocks'
      '\n3. Find command blocks'
      '\n4. Find entities')

   tool = None
   while True:
      answer = input('Select a tool (1-4): ')
      if not answer.isnumeric():
         print('Please state a number.')
         continue
      
      tool = int(answer)
      if tool < 1 or tool > 4:
         print('Please state a number between 1 and 4.')
         continue
      break

   if tool == 1:
      remove_unused_chunks.start(world_folder)
   elif tool == 2:
      find_blocks.start(world_folder)
   elif tool == 3:
      find_command_blocks.start(world_folder)
   elif tool == 4:
      find_entities.start(world_folder)

if __name__ == '__main__':
   main()