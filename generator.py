import argparse
from typing import List,Dict,Tuple
import csv
from trait.collection import TraitCollection, TraitCollectionState
from nft import NFT
from trait.trait import Trait

description="""NFT collection generator

Default input list: collection.csv
    Default name for 1 column is "name" and it used as name field in result json
    Default name for last column is "attribute_number" and it stored in result json if --attribute-name key exists
    All columns between first and last interpreted as traits columns
Default traits description: traits.json
Default out directory: ./out
"""
parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--csv', help='CSV file with list of NFT combination', default='collection.csv')
parser.add_argument('--first-column', help='Name of first column in CSV (used as name)', default='name')
parser.add_argument('--last-column', help='Name of last column in CSV (used as attribute_number)', default='attribute_number')
parser.add_argument('--traits', help='JSON description of traits', default='traits.json')
parser.add_argument('--blueprint', help='JSON template for generating output json file', default='blueprint.json')
parser.add_argument('--out', help='Output folder for results', default='out')
parser.add_argument('--svg-width', help='Default svg width when convert to png, if svg used as background layer', default=1080, type=int)
parser.add_argument('--svg-height', help='Default svg height when convert to png, if svg used as background layer', default=1080, type=int)
parser.add_argument('--use-names', help='Use name column from csv as out filename', action='store_true')
parser.add_argument('--attribute-number', help='Store or not attribute_number column to result json', action='store_true')
parser.add_argument('item', help='Index in input csv file to provide only this result instead of all output', default=None, type=int, nargs='?')

args = parser.parse_args()

class Generator():
    def __init__(self, args:argparse.Namespace) -> None:
        self.args = args

        self.traits = TraitCollection()
        self.traits.load_from_file(args.traits)
       
        
    def load_csv(self) -> List:
        collection:List = []
        with open(args.csv, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            header = None
            traits_name_index = None
            traits_attributes_index = None
            rn = 0
            for row in reader:
                if rn == 0:
                    header = row
                    try:
                        traits_name_index = header.index(args.first_column)
                    except ValueError as err:
                        print("Can't find first column with given name. Please provide column, that will be used as 'name' column and start index")
                        print("ValueError: %s" % err)
                        exit()
                    try:
                        traits_attributes_index = header.index(args.last_column)
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

    def load_nft(self):
        csv = self.load_csv()
        for item in csv:
            broken = False
            broken_messages:List[str] = []
            not_founded:List[Tuple[str,str]] = []

            values = [trait_name for _, trait_name in item['traits'].items()]
            nft = NFT(name=item['name'])
            nft_traits:TraitCollection = TraitCollection()
            for group_name, trait_name in item['traits'].items():
                trait = next((trait for trait in self.traits if trait.name == trait_name and trait.group == group_name), None)
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

            nft_traits.groups = nft_traits.make_groups()
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
                print('Warning: NFT "%s" is broken:' % nft.name)
                for message in broken_messages:
                    print(message)
gen = Generator(args)
gen.load_nft()