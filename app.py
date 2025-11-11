from flask import Flask, render_template, request, abort, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
import time
from werkzeug.utils import secure_filename

# --- CONFIGURACIÓN ---
app = Flask(__name__)
# Esta es la ruta base de nuestro proyecto
basedir = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads') # Ruta completa a la carpeta de subidas
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ADMIN_PASSWORD = 'unimarket123' # ¡¡¡CAMBIA ESTA CONTRASEÑA!!!

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.urandom(24)

# --- INICIO: CONFIGURACIÓN DE BASE DE DATOS (SQLite) ---
# Esta es la configuración universal para SQLite.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
# --- FIN: CONFIGURACIÓN DE BASE DE DATOS ---


# --- INICIO: EL "MODELO" DE PRODUCTO ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(300), nullable=False)
    product_url = db.Column(db.String(500), nullable=True)
    eta = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Product {self.name}>'
# --- FIN: EL "MODELO" DE PRODUCTO ---


# --- Funciones de Ayuda ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_image_upload(request_files, producto=None):
    """
    Maneja la subida de un archivo de imagen.
    Devuelve la URL *relativa* de la imagen guardada.
    """
    if 'image_file' not in request_files:
        flash("No se encontró la parte del archivo (image_file).", "danger")
        return None
        
    file = request_files['image_file']

    if file.filename == '':
        # Si no se selecciona archivo, revisa si es una edición
        if producto and producto.image:
            return producto.image # Devolvemos la imagen antigua
        else:
            flash("Debes seleccionar un archivo de imagen.", "danger")
            return None # Error si es un producto nuevo sin imagen

    if file and allowed_file(file.filename):
        clean_filename = secure_filename(file.filename)
        unique_filename = f"{int(time.time())}_{clean_filename}"
        
        # Asegurarnos que la carpeta 'static/uploads' exista
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # La ruta completa donde se guardará el archivo
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        file.save(save_path)
        
        # Guardamos la ruta *relativa* en la base de datos
        # ej: /static/uploads/12345_mi_reloj.jpg
        return f"/static/uploads/{unique_filename}"
    else:
        flash("Extensión de archivo no permitida. Solo se aceptan: png, jpg, jpeg, gif, webp.", "danger")
        return None

# --- RUTAS PÚBLICAS (CLIENTES) ---
@app.context_processor
def inject_cart_count():
    cart = session.get('cart', {})
    count = sum(cart.values())
    return dict(cart_count=count)


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    
    if q:
        products = Product.query.filter(Product.name.ilike(f'%{q}%')).all()
    else:
        products = Product.query.all()
        
    categories_query = db.session.query(Product.category).distinct().all()
    categories = sorted([c[0] for c in categories_query if c[0]])

    return render_template("index.html", products=products, query=q, categories=categories)


@app.route("/producto/<int:product_id>")
def producto_detalle(product_id):
    producto = Product.query.get_or_404(product_id)
    return render_template("producto.html", producto=producto)


@app.route("/carrito")
def cart_page():
    cart_data = session.get('cart', {})
    if not cart_data:
        return render_template("cart.html", cart_items=[], total_price=0)

    cart_items = []
    total_price = 0
    
    for product_id_str, quantity in cart_data.items():
        try:
            product_id = int(product_id_str)
            producto = Product.query.get(product_id)
            
            if producto:
                subtotal = producto.price * quantity
                cart_items.append({
                    "product": producto,
                    "quantity": quantity,
                    "subtotal": subtotal
                })
                total_price += subtotal
        except (ValueError, TypeError):
            print(f"Error: ID de producto inválido en el carrito: {product_id_str}")
            
    return render_template("cart.html", cart_items=cart_items, total_price=total_price)


