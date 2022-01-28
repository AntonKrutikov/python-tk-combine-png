import os
import glob
import json
import random
from tkinter.messagebox import NO
from typing import Optional, Tuple, Dict, List
from unicodedata import name
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

    def save(self, blueprint_template) -> Tuple[bool,str]:
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

        self.save_json(blueprint_template)
        self.save_image()

        return True, 'File saved to %s with NFT name: "%s"' % (self.png_path, self.name)

    def save_json(self, blueprint_template) -> None:
        blueprint = blueprint_template.copy()
        blueprint['name'] = self.name
        blueprint['attributes'] = self.attributes
        
        with open(self.json_path, 'w') as outfile:
            json.dump(blueprint, outfile)

    def save_image(self) -> None:
        optimized = self.image.convert('P')
        optimized.save(self.png_min_path)
        self.image.save(self.png_path)


    def unique(self) -> Tuple[bool,str]:
        """Check if NFT with it attributes already exists in list"""
        for nft in NFT.list():
            if len(self.attributes) == len(nft.attributes) and all(a in nft.attributes for a in self.attributes):
                return False, 'NFT with same attributes exists: "%s" in %s' % (nft.name, nft.json_path)
        return True, None

    def delete(self) -> None:
        """Delete NFT files from out folder. file_name used as base pattern."""
        file_list = glob.glob("%s/%s*" % (self.out_path, self.file_name))
        for file in file_list:
            try:
                os.remove(file)
            except:
                print("Error while deleting file : ", file)

    def rename(self, new_file_name:str, name_prefix:str = None) -> None:
        # Order matter, because while update json we change file_name attribute
        self.rename_image(new_file_name)
        self.rename_min_image(new_file_name)
        self.rename_json(new_file_name, name_prefix)
   

    def rename_json(self, new_file_name:str, name_prefix:str = None) -> None:
        path= ("%s/%s.json" % (self.out_path, self.file_name))
        # TODO: for now we use name prefix as splited json name by #
        if name_prefix is None:
            name_prefix = self.name_prefix
        try:
            os.remove(path)
            self.file_name = new_file_name
            self.name = "%s%s" % (name_prefix, new_file_name)
            self.save_json()
        except:
            print("Error: can't rename json file: %s", path)


    def rename_image(self, new_file_name:str) -> None:
        path= self.png_path
        new_path = "%s/%s.png" % (self.out_path, new_file_name)
        try:
            os.rename(path, new_path)
        except Exception as e:
            print("Error while renaming file: ", path, e)

    def rename_min_image(self, new_file_name:str) -> None:
        path= self.png_min_path
        new_path = "%s/%s.min.png" % (self.out_path, new_file_name)
        try:
            os.rename(path, new_path)
        except:
            print("Error while renaming file: ", path)

    @classmethod
    def parse_name_prefix(cls, name) -> str:
        """Try to get collection name_prefix from nft.name"""
        parts = name.rsplit('#', 1)
        if len(parts) > 0:
            return '%s#' % parts[0]
        else:
            return ''

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
                    nft.name_prefix = cls.parse_name_prefix(nft.name)
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
        """Load blueprint template once and store it as class variable. This used as default blueprint."""

        if cls.blueprint_template is None:
            if path is None:
                path = cls.blueprint_path
            try:
                with open(path) as json_file:
                    cls.blueprint_template = json.load(json_file)  
            except Exception as e:
                print('Warning: Failed to load default Blueprint Template "%s". Message: %s' % (path, e))

    @classmethod
    def list(cls) -> List["NFT"]:
        """Returns all files from out_path as NFT instance"""

        nft_list:List["NFT"] = []

        files = [f.split('.')[0] for f in os.listdir(cls.out_path) if f.endswith('.json')]

        ordered = sorted(files, key=lambda x:int(x) if x.isdigit() else -1, reverse=False)
        for item in ordered:
            nft = NFT.load(item)
            if nft is not None:
                nft_list.append(nft)
        
        return nft_list

    @classmethod
    def next_file_index(cls) -> str:
        """Returns next numeric name for files in out_path"""

        return str(max((int(nft.file_name) for nft in cls.list() if nft.file_name.isdigit()), default=0) + 1)

    @classmethod
    def repair(cls, name_prefix:str = None) -> List["NFT"]:
        """
        Rename nft files to fill missing indexes, also change name attribute in json file.
        If name_prefix not provided - try to take name_prefix from last NFT in collection
        """
        ordered = sorted(cls.list(),key=lambda n: n.file_name)
        if name_prefix is None and len(ordered) > 0:
            name_prefix = ordered[-1].name_prefix
        for i,nft in enumerate(ordered):
            nft.rename(i+1, name_prefix)
        return cls.list()

    @classmethod
    def shuffle_names(cls) -> List["NFT"]:
        """
        Shuffle names in NFT resulting collection by random order, keep file names same.
        Collection is repaired before.
        """

        collection = cls.repair()
        names = [nft.name for nft in collection]
        random.shuffle(names)
        for i,nft in enumerate(collection):
            nft.name = names[i]
            nft.save_json()
        
        collection.sort(key=lambda nft: nft.file_name)
        return collection
    
    @classmethod
    def shuffle(cls) -> List["NFT"]:
        """
        Shuffle names and file names in NFT resulting collection by random order.
        Collection is repaired before.
        Use temporary renaming to underscored names to avoid file override, because we only rename, not load/save with images.
        """

        collection = cls.repair()
        names = [nft.file_name for nft in collection].copy()
        random.shuffle(names)
        for i,nft in enumerate(collection):
            # Rename to temp files to exclude conflicts (one file can overwrite another)
            # respects nft name and filename
            nft.rename("_%s" % names[i])
        
        #fix names to not temporary
        for nft in collection:
            nft.rename(nft.file_name[1:])

        collection.sort(key=lambda nft: nft.file_name)
        return collection