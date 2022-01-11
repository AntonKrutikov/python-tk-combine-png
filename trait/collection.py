import json
from typing import Iterator, Tuple
from trait.file import TraitFile
from trait.trait import Trait
from trait.group import TraitGroup

class TraitCollection():
    """Collection of traits loaded from traits.json file. Also provide collection health check"""

    def __init__(self) -> None:
        self.collection:list[Trait] = []
        self.groups:list[TraitGroup] = []

        self.out_order:list[str] = []
        self.out_order_hide_other:bool = False

        self.order:list[str] = []
        self.order_hide_other:bool = False


    def __iter__(self) -> Iterator[Trait]:
        return self.collection.__iter__()

    def __next__(self) -> Trait:
        return self.collection.__next__()

    def load_from_file(self, path:str) -> None:
        """Load Traits from json file. File must have valid strucutre. Not real file paths for each Trait - ignored."""
        
        with open(path) as json_file:
            parsed = json.load(json_file)
            for group, traits in parsed.items():
                group:str
                if group == '_out_order' and isinstance(parsed[group], list):
                    self.out_order = parsed[group]
                if group == '_out_order_hide_other' and isinstance(parsed[group], bool):
                    self.out_order_hide_other = parsed[group]
                if group == '_order' and isinstance(parsed[group], list):
                    self.order = parsed[group]
                if group == '_order_hide_other' and isinstance(parsed[group], bool):
                    self.order_hide_other = parsed[group]
                if not group.startswith('_'):
                    for name, trait in traits.items():
                        name:str
                        if not name.startswith('_'):
                            trait = Trait.parse(name, group, trait)
                            self.collection.append(trait)
        self.groups = self.make_groups()
        self.health_check()

    def make_groups(self) -> list[TraitGroup]:
        """Collect all traits to it associated group"""

        groups:dict[str, TraitGroup] = {}
        for trait in self.collection:
            if not self.order_hide_other or trait.group in self.order:
                if trait.group not in groups:
                        groups[trait.group] = TraitGroup(trait.group)
                groups[trait.group].append(trait)
            
        group_list = [group for _,group in groups.items()]
        group_list.sort(key=lambda g: self.order.index(g.name) if g.name in self.order else len(self.order))
        return group_list


    def health_check(self) -> None:
        """Do checks over self items and print notice if check failed."""

        self.check_duplicate_names()
        self.check_adapted_exists()
        self.check_excluded_exists()
        self.check_hide_out_not_ordered()

    # def colored(self,r, g, b, text):
    #     return "\033[38;2;{};{};{}m{}\033[38;2;255;255;255m".format(r, g, b, text)

    def check_duplicate_names(self) -> None:
        """Check if trait name not unique over whole collection"""

        for trait in self.collection:
            others = [other for other in self.collection if other.name == trait.name and other != trait]
            if len(others)>0:
                print("Notice: Trait '%s -> %s' has same inner name as:" % (trait.group, trait.name), *["'%s -> %s'," % (o.group, o.name) for o in others])

    def check_adapted_exists(self) -> None:
        """Check for adapted_to property link to unknow trait name in collection"""

        for trait in self.collection:
            for file in trait.files:
                for adapted in file.adapted_to:
                    if adapted not in [t.name for t in self.collection]:
                        print("Notice: Trait '%s -> %s' adapted to unknown trait name '%s'" % (trait.group, trait.name, adapted))

    def check_excluded_exists(self) -> None:
        """Check for exclude property link to unknow trait name in collection"""

        for trait in self.collection:
            for exclude in trait.exclude:
                if exclude not in [t.name for t in self.collection]:
                    print("Notice: Trait '%s -> %s' excluded for unknown trait name '%s'" % (trait.group, trait.name, exclude))

    def check_hide_out_not_ordered(self) -> None:
        """Check if group name not in order list for json output and out_json_hide_not_ordered is True"""

        if self.out_order_hide_other:
            for group in self.groups:
                if group.name not in self.out_order:
                    print("Notice: Attribute '%s' not in out_json_order list and will be hidden in any resulting NFT json file." % group.name)

class TraitCollectionState():
    """Wrapper around TraitCollection which store selected trait and file per group. 
    Also provide conndition, excludes and adoptions state."""

    def __init__(self, traits:TraitCollection) -> None:
        self.traits:TraitCollection = traits
        self.groups:dict[TraitGroup,Tuple[Trait, TraitFile]] = {}

        for group in traits.groups:
            # TODO: checks
            trait = group.traits[0]
            file = trait.files[0]
            self.groups[group] = (trait, file)
    
    def current(self, group:TraitGroup) -> Tuple[Trait, TraitFile]:
        return self.groups[group]

    def next(self, group:TraitGroup) ->Tuple[Trait, TraitFile]:
        """Return next file of trait or next trait"""

        trait, file = self.current(group)

        file_indx = trait.files.index(file)
        if file_indx + 1 < len(trait.files):
            file = trait.files[file_indx + 1]
        else:
            trait_index = group.traits.index(trait)
            if trait_index + 1 < len(group.traits):
                trait = group.traits[trait_index + 1]
                file = trait.files[0]
            else:
                trait = group.traits[0]
                file = trait.files[0]

        self.groups[group] = (trait, file)
        return self.current(group)

    def prev(self, group:TraitGroup) ->Tuple[Trait, TraitFile]:
        """Return previous file of trait or previous trait"""

        trait, file = self.current(group)

        file_indx = trait.files.index(file)
        if file_indx - 1 >= 0:
            file = trait.files[file_indx - 1]
        else:
            trait_index = group.traits.index(trait)
            if trait_index - 1 >= 0:
                trait = group.traits[trait_index - 1]
                file = trait.files[-1]
            else:
                trait = group.traits[-1]
                file = trait.files[-1]

        self.groups[group] = (trait, file)
        return self.current(group)

    def current_list(self) -> list[Tuple[Trait, TraitFile]]:
        traits:list[Tuple[Trait, TraitFile]] = []
        for group in self.groups:
            traits.append(self.groups[group])
        return traits

    def conditions(self) -> dict[Trait,list[Tuple[str,bool]]]:
        """Return adapted_to match or not for current state"""
        match:dict[Trait,list[Tuple[str,bool]]] = {}
        for group in self.groups:
            trait, file = self.groups[group]
            if len(file.adapted_to) > 0:
                match[trait] = []
                for adapted in file.adapted_to:
                    if adapted in [trait.name for trait, file in self.current_list()]:
                        match[trait].append((adapted, True))
                    else:
                        match[trait].append((adapted, False))
        return match

    def excludes(self) -> dict[Trait,list[Tuple[str,bool]]]:
        """Return excluded or not for current state"""
        match:dict[Trait,list[Tuple[str,bool]]] = {}
        for group in self.groups:
            trait, file = self.groups[group]
            if len(trait.exclude) > 0:
                match[trait] = []
                for exclude in trait.exclude:
                    match[trait] = []
                    if exclude in [trait.name for trait, file in self.current_list()]:
                        match[trait].append((exclude, True))
                    else:
                        match[trait].append((exclude, False))
        return match

    def adaptions(self) -> dict[Trait,list[Tuple[str,bool]]]:
        match:dict[Trait,list[Tuple[str,bool]]] = {}
        for group in self.groups:
            trait, current_file = self.groups[group]
            match[trait] = []
            for file in trait.files:
                if file != current_file and len(file.adapted_to) > 0:
                    for adapted in file.adapted_to:
                        if adapted in [trait.name for trait, file in self.current_list()]:
                            match[trait].append((adapted, True))
        return match