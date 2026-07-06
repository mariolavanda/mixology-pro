from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base

# Tabla intermedia para la relación muchos a muchos
recipe_ingredients = Table(
    'recipe_ingredients',
    Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id')),
    Column('ingredient_id', Integer, ForeignKey('ingredients.id'))
)

class Ingredient(Base):
    __tablename__ = "ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # Ej: "Ron", "Limón"
    category = Column(String) # Ej: "Base", "Mezclador", "Hierba"
    
    # Relación inversa: una lista de recetas que usan este ingrediente
    recipes = relationship("Recipe", secondary=recipe_ingredients, back_populates="ingredients")

class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True) # Ej: "Pisco Sour"
    instructions = Column(String)
    
    # Relación muchos a muchos con ingredientes
    ingredients = relationship("Ingredient", secondary=recipe_ingredients, back_populates="recipes")