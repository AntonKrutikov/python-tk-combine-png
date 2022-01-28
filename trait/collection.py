import copy
import json
from typing import Iterator, Tuple, List, Dict, Optional

from attr import attributes
from nft import NFT
import trait
from trait.file import TraitFile
from trait.trait import Trait
from trait.trait import TraitType

def colored(text, r, g, b):
    return "\033[38;2;{};{};{}m{}\033[0m".format(r, g, b, text)

class TraitCollectionOrder():

    def __init__(self, collection:"TraitCollection" = None) -> None:
        self.collection = collection
        self._image_order:List[str] = []
        self._image_order_exclusion:bool = False
        self._json_order:List[str] = []
        self._json_order_exclusion:bool = False
        self.name_prefix:str = ''
        self.blueprint_path:str = None
        self.blueprint_template:Dict = None
        pass

    def is_default(self) -> bool:
        if self._image_order is not None or self._json_order is not None:
            return False
        return True

    @property
    def image_order(self) -> List[str]:
        if len(self._image_order) == 0:
            return [group.name for group in self.collection.types]
        ordered = sorted([group.name for group in self.collection.types], key=lambda g: self._image_order.index(g) if g in self._image_order else len(self._image_order))
        if self._image_order_exclusion == True:
            ordered = [group for group in ordered if group in self._image_order]
        return ordered

    @property
    def json_order(self) -> List[str]:
        if len(self._json_order) == 0:
            return [group.name for group in self.collection.types]
        ordered = sorted([group.name for group in self.collection.types], key=lambda g: self._json_order.index(g) if g in self._json_order else len(self._json_order))
        if self._json_order_exclusion == True:
            ordered = [group for group in ordered if group in self._json_order]
        return ordered

    def check_image_order(self) -> Tuple[bool,str]:
        """Check that values in "_image_order" exists in trait types"""

        not_found = []
        for o in self._image_order:
            if o not in [group.name for group in self.collection.types]:
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
            trait_order.name_prefix = collection.get('_name_prefix', '')
            trait_order.blueprint_path = collection.get('_blueprint', None)
            if trait_order.blueprint_path is not None:
                trait_order.blueprint_template = TraitCollection.load_blueprint(trait_order.blueprint_path)
            result.append(trait_order)
        return result

class TraitCollectionInfo():
    def __init__(self, collection:"TraitCollection") -> None:
        self.collection = collection

    @property
    def original_groups(self) -> List[str]:
        """Return all possible group(type) names from original collection"""

        collection = self.collection if self.collection.original is None else self.collection.original
        return [group.name for group in collection.types]

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
        for group in self.collection.types:
            msg.append('Info: The trait type "%s" has the values [%s]' % (group.name, ','.join('"%s"' % trait.name for trait in group.traits)))
        return '\n'.join(msg)
        

class TraitCollection():
    """Collection of traits loaded from traits.json file. Also provide collection health check"""

    def __init__(self) -> None:
        self.collection:List[Trait] = []
        self.types:List[TraitType] = []
        self.order:TraitCollectionOrder = TraitCollectionOrder(self)
        self.original:TraitCollection = None
        self.info:TraitCollectionInfo = TraitCollectionInfo(self)
        self.error_messages:List[str] = []
        self.name_prefix:str = ''
        self.blueprint_path:str = None
        self.blueprint_template:Dict = None

    def __iter__(self) -> Iterator[Trait]:
        return self.collection.__iter__()

    def __next__(self) -> Trait:
        return self.collection.__next__()

    def __copy__(self) -> "TraitCollection":
        copy = TraitCollection()
        copy.collection = self.collection.copy()
        copy.types = self.types.copy()
        copy.blueprint_path = self.blueprint_path
        copy.blueprint_template = self.blueprint_template
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
            for attribute, value in parsed.items():
                attribute:str
                if attribute == '_collections' and isinstance(value, list):
                    order_list = TraitCollectionOrder.parse(value)
                if attribute == '_name_prefix' and isinstance(value, str):
                    default.name_prefix = value
                if attribute == '_blueprint' and isinstance(value, str):
                    default.blueprint_path = value
                if not attribute.startswith('_'):
                    for name, trait in value.items():
                        name:str
                        if not name.startswith('_'):
                            trait = Trait.parse(name, attribute, trait)
                            default.collection.append(trait)
        default.types = default.make_groups()

        # Load blueprint template
        if default.blueprint_path is not None:
            default.blueprint_template = cls.load_blueprint(default.blueprint_path)
        if default.blueprint_template is None:
            default.blueprint_template = NFT.blueprint_template

        collections.append(default)

        # For each "_collection" entry make ordered version
        for order in order_list:
            ordered = default.make_ordered(order)
            collections.append(ordered)

        return collections

    @classmethod
    def load_blueprint(cls, path:str = None) -> Optional[Dict]:
        """Load blueprint template once and store it as class variable. This used as default blueprint."""
        template = None
        if path is not None:
            try:
                with open(path) as json_file:
                    template = json.load(json_file)  
            except Exception as e:
                print('Warning: Failed to load collection Blueprint Template "%s". Message: %s' % (path, e))

        return template

    def make_ordered(self, order:TraitCollectionOrder) -> Optional["TraitCollection"]:
        ordered = copy.copy(self)
        order.collection = ordered
        ordered.order = order
        if order.blueprint_template is not None:
            ordered.blueprint_template = order.blueprint_template
        ordered.original = self

        # TODO: more optimized solution?
        ordered.types = [group for group in ordered.types if group.name in order.image_order]
        ordered.collection = [trait for trait in ordered.collection if trait.type_name in [group.name for group in ordered.types]]
        # Sort collection
        ordered.types = sorted(ordered.types, key=lambda g: order.image_order.index(g.name) if g.name in order.image_order else len(order.image_order))

        if order.name_prefix != '':
            ordered.name_prefix = order.name_prefix
        return ordered

    def make_groups(self) -> List[TraitType]:
        """Collect all traits to it associated group"""

        groups:Dict[str, TraitType] = {}
        for trait in self.collection:
            if trait.type_name not in groups:
                groups[trait.type_name] = TraitType(trait.type_name)
            groups[trait.type_name].append(trait)
            
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
        print("\nHealth check:")
        self.check_blueprint_template()
        self.check_duplicate_names()
        self.check_adapted_exists()
        self.check_excluded_exists()
        
    def check_blueprint_template(self) -> None:
        """
        Check if collection has blueprint template
        Order in wich path checked previously on load: TraitOrdererdCollection -> TraitCollection -> args -> blueprint.json from NFT default
        """
        if self.blueprint_template is None:
            print("Critical: collection hasn't got Blueprint Template.")
            exit()

    def check_duplicate_names(self) -> None:
        """Check if trait name not unique over whole collection"""

        for trait in self.collection:
            others = [other for other in self.collection if other.name == trait.name and other != trait]
            if len(others)>0:
                print("Notice: Trait '%s -> %s' has same inner name as:" % (trait.type_name, trait.name), *["'%s -> %s'," % (o.type_name, o.name) for o in others])

    def check_adapted_exists(self) -> None:
        """Check for adapted_to property link to unknow trait name in collection"""

        for trait in self.collection:
            for file in trait.files:
                for adapted in file.adapted_to:
                    if adapted not in [t.name for t in self.collection]:
                        print("Notice: Trait '%s -> %s' adapted to unknown trait name '%s'" % (trait.type_name, trait.name, adapted))

    def check_excluded_exists(self) -> None:
        """Check for exclude property link to unknow trait name in collection"""

        for trait in self.collection:
            for exclude in trait.exclude:
                if exclude not in [t.name for t in self.collection]:
                    print("Notice: Trait '%s -> %s' excluded for unknown trait name '%s'" % (trait.type_name, trait.name, exclude))

