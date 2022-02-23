import argparse

from typing import Optional, List

from nft.merge import Merge
from nft.viewer import Viewer
from nft.editor import Editor
from nft.nft import NFT
from nft.collection import TraitCollection, TraitCollectionState
from nft.generator import Generator

description="""NFT editor and generator"""
# shared args
shared_parser = argparse.ArgumentParser(add_help=False)
shared_parser.add_argument('--blueprint', help='JSON template for generating output json file', default='blueprint.json')
shared_parser.add_argument('--nft-name-prefix', help='Prefix for NFT name in result json', default='NFT #')
shared_parser.add_argument('--collection-id', '--id', help='Id of ordered collection from "_collections" attribute of traits. 0 - default not ordered,', default=0, type=int)
shared_parser.add_argument('--svg-width', help='Default svg width when convert to png, if svg used as background layer', default=1080, type=int)
shared_parser.add_argument('--svg-height', help='Default svg height when convert to png, if svg used as background layer', default=1080, type=int)
shared_parser.add_argument('--traits', help='JSON description of traits', default='traits.json')
shared_parser.add_argument('--skip-invalid', help="skip invalid combinations in manual generator", default=False, action='store_true')
# main
parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[shared_parser])
subparsers = parser.add_subparsers(title="modes", dest="command")

# generator manual (editor)
parser_generator = subparsers.add_parser('nft-gen', help="nft generator mode", parents=[shared_parser])
parser_generator.add_argument('--manual','-m', help="manual generator", default=False, action='store_true')

# generator auto
parser_generator.add_argument('--auto','-a', help="auto generator", default=False, action='store_true')
parser_generator.add_argument('--first-column', help='Name of first column in CSV (used as name)', default='name')
parser_generator.add_argument('--last-column', help='Name of last column in CSV (used as attribute_number)', default='attribute_number')
parser_generator.add_argument('--out', help='Output folder for results', default='out')
parser_generator.add_argument('--use-names', help='Use name column from csv as out filename', action='store_true')
parser_generator.add_argument('--attribute-number', help='Store or not attribute_number column to result json', action='store_true')
parser_generator.add_argument('item', help='Index in input csv file to provide only this result instead of all output', default=None, type=int, nargs='?')
parser_generator.add_argument('--csv', help='CSV file with list of NFT combination', default='collection.csv')

# viewer
parser_viewer = subparsers.add_parser('viewer', help="viewer mode", parents=[shared_parser])
parser_viewer.add_argument('id', nargs='?', const=-1, default=None)

# csv generator
parser_csv = subparsers.add_parser('csv-gen', help="csv generator mode", parents=[shared_parser])
parser_csv.add_argument('--csv', help='Path to output csv file (csv generator mode)', required=True, metavar="path")
parser_csv.add_argument('--size', help='Size of resulting collection (csv generator mode)', default=50, type=int, metavar="size")
parser_csv.add_argument('--weighted', help='Respect trait weights (csv generator mode)', default=False, action='store_true')


def colored(text, r, g, b):
    return "\033[38;2;{};{};{}m{}\033[0m".format(r, g, b, text)

class App:
    blueprint_template: dict
    traits: list
    viewer_instance: Optional[Viewer] = None

    def __init__(self, args) -> None:
        self.args = args
        self.collection_id = args.collection_id
        self.command = args.command
        self.options = {
            "editor_skip_invalid": args.skip_invalid if "skip_invalid" in args else False
        }
       
    def show_editor(self, collection_list:List[TraitCollection], collection_index:int, merge:Merge):
        self.editor = Editor(collection_list, collection_index, merge, skip_invalid=self.options["editor_skip_invalid"])
        self.editor.show_viewer_button.configure(command=self.show_viewer)
        self.editor.mainloop()

    def show_viewer(self):
        if self.viewer_instance == None:
            self.viewer_instance = Viewer()
            self.viewer_instance.protocol("WM_DELETE_WINDOW", self.close_viewer)
            self.viewer_instance.show_item_by_file_name()
        else:
            self.viewer_instance.focus_force()
        return self.viewer_instance

    def close_viewer(self):
        self.viewer_instance.destroy()
        self.viewer_instance = None

    def load_trait_collection(self):
        """Load collection from traits.json by id passed in args"""

        self.collection_list = TraitCollection.load_from_file(self.args.traits)
        print('\nFound %s collection(s) in "traits.json"\n' % len(self.collection_list))

        if self.collection_id < 0 or self.collection_id >= len(self.collection_list):
            print('%s: No collection in "traits.json" with index "%s"' % (colored('Error', 255, 0, 0), self.collection_id))
            exit()

        print('Using collection with index = %s' % self.collection_id)

        if not self.collection_list[self.collection_id].is_valid():
            exit()

        self.collection = self.collection_list[self.collection_id]

        print('Info: using "%s" as blueprint template' % self.collection.blueprint_path)
        print(self.collection.info)
        self.collection.health_check()
    
    def run(self):
        if self.command == 'viewer':
            viewer = self.show_viewer()
            viewer.show_item_by_file_name(self.args.id)
            viewer.mainloop()
        elif self.command == 'csv-gen':
            self.load_trait_collection()
            state = TraitCollectionState(self.collection)
            state.valid_combinations_to_csv(self.args.csv, self.args.size, respect_weights=self.args.weighted)
        elif self.command == 'nft-gen' and self.args.auto == True:
            merge = Merge(svg_height=self.args.svg_height, svg_width=self.args.svg_width)
            generator = Generator(self.args, merge)
            generator.generate()
        elif self.command == None or (self.command == 'nft-gen' and self.args.auto == False):
            self.load_trait_collection()
            merge = Merge(self.args.svg_width, self.args.svg_height)
            self.show_editor(self.collection_list, self.collection_id, merge)


args = parser.parse_args()

NFT.name_prefix = args.nft_name_prefix
NFT.load_blueprint(args.blueprint)

app = App(args)
app.run()
# if args.command == 'viewer':
#     viewer = app.show_viewer()
#     viewer.show_item_by_file_name(args.id)
#     viewer.mainloop()
# else:
#     collection_list = TraitCollection.load_from_file('traits.json')
#     print('\nFound %s collection(s) in "traits.json"\n' % len(collection_list))

#     if args.collection_id < 0 or args.collection_id >= len(collection_list):
#         print('%s: No collection in "traits.json" with index "%s"' % (colored('Error', 255, 0, 0), args.collection_id))
#         exit()

#     print('Using collection with index = %s' % args.collection_id)

#     if not collection_list[args.collection_id].is_valid():
#         exit()

#     collection = collection_list[args.collection_id]
#     # print collection blueprint path, info and healthchek messages
#     print('Info: using "%s" as blueprint template' % collection.blueprint_path)
#     print(collection.info)
#     collection.health_check()
    
#     # csv generatir mode
#     if args.command == 'collection-generator':
#         state = TraitCollectionState(collection)
#         state.valid_combinations_to_csv(args.csv, args.size, respect_weights=args.weighted)
#         exit()
#     # editor mode
#     merge = Merge(args.svg_width, args.svg_height)
#     app.show_editor(collection_list, args.collection_id, merge)