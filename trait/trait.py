from typing import List
from trait.file import TraitFile

class Trait():
    """Represent one trait with it attributes, including paths of files from trait.json"""

    def __init__(self, name:str, type_name:str, weight:int = 1, hidden:bool = False) -> None:
        self.name:str = name
        self.type_name:str = type_name
        self.weight:int = weight
        self.hidden:bool = hidden
        self.files:List[TraitFile] = [] 
        self.exclude:List[str] = []
        self.current_file:TraitFile = None
        self.current_file_index:int = None
        self.groups:List[str] = []

    @property
    def full_name(self) -> str:
        return "%s->%s" % (self.type_name, self.name) 

    @classmethod
    def parse(cls, name:str, type_name:str, trait_dict:dict) -> "Trait":
        """Parse single trait from dict provided from traits.json file"""
        trait = Trait(name, type_name)
        
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

        if 'group' in trait_dict:
            groups = trait_dict['group']
            if isinstance(groups, str):
                trait.groups.append(groups)
            if isinstance(groups, list) and all(isinstance(g,str) for g in groups):
                trait.groups = groups
        
        return trait


class TraitType():
    """Represent all Traits per group"""
    
    def __init__(self, name:str) -> None:
        self.name:str = name
        self.traits:List[Trait] = []

    def __len__(self) -> int:
        return len(self.traits)

    def append(self, trait:Trait) -> None:
        self.traits.append(trait)