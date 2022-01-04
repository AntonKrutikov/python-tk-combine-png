
import argparse
from viewer import Viewer
from editor import Editor

description="""NFT manual generator

Compare your png or svg images to resulting NFT
"""
parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--svg-width', help='Default svg width when convert to png, if svg used as background layer', default=1080, type=int)
parser.add_argument('--svg-height', help='Default svg height when convert to png, if svg used as background layer', default=1080, type=int)
parser.add_argument('--blueprint', help='JSON template for generating output json file', default='blueprint.json')
parser.add_argument('--viewer', help='Starts in viewer mode', nargs='?', const=-1, default=None)
parser.add_argument('--nft-name-prefix', help='Prefix for NFT name in result json', default='NFT #')
args = parser.parse_args()

class App:
    blueprint_template: dict
    traits: list
    viewer_instance: Viewer | None

    def __init__(self, args) -> None:
        self.args = args
       
    def show_editor(self):
        self.editor = Editor(args=self.args)
        self.editor.show_viewer_button.configure(command=self.show_viewer)
        self.editor.mainloop()

    def show_viewer(self):
        self.viewer_instance = Viewer()
        self.viewer_instance.protocol("WM_DELETE_WINDOW", self.close_viewer)
        self.viewer_instance.show_item_by_name(-1)
        return self.viewer_instance

    def close_viewer(self):
        self.viewer_instance.destroy()
        self.viewer_instance = None

app = App(args)
if args.viewer:
    viewer = app.show_viewer()
    viewer.show_item_by_name(args.viewer)
    viewer.mainloop()
else:
    app.show_editor()