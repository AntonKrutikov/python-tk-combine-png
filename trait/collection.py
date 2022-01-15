import copy
import json
from typing import Iterator, Tuple, List, Dict, Optional
import trait
from trait.file import TraitFile
from trait.trait import Trait
from trait.group import TraitGroup

def colored(text, r, g, b):
    return "\033[38;2;{};{};{}m{}\033[0m".format(r, g, b, text)

class TraitCollectionOrder():

    def __init__(self, collection:"TraitCollection" = None) -> None:
        self.collection = collection
        self._image_order:List[str] = []
        self._image_order_exclusion:bool = False
        self._json_order:List[str] = []
        self._json_order_exclusion:bool = False

        pass

    def is_default(self) -> bool:
        if self._image_order is not None or self._json_order is not None:
            return False
        return True

    @property
    def image_order(self) -> List[str]:
        if len(self._image_order) == 0:
            return [group.name for group in self.collection.groups]
        ordered = sorted([group.name for group in self.collection.groups], key=lambda g: self._image_order.index(g) if g in self._image_order else len(self._image_order))
        if self._image_order_exclusion == True:
            ordered = [group for group in ordered if group in self._image_order]
        return ordered

    @property
    def json_order(self) -> List[str]:
        if len(self._json_order) == 0:
            return [group.name for group in self.collection.groups]
        ordered = sorted([group.name for group in self.collection.groups], key=lambda g: self._json_order.index(g) if g in self._json_order else len(self._json_order))
        if self._json_order_exclusion == True:
            ordered = [group for group in ordered if group in self._json_order]
        return ordered

    def check_image_order(self) -> Tuple[bool,str]:
        """Check that values in "_image_order" exists in trait types"""

        not_found = []
        for o in self._image_order:
            if o not in [group.name for group in self.collection.groups]:
                not_found.append(o)
        if len(not_found) > 0:
            return False, '"_image_order" contain unknown trait type(s): [%s]' % ','.join('"%s"' % group for group in not_found)
        return True, ''

    def check_json_order(self) -> Tuple[bool,str]:
        """Check that values in "_json_order" exists in "_image_order". Must call check_image_order() before."""

        not_found = []
        for o in self._json_order:
            if o not in [group for group in self.image_order]:
                not_found.append(o)
        if len(not_found) > 0:
            return False, '"_json_order" contain unknown trait type(s): [%s]' % ','.join('"%s"' % group for group in not_found)
        return True,''

    def check(self) -> Tuple[bool,str]:
        ok, err = self.check_image_order()
        if not ok:
            return ok, err
        ok, err = self.check_json_order()
        if not ok:
            return ok, err
        return True, ''

    @classmethod
    def parse(cls, collection_list:List[Dict]) -> List["TraitCollectionOrder"]:
        """Parse '_collections' attribute from traits.json and return List of TraitCollectionOrder"""

        result = []
        for collection in collection_list:
            trait_order = TraitCollectionOrder()
            trait_order._image_order = collection.get('_image_order', [])
            trait_order._image_order_exclusion = collection.get('_image_order_exclusion', False)
            trait_order._json_order = collection.get('_json_order', [])
            trait_order._json_order_exclusion = collection.get('_json_order_exclusion', False)
            result.append(trait_order)
        return result

class TraitCollectionInfo():
    def __init__(self, collection:"TraitCollection") -> None:
        self.collection = collection

    @property
    def original_groups(self) -> List[str]:
        """Return all possible group(type) names from original collection"""

        collection = self.collection if self.collection.original is None else self.collection.original
        return [group.name for group in collection.groups]

    @property
    def ordered_groups(self) -> List[str]:
        return self.collection.order.image_order

    @property
    def ordered_json(self) -> List[str]:
        return self.collection.order.json_order

    def __str__(self) -> str:
        msg = []
        msg.append('Info: There are %s trait type(s): [%s]' % (len(self.original_groups), ','.join('"%s"' % group for group in self.original_groups)))
        msg.append('Info: The NFTs will consist of %s trait type(s) [%s]' % (len(self.ordered_groups), ','.join('"%s"' % group for group in self.ordered_groups)))
        msg.append('Info: The JSON file will consist of %s trait type(s) [%s]' % (len(self.ordered_json), ','.join('"%s"' % group for group in self.ordered_json)))
        for group in self.collection.groups:
            msg.append('Info: The trait type "%s" has the values [%s]' % (group.name, ','.join('"%s"' % trait.name for trait in group.traits)))
        return '\n'.join(msg)
        

