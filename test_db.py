# Crea este pequeño archivo temporalmente llamado test_db.py y ejecútalo
from database import engine, Base
import models

Base.metadata.create_all(bind=engine)
print("¡Base de datos creada con éxito!")