@app.route("/add-to-cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    product_id_str = str(product_id)
    cart = session.get('cart', {})
    cart[product_id_str] = cart.get(product_id_str, 0) + 1
    session['cart'] = cart
    producto = Product.query.get(product_id)
    if producto:
        flash(f"¡Añadido! '{producto.name}' está en tu carrito.", 'success')
    return redirect(request.referrer or url_for('index'))


@app.route("/remove-from-cart/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    product_id_str = str(product_id)
    cart = session.get('cart', {})
    if product_id_str in cart:
        del cart[product_id_str]
    session['cart'] = cart
    return redirect(url_for('cart_page'))


@app.route("/cart/increase/<int:product_id>", methods=["POST"])
def cart_increase(product_id):
    product_id_str = str(product_id)
    cart = session.get('cart', {})
    if product_id_str in cart:
        cart[product_id_str] += 1
        session['cart'] = cart
    return redirect(url_for('cart_page'))

@app.route("/cart/decrease/<int:product_id>", methods=["POST"])
def cart_decrease(product_id):
    product_id_str = str(product_id)
    cart = session.get('cart', {})
    if product_id_str in cart:
        if cart[product_id_str] <= 1:
            del cart[product_id_str]
        else:
            cart[product_id_str] -= 1
        session['cart'] = cart
    return redirect(url_for('cart_page'))

# --- RUTAS DE ADMIN ---

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if 'admin_logged_in' in session:
        all_products = Product.query.order_by(Product.id.desc()).all()
        return render_template("admin.html", products=all_products)
        
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash("¡Bienvenido, jefe! Sesión iniciada.", "success")
            return redirect(url_for('admin_panel'))
        else:
            flash("Contraseña incorrecta. Intenta de nuevo.", "danger")
    return render_template("admin.html")


@app.route("/admin/add", methods=["POST"])
def admin_add_product():
    if 'admin_logged_in' not in session:
        abort(403)
    try:
        image_url = handle_image_upload(request.files)
        if image_url is None: 
             return redirect(url_for('admin_panel'))

        new_product = Product(
            name=request.form.get("name"),
            price=float(request.form.get("price")),
            description=request.form.get("description"),
            source=request.form.get("source"),
            type=request.form.get("type"),
            category=request.form.get("category"),
            image=image_url,
            product_url=request.form.get("product_url", ""),
            eta=request.form.get("eta")
        )
        
        if not new_product.name or not new_product.price:
             flash("El Nombre y el Precio son obligatorios.", "danger")
             return redirect(url_for('admin_panel'))
             
        db.session.add(new_product)
        db.session.commit()
        
        flash(f"¡Producto '{new_product.name}' añadido con éxito!", "success")
        
    except ValueError:
        flash("Error: El precio debe ser un número (ej: 150.50).", "danger")
    except Exception as e:
        flash(f"Error inesperado: {e}", "danger")
        
    return redirect(url_for('admin_panel'))


@app.route("/admin/edit/<int:product_id>", methods=["GET", "POST"])
def admin_edit_product(product_id):
    if 'admin_logged_in' not in session:
        abort(403)
    producto = Product.query.get_or_404(product_id)

    if request.method == "POST":
        try:
            image_url = handle_image_upload(request.files, producto=producto)
            if image_url is None:
                return redirect(url_for('admin_edit_product', product_id=product_id))
            
            producto.name = request.form.get("name")
            producto.price = float(request.form.get("price"))
            producto.description = request.form.get("description")
            producto.source = request.form.get("source")
            producto.type = request.form.get("type")
            producto.category = request.form.get("category")
            producto.image = image_url # Asigna la imagen nueva o la antigua
            producto.product_url = request.form.get("product_url", "")
            producto.eta = request.form.get("eta")
            
            db.session.commit()
            
            flash(f"¡Producto '{producto.name}' actualizado con éxito!", "success")
            return redirect(url_for('admin_panel'))

        except ValueError:
            flash("Error: El precio debe ser un número.", "danger")
        except Exception as e:
            flash(f"Error inesperado: {e}", "danger")
        
        return redirect(url_for('admin_edit_product', product_id=product_id))

    return render_template("admin_edit.html", producto=producto)


@app.route("/admin/delete/<int:product_id>", methods=["POST"])
def admin_delete_product(product_id):
    if 'admin_logged_in' not in session:
        abort(403)
    producto = Product.query.get_or_404(product_id)
    
    try:
        product_name = producto.name
        
        # Opcional: Borrar el archivo de imagen del disco
        if producto.image:
            image_path = os.path.join(basedir, producto.image.lstrip('/'))
            if os.path.exists(image_path):
                os.remove(image_path)
                
        db.session.delete(producto)
        db.session.commit()
        flash(f"Producto '{product_name}' eliminado con éxito.", "success")
    except Exception as e:
        flash(f"Error al eliminar: {e}", "danger")
        
    return redirect(url_for('admin_panel'))

@app.route("/admin/logout")
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("Has cerrado sesión.", "info")
    return redirect(url_for('index'))


# Este bloque SÍ es necesario para crear la base de datos la PRIMERA VEZ
# Ejecútalo en tu PC con 'python app.py' ANTES de subirlo a GitHub
if __name__ == "__main__":
    with app.app_context():
        db_path = os.path.join(basedir, 'database.db')
        if not os.path.exists(db_path):
            print("Creando la base de datos (database.db)...")
            db.create_all()
            print("¡Base de datos creada!")
        else:
            print("La base de datos ya existe.")
    
    app.run(debug=True)