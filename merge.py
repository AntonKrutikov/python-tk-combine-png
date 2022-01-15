from io import BytesIO
from typing import Optional
from PIL import Image
from cairosvg import svg2png
from trait.collection import TraitCollectionState

class Merge():
    """Merge all images from TraitCollectionState into 1 resulting image"""
    
    def __init__(self, svg_width:int = 1080, svg_height:int = 1080) -> None:
        self.svg_width = svg_width
        self.svg_height = svg_height

    def load(self, file:str) -> Image.Image:
        """Open image or svg file and returns Image instance"""
        if file.endswith('.svg'):
            new_bites = svg2png(file_obj=open(file, "rb"), unsafe=True, write_to=None, scale=1, output_width=self.svg_width, output_height=self.svg_height)
            return Image.open(BytesIO(new_bites)).convert('RGBA')
        return Image.open(file).convert('RGBA')

    def combine(self, traits:TraitCollectionState) -> Optional[Image.Image]:
        """Combine resulting Image based on current selected trait and file in each group"""
        result = None
        for group in traits.groups:
                trait, files = traits.current(group)
                for file in files.paths:
                    img = self.load(file)
                    if result == None:
                        result = img
                        self.svg_width = img.width
                        self.svg_height = img.height
                    else:
                        aimg = Image.new('RGBA', result.size)
                        aimg.paste(img, (0,0))
                        result = Image.alpha_composite(result, aimg)

        return result