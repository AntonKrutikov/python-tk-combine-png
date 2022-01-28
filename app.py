
import argparse
from merge import Merge
from viewer import Viewer
from editor import Editor
from typing import Optional, List
from nft import NFT
from trait.collection import TraitCollection, TraitCollectionState

description="""NFT manual generator

Compare your png or svg images to resulting NFT
"""
parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--svg-width', help='Default svg width when convert to png, if svg used as background layer', default=1080, type=int)
parser.add_argument('--svg-height', help='Default svg height when convert to png, if svg used as background layer', default=1080, type=int)
parser.add_argument('--blueprint', help='JSON template for generating output json file', default='blueprint.json')
parser.add_argument('--viewer', help='Starts in viewer mode', nargs='?', const=-1, default=None)
parser.add_argument('--nft-name-prefix', help='Prefix for NFT name in result json', default='NFT #')
parser.add_argument('--collection-id', help='Id of ordered collection from "_collections" attribute of traits. 0 - default not ordered,', default=0, type=int)
parser.add_argument('--generate-csv-index', help='Flag indicate to generate all possible valid combinations to provided csv file', default=None)
args = parser.parse_args()

NFT.name_prefix = args.nft_name_prefix
NFT.load_blueprint(args.blueprint)

def colored(text, r, g, b):
    return "\033[38;2;{};{};{}m{}\033[0m".format(r, g, b, text)

class App:
    blueprint_template: dict
    traits: list
    viewer_instance: Optional[Viewer] = None

    def __init__(self, args) -> None:
        self.args = args
       
    def show_editor(self, collection_list:List[TraitCollection], collection_index:int, merge:Merge):
        self.editor = Editor(collection_list, collection_index, merge)
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

app = App(args)
if args.viewer:
    viewer = app.show_viewer()
    viewer.show_item_by_file_name(args.viewer)
    viewer.mainloop()
else:
    collection_list = TraitCollection.load_from_file('traits.json')
    print('\nFound %s collection(s) in "traits.json"\n' % len(collection_list))

    if args.collection_id < 0 or args.collection_id >= len(collection_list):
        print('%s: No collection in "traits.json" with index "%s"' % (colored('Error', 255, 0, 0), args.collection_id))
        exit()

    print('Using collection with index = %s' % args.collection_id)

    if not collection_list[args.collection_id].is_valid():
        exit()
    # generate csv index
    if args.generate_csv_index is not None:
        state = TraitCollectionState(collection_list[args.collection_id])
        state.valid_combinations_to_csv(args.generate_csv_index)
    merge = Merge(args.svg_width, args.svg_height)
    app.show_editor(collection_list, args.collection_id, merge)