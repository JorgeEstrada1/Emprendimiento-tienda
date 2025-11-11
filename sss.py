import json
import os

PRODUCTS_FILE = "productos.json"

def load_products():
    """Carga la lista de productos desde productos.json."""
    if not os.path.exists(PRODUCTS_FILE):
        print("⚠️ No se encontró productos.json, devolviendo lista vacía.")
        return []

    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"⚠️ Error cargando {PRODUCTS_FILE}:", e)
        return []

def get_products(keyword: str = ""):
    """
    Devuelve la lista de productos.
    Si keyword no está vacío, filtra por nombre que contenga ese texto (insensible a mayúsculas).
    """
    productos = load_products()

    if not keyword:
        return productos

    k = keyword.lower()
    filtrados = [p for p in productos if k in p.get("name", "").lower()]

    return filtrados

def get_product_by_id(product_id: int):
    """
    Encuentra y devuelve un solo producto por su ID.
    Devuelve None si no lo encuentra.
    """
    productos = load_products()
    
    for p in productos:
        if p.get("id") == product_id:
            return p
    
    return None

def save_products(products_list):
    """
    Recibe una lista de productos y la escribe en productos.json.
    """
    try:
        with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
            json.dump(products_list, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error fatal guardando {PRODUCTS_FILE}:", e)

def add_product(new_product_data):
    """
    Añade un nuevo producto al JSON.
    """
    productos = load_products()
    
    if not productos:
        new_id = 1
    else:
        new_id = max(p.get("id", 0) for p in productos) + 1
        
    new_product_data["id"] = new_id
    productos.append(new_product_data)
    save_products(productos)

def get_all_categories():
    """
    Carga todos los productos y devuelve una lista de categorías únicas.
    """
    productos = load_products()
    categories_set = set()
    for p in productos:
        if p.get("category"):
            categories_set.add(p["category"].strip())
    return sorted(list(categories_set))

# --- INICIO DE NUEVAS FUNCIONES DE ADMIN ---

def update_product_by_id(product_id: int, updated_data: dict):
    """
    Encuentra un producto por su ID y actualiza sus datos.
    """
    productos = load_products()
    product_found = False
    
    # Creamos una *nueva* lista con los datos actualizados
    productos_actualizados = []
    for p in productos:
        if p.get("id") == product_id:
            # Encontramos el producto. Conservamos su ID.
            updated_data["id"] = product_id 
            # Reemplazamos el producto 'p' viejo por 'updated_data' nuevo
            productos_actualizados.append(updated_data)
            product_found = True
        else:
            # Este no es, lo añadimos a la lista sin cambiarlo
            productos_actualizados.append(p)
            
    # Guardamos la lista nueva en el archivo JSON
    if product_found:
        save_products(productos_actualizados)
        
    return product_found


def delete_product_by_id(product_id: int):
    """
    Encuentra un producto por su ID y lo elimina de la lista.
    """
    productos = load_products()
    product_found = False
    
    # Creamos una *nueva* lista que excluye el producto a eliminar
    productos_actualizados = []
    for p in productos:
        if p.get("id") == product_id:
            # Este es el que hay que borrar. Simplemente NO lo añadimos a la lista.
            product_found = True
        else:
            # Este no es, lo conservamos.
            productos_actualizados.append(p)
            
    # Guardamos la lista nueva (sin el producto eliminado) en el JSON
    if product_found:
        save_products(productos_actualizados)
        
    return product_found
# --- FIN DE NUEVAS FUNCIONES DE ADMIN ---