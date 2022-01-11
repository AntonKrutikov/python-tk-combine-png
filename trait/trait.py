from typing import Optional
from trait.file import TraitFile

class Trait():
    """Represent one trait with it attributes, including paths of files from trait.json"""

    def __init__(self, name:str, group:str, weight:int = 1, hidden:bool = False) -> None:
        self.name:str = name
        self.group:str = group
        self.weight:int = weight
        self.hidden:bool = hidden
        self.files:list[TraitFile] = [] 
        self.exclude:list[str] = []
        self.current_file:TraitFile = None
        self.current_file_index:int = None

    @property
    def full_name(self) -> str:
        return "%s->%s" % (self.group, self.name) 

    @classmethod
    def parse(cls, name:str, group:str, trait_dict:dict) -> "Trait":
        """Parse single trait from dict provided from traits.json file"""
        trait = Trait(name, group)
        
        if 'weight' in trait_dict and isinstance(trait_dict['weight'], int):
            trait.weight = trait_dict['weight']

        if 'file' in trait_dict:
            file = trait_dict['file']

            if isinstance(file, str) or isinstance(file, dict): # single variant as str or dict
                trait_file = TraitFile()
                if trait_file.load(file) == True:
                    trait.files.append(trait_file)
            elif isinstance(file, list) and all(isinstance(f, str) for f in file): # single variant as array of paths
                trait_file = TraitFile()
                if trait_file.load(file) == True:
                    trait.files.append(trait_file)
            elif isinstance(file, list): # multiple variants of files for this trait
                for f in file:
                    trait_file = TraitFile()
                    if trait_file.load(f) == True:
                        trait.files.append(trait_file)
            
            if len(trait.files) > 0:
                trait.current_file_index = 0
                trait.current_file = trait.files[0]

        if 'exclude' in trait_dict and isinstance(trait_dict['exclude'], list) and all(isinstance(e, str) for e in trait_dict['exclude']):
            trait.exclude = trait_dict['exclude']
        
        return trait


