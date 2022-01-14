import os
import json
from typing import Optional, Tuple, Dict, List
from PIL.Image import Image

class NFT():
    out_path:str = './out'
    blueprint_path:str = 'blueprint.json'
    blueprint_template:dict = None
    name_prefix:str = ''

    def __init__(self, file_name:str = None, name:str = None, image:Image = None, attributes:List[Dict[str,str]] = []) -> None:
        self.file_name:str = file_name
        self.name:str = name
        self.image:Image = image
        self.attributes:List[Dict[str,str]] = attributes

    @property
    def json_path(self) -> str:
        return "%s/%s.json" % (self.out_path, self.file_name)

    @property
    def png_path(self) -> str:
        return "%s/%s.png" % (self.out_path, self.file_name)

    @property
    def png_min_path(self) -> str:
        return "%s/%s.min.png" % (self.out_path, self.file_name)

    def save(self) -> Tuple[bool,str]:
        if len(self.attributes) == 0:
            return False, "Error: can't save NFT with empty attributes"
        unique, msg = self.unique()
        if not unique:
            return False, msg
        if self.file_name is None:
            self.file_name = NFT.next_file_index()
        if self.name is None:
            self.name = "%s%s" % (self.name_prefix, self.file_name)
        if self.image is None:
            return False, "Error: saving NFT without image"

        blueprint = self.blueprint_template.copy()
        blueprint['name'] = self.name
        blueprint['attributes'] = self.attributes
        
        with open(self.json_path, 'w') as outfile:
            json.dump(blueprint, outfile)

        self.image.save(self.png_path)

        optimized = self.image.convert('P')
        optimized.save(self.png_min_path)

        return True, 'File saved to %s with NFT name: "%s"' % (self.png_path, self.name)

    def unique(self) -> Tuple[bool,str]:
        """Check if NFT with it attributes already exists in list"""
        for nft in NFT.list():
            if len(self.attributes) == len(nft.attributes) and all(a in nft.attributes for a in self.attributes):
                return False, 'NFT with same attributes exists: "%s" in %s' % (nft.name, nft.json_path)
        return True, None

    @classmethod
    def load(cls, file_name:str) -> Optional["NFT"]:
        """Detect json and png file by name and return NFT intance"""

        desc_path = "%s/%s.json" % (cls.out_path, file_name)
        png_path = "%s/%s.png" % (cls.out_path, file_name)

        if not os.path.isfile(desc_path):
            print("Error: Load NFT failed - %s file not found" % desc_path)
            return None
        if not os.path.isfile(png_path):
            print("Error: Load NFT failed - %s file not found" % png_path)
            return None

        nft = NFT(file_name=file_name, attributes=[])

        with open(desc_path) as json_file:
            try:
                parsed = json.load(json_file)

                # name
                if 'name' in parsed:
                    nft.name = parsed['name']
                else:
                    print('Notice: no nft name in %s' % desc_path)
                
                # attributes
                if 'attributes' in parsed and isinstance(parsed['attributes'],list):
                    nft.attributes = parsed['attributes']

            except Exception as e:
                print("Error: parsing %s Message: %s" % (desc_path, e))
        
        return nft

    @classmethod
    def load_blueprint(cls, path:str = None):
        """Load blueprint template once and store it as class variable"""

        if cls.blueprint_template is None:
            if path is None:
                path = cls.blueprint_path
            with open(path) as json_file:
                try:
                    cls.blueprint_template = json.load(json_file)  
                except Exception as e:
                    print('Error: Failed to load %s. Message: %s' % (path, e))

    @classmethod
    def list(cls) -> List["NFT"]:
        """Returns all files from out_path as NFT instance"""

        nft_list:List["NFT"] = []

        files = [f.split('.')[0] for f in os.listdir(cls.out_path) if f.endswith('.json')]

        ordered = sorted(files, key=lambda x:int(x) if x.isdigit() else -1, reverse=True)
        for item in ordered:
            nft = NFT.load(item)
            if nft is not None:
                nft_list.append(nft)
        
        return nft_list

    @classmethod
    def next_file_index(cls) -> str:
        """Returns next numeric name for files in out_path"""

        return str(max((int(nft.file_name) for nft in cls.list() if nft.file_name.isdigit()), default=0) + 1)

# preload template on import
NFT.load_blueprint()