from argparse import ArgumentParser
from pathlib import Path
from re import A
from nbt.nbt import *

try:
   from .tools import remove_unused_chunks, find_blocks, find_command_blocks, find_entities
except ImportError:
   from tools import remove_unused_chunks, find_blocks, find_command_blocks, find_entities

available_tools = ['Remove unused chunks', 'Find blocks', 'Find command blocks', 'Find entities']

def main():
   parser = ArgumentParser(prog='mcworldtools',
                           description='MCWorldTools by Rapha149',
                           allow_abbrev=False)
   parser.add_argument('-w', '--world', help='Use a different world folder than the current working directory.')
   parser.add_argument('-t', '--tool', type=int, choices=range(1, len(available_tools) + 1), help='Choose the tool you want to use beforehand')
   parser.add_argument('-o', '--output', help='Select a file to write the output statistics to.')
   parser.add_argument('-f', '--output-format', choices=['json', 'yaml'], default='json', help='The output file format. May be "json" (default) or "yaml".')
   parser.add_argument('--confirm', action='store_true', help='Automatically confirm any confirmation requests.')
   args = parser.parse_args()

   world_folder = Path.cwd()
   if args.world:
      world_folder = Path(args.world)
      if not world_folder.is_dir():
         print(f'The folder "{sys.argv[1]}" does not exist.')
         exit(1)

   output_file = None
   if args.output:
      output_file = Path(args.output)
      if output_file.is_dir():
         print(f'The output file "{output_file.name}" is a folder.')
         exit(1)

   level_dat = Path(world_folder, 'level.dat')
   if not level_dat.is_file():
      if args.world:
         print('That is not a world folder.')
      else:
         print('Please run in a world folder or use the option "--world".')
      exit(2)
   
   level = NBTFile(fileobj=level_dat.open('rb'))
   try:
      data = level['Data']
      version = f' (Version: {data["Version"]["Name"]})' if 'Version' in data else ''
      print(f'Detected world: "{data["LevelName"]}"{version}')
   except KeyError:
      print(('That' if args.world else 'This') + ' is not a valid world folder.')
      exit(2)


   tool = args.tool
   if not tool:
      print('Select which tool you want to use.'
         '\n1. Remove unused chunks'
         '\n2. Find blocks'
         '\n3. Find command blocks'
         '\n4. Find entities')

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
   print(f'Using tool "{available_tools[tool - 1]}"')

   if tool == 1:
      remove_unused_chunks.start(world_folder, output_file, args.output_format, args.confirm)
   elif tool == 2:
      find_blocks.start(world_folder, output_file, args.output_format, args.confirm)
   elif tool == 3:
      find_command_blocks.start(world_folder, output_file, args.output_format, args.confirm)
   elif tool == 4:
      find_entities.start(world_folder, output_file, args.output_format, args.confirm)

if __name__ == '__main__':
   main()
