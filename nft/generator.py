import argparse
import csv

from tqdm import tqdm
from typing import List,Dict,Tuple

from nft.collection import TraitCollection, TraitCollectionState
from nft.nft import NFT
from nft.trait import Trait
from nft.merge import Merge

def colored(text, r, g, b):
    return "\033[38;2;{};{};{}m{}\033[0m".format(r, g, b, text)

class Generator():
    def __init__(self, args, merge:Merge) -> None:
        self.args = args

        collection_list = TraitCollection.load_from_file(args.traits)
        if args.collection_id < 0 or args.collection_id >= len(collection_list):
            print('%s: No collection in "traits.json" with index "%s"' % (colored('Error', 255, 0, 0), args.collection_id))
            exit()

        self.collection_list = collection_list
        self.collection = collection_list[args.collection_id]

        self.merge = merge
       
        
    def load_csv(self) -> List:
        collection:List = []
        with open(self.args.csv, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            header = None
            traits_name_index = None
            traits_attributes_index = None
            rn = 0
            for row in reader:
                if rn == 0:
                    header = row
                    try:
                        traits_name_index = header.index(self.args.first_column)
                    except ValueError as err:
                        print("Can't find first column with given name. Please provide column, that will be used as 'name' column and start index")
                        print("ValueError: %s" % err)
                        exit()
                    try:
                        traits_attributes_index = header.index(self.args.last_column)
                    except ValueError as err:
                        print("Can't find last column with given name. Please provide column, that will be used as 'attribute_number' column and end index")
                        print("ValueError: %s" % err)
                        exit()
                    rn+=1
                else:
                    item = {}
                    item['name'] = row[traits_name_index]
                    item['attribute-number'] = row[traits_attributes_index]
                    item['traits'] = dict(zip(header[traits_name_index+1:traits_attributes_index],row[traits_name_index+1:traits_attributes_index])) #obtain all columns between name and attribute_number
                    collection.append(item)
        return collection

    def generate(self):
        errors:Dict[NFT,List[str]] = {}
        csv = self.load_csv()
        if self.args.item is not None:
            csv = [csv[self.args.item - 1]]
        saved = 0
        with tqdm(total=len(csv)) as pbar:
            for item in csv:
                broken = False
                broken_messages:List[str] = []
                not_founded:List[Tuple[str,str]] = []

                values = [trait_name for _, trait_name in item['traits'].items()]
                nft = NFT(name=item['name'])
                nft_traits:TraitCollection = TraitCollection()
                for group_name, trait_name in item['traits'].items():
                    trait = next((trait for trait in self.collection if trait.name == trait_name and trait.type_name == group_name), None)
                    if trait is not None:
                        nft_traits.collection.append(trait)
                    if trait is None and trait_name != '':
                        not_founded.append((group_name, trait_name))
                        broken = True
                        continue

                if broken == True:
                    broken_messages.append('\tTrait(s) not found in collection: [%s]' % ','.join('"%s" -> "%s"' % (group_name, trait_name) for group_name, trait_name in not_founded))

                # Try to find adapted version of each trait file for current trait set. Get first matched or leave unchanged.
                for trait in nft_traits.collection:
                    for file_indx, file in enumerate(trait.files):
                        for adapt in file.adapted_to:
                            if adapt in values:
                                trait.current_file = file
                                trait.current_file_index = file_indx
                                break

                nft_traits.types = nft_traits.make_groups()
                state = TraitCollectionState(nft_traits)

                excludes = state.excludes(matched_only=True)
                if len(excludes) > 0:
                    broken = True
                    for trait, exclude in excludes.items():
                        broken_messages.append('\tTrait "%s" excluded because next trait value(s) exists in collection: [%s]' % (trait.name, ','.join('"%s"' % name for name,_ in exclude)))

                conditions = state.conditions()
                broken_conditions:Dict[Trait,List[str,bool]] = {}
                for trait, condition in conditions.items():
                    if all(not ok for name,ok in condition):
                        if trait not in broken_conditions:
                            broken_conditions[trait] = condition
                if len(broken_conditions) > 0:
                    broken = True
                    for trait, condition in broken_conditions.items():
                        broken_messages.append('\tTrait %s not match any adapted_to condition: [%s]' % (trait.name, ','.join('"%s"' % name for name,_ in condition)))

                if broken == True:
                    errors[nft] = broken_messages
                else:
                    attributes = []
                    order = state.collection.order.json_order
                    for json_group in order:
                        for group in state.current_state:
                            if group.name == json_group:
                                trait, _ = state.current(group)
                                attributes.append({"trait_type": group.name, "value": trait.name})
                    nft.attributes = attributes
                    nft.image = self.merge.combine(state)
                    if self.args.use_names == True:
                        nft.file_name = nft.name
                    if state.collection.name_prefix != '':
                        nft.name_prefix = state.collection.name_prefix
                    # Add groups count to attributes too
                    for group, count in state.groups().items():
                        attributes.append({"group": group, "value": count})
                    ok, err = nft.save(self.collection.blueprint_template)
                    if not ok:
                        errors[nft] = ['\t%s' % err]
                    else:
                        saved += 1
                pbar.update(1)

        print("Successfully saved %s/%s item(s)" % (saved, len(csv)))

        for nft in errors:
            print('%s: NFT "%s" is broken and not saved:' % (colored('Warning', 255, 0, 0), nft.name))
            for message in errors[nft]:
                print(message)