class TraitCollection():
    """Collection of traits loaded from traits.json file. Also provide collection health check"""

    def __init__(self) -> None:
        self.collection:List[Trait] = []
        self.groups:List[TraitGroup] = []
        self.order:TraitCollectionOrder = TraitCollectionOrder(self)
        self.original:TraitCollection = None
        self.info:TraitCollectionInfo = TraitCollectionInfo(self)
        self.error_messages:List[str] = []

    def __iter__(self) -> Iterator[Trait]:
        return self.collection.__iter__()

    def __next__(self) -> Trait:
        return self.collection.__next__()

    def __copy__(self) -> "TraitCollection":
        copy = TraitCollection()
        copy.collection = self.collection.copy()
        copy.groups = self.groups.copy()
        return copy

    @classmethod
    def load_from_file(cls, path:str) -> List["TraitCollection"]:
        """
        Load Traits from json file. File must have valid strucutre. 
        Not real file paths for each Trait - ignored.
        """

        collections:List["TraitCollection"] = []

        default = TraitCollection()
        order_list:List[TraitCollectionOrder] = []

        with open(path) as json_file:
            parsed = json.load(json_file)
            for group, traits in parsed.items():
                group:str
                if group == '_collections' and isinstance(traits, list):
                    order_list = TraitCollectionOrder.parse(traits)
                if not group.startswith('_'):
                    for name, trait in traits.items():
                        name:str
                        if not name.startswith('_'):
                            trait = Trait.parse(name, group, trait)
                            default.collection.append(trait)
        default.groups = default.make_groups()

        collections.append(default)

        # For each "_collection" entry make ordered version
        for order in order_list:
            ordered = default.make_ordered(order)
            collections.append(ordered)

        return collections

    def make_ordered(self, order:TraitCollectionOrder) -> Optional["TraitCollection"]:
        ordered = copy.copy(self)
        order.collection = ordered
        ordered.order = order
        ordered.original = self

        ordered.groups = [group for group in ordered.groups if group.name in order.image_order]
        # Sort collection
        ordered.groups = sorted(ordered.groups, key=lambda g: order.image_order.index(g.name) if g.name in order.image_order else len(order.image_order))

        return ordered

    def make_groups(self) -> List[TraitGroup]:
        """Collect all traits to it associated group"""

        groups:Dict[str, TraitGroup] = {}
        for trait in self.collection:
            if trait.group not in groups:
                groups[trait.group] = TraitGroup(trait.group)
            groups[trait.group].append(trait)
            
        return list(groups.values())

    def is_valid(self) -> bool:
        """Make fatal checks of collection, if this method return False - collection not valid"""

        err_msg:List[str] = []
        # Check order is valid
        ok, err = self.order.check()
        if not ok:
            err_msg.append(err)

        if len(err_msg) > 0:
            print('\n'.join('%s %s' % (colored('Error:', 255,0,0), msg) for msg in err_msg))
            return False

        return True

    def health_check(self) -> None:
        """Do checks over self items and print notice if check failed."""
        print("Health check:")
        self.check_duplicate_names()
        self.check_adapted_exists()
        self.check_excluded_exists()

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

class TraitCollectionState():
    """Wrapper around TraitCollection which store selected trait and file per group. 
    Also provide conndition, excludes and adoptions state."""

    def __init__(self, traits:TraitCollection) -> None:
        self.traits:TraitCollection = traits
        self.groups:Dict[TraitGroup,Tuple[Trait, TraitFile]] = {}

        for group in traits.groups:
            # TODO: checks
            trait = group.traits[0]
            file = trait.current_file
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

    def current_list(self) -> List[Tuple[Trait, TraitFile]]:
        traits:List[Tuple[Trait, TraitFile]] = []
        for group in self.groups:
            traits.append(self.groups[group])
        return traits

    def conditions(self) -> Dict[Trait,List[Tuple[str,bool]]]:
        """Return adapted_to match or not for current state"""
        match:Dict[Trait,List[Tuple[str,bool]]] = {}
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

    def excludes(self, matched_only:bool = False) -> Dict[Trait,List[Tuple[str,bool]]]:
        """Return excluded or not for current state"""
        match:Dict[Trait,List[Tuple[str,bool]]] = {}
        for group in self.groups:
            trait, file = self.groups[group]
            if len(trait.exclude) > 0:
                match[trait] = []
                for exclude in trait.exclude:
                    if exclude in [trait.name for trait, file in self.current_list()]:
                        match[trait].append((exclude, True))
                    elif not matched_only:
                        match[trait].append((exclude, False))
                if len(match[trait]) == 0:
                    del match[trait]
        return match

    def adaptions(self) -> Dict[Trait,List[Tuple[str,bool]]]:
        match:Dict[Trait,List[Tuple[str,bool]]] = {}
        for group in self.groups:
            trait, current_file = self.groups[group]
            match[trait] = []
            for file in trait.files:
                if file != current_file and len(file.adapted_to) > 0:
                    for adapted in file.adapted_to:
                        if adapted in [trait.name for trait, file in self.current_list()]:
                            match[trait].append((adapted, True))
        return match