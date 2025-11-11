import json
import os
from app import app, db, Product  # Importamos la app, la DB y el Modelo

# Este script ahora leerá la variable de entorno 'DATABASE_URL'
# exactamente igual que lo hace app.py
# Así, cuando lo corramos en Render, sabrá conectarse a la DB correcta.

JSON_FILE = 'productos.json' # Asegúrate de tener este archivo aún

def migrate_data():
    if not os.path.exists(JSON_FILE):
        print(f"Error: No se encontró el archivo '{JSON_FILE}'.")
        print("Necesitas el JSON original para hacer la migración.")
        return

    print(f"Iniciando migración desde {JSON_FILE} a la base de datos...")

    with app.app_context():
        # 1. Cargar datos del JSON
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                productos_json = json.load(f)
            print(f"Se encontraron {len(productos_json)} productos en el JSON.")
        except Exception as e:
            print(f"Error leyendo {JSON_FILE}: {e}")
            return
        
        # 2. Borramos todo lo que haya en la base de datos (para evitar duplicados)
        print("Borrando datos antiguos de la base de datos...")
        db.session.query(Product).delete()
        
        # 3. Recorremos el JSON y creamos objetos 'Product'
        nuevos_productos = []
        for p in productos_json:
            nuevo = Product(
                name=p.get('name'),
                price=p.get('price'),
                description=p.get('description'),
                source=p.get('source'),
                type=p.get('type'),
                category=p.get('category'),
                image=p.get('image'),
                product_url=p.get('product_url'),
                eta=p.get('eta')
            )
            nuevos_productos.append(nuevo)
        
        # 4. Añadimos todos los productos nuevos
        db.session.bulk_save_objects(nuevos_productos)
        
        # 5. ¡Guardamos los cambios!
        db.session.commit()

    print("\n¡MIGRACIÓN COMPLETADA!")
    print(f"Se han añadido {len(nuevos_productos)} productos a la base de datos.")
    print("Ahora puedes borrar 'productos.json' y 'migracion.py' de tu proyecto si lo deseas.")

if __name__ == "__main__":
    migrate_data()