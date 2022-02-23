import os
from typing import Union, List

class TraitFile():
    """
    Represent paths for one file variant of Trait
    """
    def __init__(self) -> None:
        self.paths:List[str] = []
        self.adapted_to:List[str] = []

    def load(self, path: Union[str,list,dict]) -> bool:
        if isinstance(path, str):
            self.load_from_str(path)
        if isinstance(path, list):
            self.load_from_list(path)
        if isinstance(path, dict):
            self.load_from_dict(path)
        
        if len(self.paths) > 0:
            return True
        return False

    def exists(self, path: str) -> bool:
        if os.path.isfile(path):
            return True
        else:
            print("Warning in loading TraitFile: path %s is not exists" % path)
            return False

    def load_from_str(self, path: str) -> None:
        if self.exists(path):
            self.paths.append(path)

    def load_from_dict(self, path_dict: dict) -> None:
        if 'path' in path_dict:
            path = path_dict['path']
            if isinstance(path, str):
                self.load_from_str(path)
            if isinstance(path, list):
                self.load_from_list(path)
        if 'adapted-to' in path_dict:
            adapted_to = path_dict['adapted-to']
            if isinstance(adapted_to, list):
                for a in adapted_to:
                    if isinstance(a, str):
                        self.adapted_to.append(a)


    def load_from_list(self, path_list: list) -> None:
        for path in path_list:
            if isinstance(path, str):
                self.load_from_str(path)
            if isinstance(path, dict):
                self.load_from_dict(path)
