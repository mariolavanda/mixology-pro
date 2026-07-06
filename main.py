# --- IMPORTS (mantén los que ya tenías) ---
from fastapi import FastAPI, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models, schemas, database
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import unicodedata
from collections import defaultdict

# --- CONFIGURACIÓN ---
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_db():
    db = database.SessionLocal()
    try: yield db
    finally: db.close()

def normalize_text(text: str) -> str:
    nfkd_form = unicodedata.normalize('NFKD', text.lower().strip())
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

# --- SEGURIDAD ---
ADMIN_SECRET = "ppp2" # Cambia esto por tu contraseña

def verify_admin(x_admin_key: str = Header(None)):
    if x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="No autorizado: Requiere clave de admin")

# --- ENDPOINTS ---

@app.post("/ingredients/", response_model=schemas.Ingredient)
def create_ingredient(ingredient: schemas.IngredientBase, db: Session = Depends(get_db)):
    clean_name = normalize_text(ingredient.name)
    existing = db.query(models.Ingredient).filter(models.Ingredient.name == clean_name).first()
    if existing: return existing
    
    new_ing = models.Ingredient(name=clean_name, category=ingredient.category)
    db.add(new_ing)
    db.commit()
    db.refresh(new_ing)
    return new_ing

@app.get("/ingredients/", response_model=List[schemas.Ingredient])
def get_ingredients(db: Session = Depends(get_db)):
    return db.query(models.Ingredient).all()

# Endpoint para crear recetas (Solo Admin)
@app.post("/recipes/", response_model=schemas.Recipe)
def create_recipe(recipe: schemas.RecipeCreate, db: Session = Depends(get_db), admin: None = Depends(verify_admin)):
    new_recipe = models.Recipe(name=recipe.name, instructions=recipe.instructions)
    ingredients = db.query(models.Ingredient).filter(models.Ingredient.id.in_(recipe.ingredient_ids)).all()
    new_recipe.ingredients = ingredients
    db.add(new_recipe)
    db.commit()
    db.refresh(new_recipe)
    return new_recipe


@app.get("/recipes/filter/")
async def filter_recipes(
    ingredients: list[str] = Query(None), 
    db: Session = Depends(get_db)
):
    if not ingredients:
        return db.query(models.Recipe).all()

    # 1. Agrupamos los ingredientes seleccionados por categoría
    # Esto requiere que el backend sepa a qué categoría pertenece cada ingrediente
    selected_by_cat = defaultdict(list)
    for ing_name in ingredients:
        # Buscamos el ingrediente en la BD para saber su categoría
        ing_obj = db.query(models.Ingredient).filter(models.Ingredient.name == ing_name).first()
        if ing_obj:
            selected_by_cat[ing_obj.category].append(ing_obj.name)

    all_recipes = db.query(models.Recipe).all()
    filtered = []

    for recipe in all_recipes:
        recipe_ings = {i.name for i in recipe.ingredients}
        recipe_cats = {i.category for i in recipe.ingredients}
        
        # 2. Evaluamos categoría por categoría
        keep_recipe = True
        
        # Obtenemos todas las categorías existentes en el sistema
        all_categories = db.query(models.Ingredient.category).distinct()
        
        for cat in all_categories:
            cat_name = cat[0]
            # Si el usuario seleccionó ingredientes de esta categoría...
            if cat_name in selected_by_cat:
                # ...entonces la receta DEBE tener al menos uno de esos ingredientes
                # Si la receta no tiene NADA de esta categoría, la descartamos
                if recipe_cats.isdisjoint({cat_name}): 
                    keep_recipe = False
                    break
                
                # Opcional: si quieres que tenga Específicamente uno de los marcados:
                if recipe_ings.isdisjoint(selected_by_cat[cat_name]):
                    keep_recipe = False
                    break

        if keep_recipe:
            filtered.append(recipe)
            
    return filtered

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root(): return FileResponse("static/index.html")

@app.get("/recipes/", response_model=List[schemas.Recipe])
def get_all_recipes(db: Session = Depends(get_db)):
    return db.query(models.Recipe).all()

# Eliminar una receta
@app.delete("/recipes/{recipe_id}")
async def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if recipe:
        db.delete(recipe)
        db.commit()
        return {"message": "Receta eliminada correctamente"}
    return {"error": "Receta no encontrada"}

# Actualizar una receta
@app.put("/recipes/{recipe_id}")
async def update_recipe(recipe_id: int, recipe_data: dict, db: Session = Depends(get_db)):
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if recipe:
        recipe.name = recipe_data.get("name", recipe.name)
        recipe.instructions = recipe_data.get("instructions", recipe.instructions)
        db.commit()
        return {"message": "Receta actualizada"}
    return {"error": "Receta no encontrada"}