class TraitCollectionState():
    """Wrapper around TraitCollection which store selected trait and file per group. 
    Also provide conndition, excludes and adoptions state."""

    def __init__(self, traits:TraitCollection) -> None:
        self.traits:TraitCollection = traits
        self.types:Dict[TraitType,Tuple[Trait, TraitFile]] = {}

        for trait_type in traits.types:
            # TODO: checks
            trait = trait_type.traits[0]
            file = trait.current_file
            self.types[trait_type] = (trait, file)
    
    def current(self, trait_type:TraitType) -> Tuple[Trait, TraitFile]:
        return self.types[trait_type]

    def next(self, trait_type:TraitType, cycle:bool = True) ->Optional[Tuple[Trait, TraitFile]]:
        """Return next file of trait or next trait"""

        trait, file = self.current(trait_type)

        file_indx = trait.files.index(file)
        if file_indx + 1 < len(trait.files):
            file = trait.files[file_indx + 1]
        else:
            trait_index = trait_type.traits.index(trait)
            if trait_index + 1 < len(trait_type.traits):
                trait = trait_type.traits[trait_index + 1]
                file = trait.files[0]
            else:
                if cycle == False:
                    return None
                trait = trait_type.traits[0]
                file = trait.files[0]

        self.types[trait_type] = (trait, file)
        return self.current(trait_type)

    def prev(self, trait_type:TraitType, cycle:bool = True) ->Optional[Tuple[Trait, TraitFile]]:
        """Return previous file of trait or previous trait"""

        trait, file = self.current(trait_type)

        file_indx = trait.files.index(file)
        if file_indx - 1 >= 0:
            file = trait.files[file_indx - 1]
        else:
            trait_index = trait_type.traits.index(trait)
            if trait_index - 1 >= 0:
                trait = trait_type.traits[trait_index - 1]
                file = trait.files[-1]
            else:
                if cycle == False:
                    return None
                trait = trait_type.traits[-1]
                file = trait.files[-1]

        self.types[trait_type] = (trait, file)
        return self.current(trait_type)

    def current_list(self) -> List[Tuple[Trait, TraitFile]]:
        traits:List[Tuple[Trait, TraitFile]] = []
        for group in self.types:
            traits.append(self.types[group])
        return traits

    def conditions(self) -> Dict[Trait,List[Tuple[str,bool]]]:
        """Return adapted_to match or not for current state"""
        match:Dict[Trait,List[Tuple[str,bool]]] = {}
        for group in self.types:
            trait, file = self.types[group]
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
        for group in self.types:
            trait, file = self.types[group]
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
        for group in self.types:
            trait, current_file = self.types[group]
            match[trait] = []
            for file in trait.files:
                if file != current_file and len(file.adapted_to) > 0:
                    for adapted in file.adapted_to:
                        if adapted in [trait.name for trait, file in self.current_list()]:
                            match[trait].append((adapted, True))
        return match

    def groups(self) -> Dict[str, int]:
        """Return Trait count per group for current state"""
        result:Dict[str,int] = {}
        for trait in self.traits:
            # trait, _ = self.types[trait_type]
            for group in trait.groups:
                if group not in result:
                    result[group] = 0
                if trait in [t for t,f in self.current_list()]:
                    result[group]+=1

        return result
    