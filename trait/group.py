from trait.trait import Trait
from typing import List

class TraitGroup():
    """Represent all Traits per group"""
    
    def __init__(self, name:str) -> None:
        self.name:str = name
        self.traits:List[Trait] = []

    def __len__(self) -> int:
        return len(self.traits)

    def append(self, trait:Trait) -> None:
        self.traits.append(trait)
