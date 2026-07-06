from pydantic import BaseModel
from typing import List, Optional, Any

# --- Esquemas de Usuario ---
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

# --- Esquemas de Ingredientes ---
class IngredientBase(BaseModel):
    name: str
    category: Optional[str] = None 

class Ingredient(IngredientBase):
    id: int
    class Config:
        from_attributes = True

# --- Esquemas de Recetas ---
class RecipeBase(BaseModel):
    name: str
    instructions: str

class RecipeCreate(RecipeBase):
    ingredient_ids: List[int]

class Recipe(RecipeBase):
    id: int
    ingredients: List[Ingredient] = []
    class Config:
        from_attributes = True