from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False, default='Electronics')
    image_url = db.Column(db.String(500), nullable=False, default="https://picsum.photos/seed/default/500/300")
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_ordered = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    shipping_address = db.Column(db.String(200), nullable=False)
    shipping_city = db.Column(db.String(100), nullable=False)
    shipping_state = db.Column(db.String(100), nullable=False)
    shipping_zip = db.Column(db.String(20), nullable=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    category = request.args.get('category', 'All')
    if category == 'All':
        products = Product.query.all()
    else:
        products = Product.query.filter_by(category=category).all()
    
    # Get all unique categories for the filter dropdown
    categories = ['All'] + [cat[0] for cat in db.session.query(Product.category).distinct()]
    
    return render_template('home.html', products=products, categories=categories, current_category=category)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=product_id)
        db.session.add(cart_item)
    db.session.commit()
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:cart_item_id>', methods=['POST'])
@login_required
def remove_from_cart(cart_item_id):
    cart_item = CartItem.query.get_or_404(cart_item_id)
    if cart_item.user_id == current_user.id:
        db.session.delete(cart_item)
        db.session.commit()
    return redirect(url_for('cart'))

@app.route('/checkout')
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty')
        return redirect(url_for('cart'))
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/process_checkout', methods=['POST'])
@login_required
def process_checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty')
        return redirect(url_for('cart'))

    # Create new order
    total_amount = sum(item.product.price * item.quantity for item in cart_items)
    order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        shipping_address=request.form['address'],
        shipping_city=request.form['city'],
        shipping_state=request.form['state'],
        shipping_zip=request.form['zip']
    )
    db.session.add(order)

    # Create order items
    for cart_item in cart_items:
        order_item = OrderItem(
            order=order,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price=cart_item.product.price
        )
        db.session.add(order_item)
        # Remove item from cart
        db.session.delete(cart_item)

    db.session.commit()
    flash('Order placed successfully!')
    return redirect(url_for('home'))

def init_db():
    with app.app_context():
        db.create_all()
        # Add sample products if none exist
        if Product.query.count() == 0:
            products = [
                # Electronics (20 products)
                Product(name="Gaming Laptop", price=1299.99, category="Electronics", description="High-end gaming laptop with RTX 4070", image_url="https://picsum.photos/seed/gaminglaptop/500/300"),
                Product(name="4K Smart TV", price=899.99, category="Electronics", description="55-inch 4K Ultra HD Smart TV", image_url="https://picsum.photos/seed/smarttv/500/300"),
                Product(name="Wireless Earbuds", price=149.99, category="Electronics", description="True wireless earbuds with noise cancellation", image_url="https://picsum.photos/seed/earbuds/500/300"),
                Product(name="Gaming Mouse", price=79.99, category="Electronics", description="RGB gaming mouse with 25K DPI sensor", image_url="https://picsum.photos/seed/gamingmouse/500/300"),
                Product(name="Mechanical Keyboard", price=129.99, category="Electronics", description="RGB mechanical keyboard with Cherry MX switches", image_url="https://picsum.photos/seed/mechkeyboard/500/300"),
                Product(name="Webcam", price=89.99, category="Electronics", description="4K webcam with built-in microphone", image_url="https://picsum.photos/seed/webcam/500/300"),
                Product(name="Bluetooth Speaker", price=119.99, category="Electronics", description="Portable waterproof Bluetooth speaker", image_url="https://picsum.photos/seed/bluetoothspeaker/500/300"),
                Product(name="Power Bank", price=49.99, category="Electronics", description="20,000mAh portable charger", image_url="https://picsum.photos/seed/powerbank/500/300"),
                Product(name="USB-C Hub", price=39.99, category="Electronics", description="7-in-1 USB-C adapter hub", image_url="https://picsum.photos/seed/usbhub/500/300"),
                Product(name="Wireless Charger", price=29.99, category="Electronics", description="15W fast wireless charging pad", image_url="https://picsum.photos/seed/wirelesscharger/500/300"),
                Product(name="Monitor Stand", price=69.99, category="Electronics", description="Adjustable dual monitor stand", image_url="https://picsum.photos/seed/monitorstand/500/300"),
                Product(name="Microphone", price=159.99, category="Electronics", description="USB condenser microphone for streaming", image_url="https://picsum.photos/seed/microphone/500/300"),
                Product(name="Graphics Tablet", price=199.99, category="Electronics", description="Digital drawing tablet with stylus", image_url="https://picsum.photos/seed/graphicstablet/500/300"),
                Product(name="Network Switch", price=89.99, category="Electronics", description="8-port gigabit network switch", image_url="https://picsum.photos/seed/networkswitch/500/300"),
                Product(name="WiFi Extender", price=59.99, category="Electronics", description="Dual-band WiFi range extender", image_url="https://picsum.photos/seed/wifiextender/500/300"),
                Product(name="Smart Bulb Set", price=79.99, category="Electronics", description="4-pack smart LED bulbs with app control", image_url="https://picsum.photos/seed/smartbulbs/500/300"),
                Product(name="Security Camera", price=129.99, category="Electronics", description="1080p wireless security camera", image_url="https://picsum.photos/seed/securitycamera/500/300"),
                Product(name="Robot Vacuum", price=299.99, category="Electronics", description="Smart robot vacuum with mapping", image_url="https://picsum.photos/seed/robotvacuum/500/300"),
                Product(name="Smart Thermostat", price=199.99, category="Electronics", description="WiFi-enabled smart thermostat", image_url="https://picsum.photos/seed/smartthermostat/500/300"),
                Product(name="Digital Photo Frame", price=89.99, category="Electronics", description="10-inch digital photo frame", image_url="https://picsum.photos/seed/photoframe/500/300"),
                
                # Clothing (20 products)
                Product(name="Denim Jacket", price=89.99, category="Clothing", description="Classic denim jacket with vintage wash", image_url="https://picsum.photos/seed/denimjacket/500/300"),
                Product(name="Leather Boots", price=149.99, category="Clothing", description="Premium leather ankle boots", image_url="https://picsum.photos/seed/leatherboots/500/300"),
                Product(name="Cashmere Sweater", price=129.99, category="Clothing", description="Soft cashmere crew neck sweater", image_url="https://picsum.photos/seed/cashmeresweater/500/300"),
                Product(name="Slim Fit Jeans", price=79.99, category="Clothing", description="Dark wash slim fit denim jeans", image_url="https://picsum.photos/seed/slimjeans/500/300"),
                Product(name="Polo Shirt", price=39.99, category="Clothing", description="Cotton polo shirt in classic colors", image_url="https://picsum.photos/seed/poloshirt/500/300"),
                Product(name="Winter Coat", price=199.99, category="Clothing", description="Warm winter coat with faux fur hood", image_url="https://picsum.photos/seed/wintercoat/500/300"),
                Product(name="Running Shoes", price=119.99, category="Clothing", description="Lightweight running shoes with cushioning", image_url="https://picsum.photos/seed/runningshoes/500/300"),
                Product(name="Dress Shirt", price=69.99, category="Clothing", description="Cotton dress shirt for formal occasions", image_url="https://picsum.photos/seed/dressshirt/500/300"),
                Product(name="Hoodie", price=59.99, category="Clothing", description="Comfortable cotton hoodie", image_url="https://picsum.photos/seed/hoodie/500/300"),
                Product(name="Summer Dress", price=89.99, category="Clothing", description="Floral print summer dress", image_url="https://picsum.photos/seed/summerdress/500/300"),
                Product(name="Blazer", price=159.99, category="Clothing", description="Professional blazer for office wear", image_url="https://picsum.photos/seed/blazer/500/300"),
                Product(name="T-Shirt Pack", price=29.99, category="Clothing", description="3-pack basic cotton t-shirts", image_url="https://picsum.photos/seed/tshirtpack/500/300"),
                Product(name="Sneakers", price=89.99, category="Clothing", description="Casual sneakers for everyday wear", image_url="https://picsum.photos/seed/sneakers/500/300"),
                Product(name="Scarf", price=24.99, category="Clothing", description="Warm wool scarf for winter", image_url="https://picsum.photos/seed/scarf/500/300"),
                Product(name="Sunglasses", price=79.99, category="Clothing", description="Polarized sunglasses with UV protection", image_url="https://picsum.photos/seed/sunglasses/500/300"),
                Product(name="Watch", price=199.99, category="Clothing", description="Classic analog watch with leather strap", image_url="https://picsum.photos/seed/watch/500/300"),
                Product(name="Backpack", price=69.99, category="Clothing", description="Durable backpack for daily use", image_url="https://picsum.photos/seed/backpack/500/300"),
                Product(name="Belt", price=34.99, category="Clothing", description="Genuine leather belt with classic buckle", image_url="https://picsum.photos/seed/belt/500/300"),
                Product(name="Socks Pack", price=19.99, category="Clothing", description="6-pack cotton socks", image_url="https://picsum.photos/seed/sockspack/500/300"),
                Product(name="Gloves", price=29.99, category="Clothing", description="Warm winter gloves", image_url="https://picsum.photos/seed/gloves/500/300"),
                Product(name="Tie", price=39.99, category="Clothing", description="Silk tie for formal occasions", image_url="https://picsum.photos/seed/tie/500/300"),
                
                # Home & Garden (20 products)
                Product(name="Coffee Maker", price=89.99, category="Home & Garden", description="Programmable coffee maker with thermal carafe", image_url="https://picsum.photos/seed/coffeemaker/500/300"),
                Product(name="Blender", price=69.99, category="Home & Garden", description="High-speed blender for smoothies", image_url="https://picsum.photos/seed/blender/500/300"),
                Product(name="Toaster", price=49.99, category="Home & Garden", description="4-slice toaster with bagel setting", image_url="https://picsum.photos/seed/toaster/500/300"),
                Product(name="Microwave", price=129.99, category="Home & Garden", description="Countertop microwave with sensor cooking", image_url="https://picsum.photos/seed/microwave/500/300"),
                Product(name="Air Fryer", price=99.99, category="Home & Garden", description="Digital air fryer with 5.8L capacity", image_url="https://picsum.photos/seed/airfryer/500/300"),
                Product(name="Stand Mixer", price=199.99, category="Home & Garden", description="Professional stand mixer for baking", image_url="https://picsum.photos/seed/standmixer/500/300"),
                Product(name="Food Processor", price=79.99, category="Home & Garden", description="8-cup food processor with multiple blades", image_url="https://picsum.photos/seed/foodprocessor/500/300"),
                Product(name="Rice Cooker", price=59.99, category="Home & Garden", description="Programmable rice cooker with steamer", image_url="https://picsum.photos/seed/ricecooker/500/300"),
                Product(name="Slow Cooker", price=69.99, category="Home & Garden", description="6-quart slow cooker with programmable timer", image_url="https://picsum.photos/seed/slowcooker/500/300"),
                Product(name="Electric Kettle", price=39.99, category="Home & Garden", description="Stainless steel electric kettle", image_url="https://picsum.photos/seed/electrickettle/500/300"),
                Product(name="Garden Hose", price=34.99, category="Home & Garden", description="50-foot expandable garden hose", image_url="https://picsum.photos/seed/gardenhose/500/300"),
                Product(name="Plant Pot Set", price=24.99, category="Home & Garden", description="Set of 3 ceramic plant pots", image_url="https://picsum.photos/seed/plantpots/500/300"),
                Product(name="Garden Tools", price=49.99, category="Home & Garden", description="Essential garden tool set", image_url="https://picsum.photos/seed/gardentools/500/300"),
                Product(name="Outdoor Chair", price=79.99, category="Home & Garden", description="Folding outdoor chair for patio", image_url="https://picsum.photos/seed/outdoorchair/500/300"),
                Product(name="Bird Feeder", price=19.99, category="Home & Garden", description="Hanging bird feeder for backyard", image_url="https://picsum.photos/seed/birdfeeder/500/300"),
                Product(name="Watering Can", price=29.99, category="Home & Garden", description="2-gallon metal watering can", image_url="https://picsum.photos/seed/wateringcan/500/300"),
                Product(name="Garden Gloves", price=14.99, category="Home & Garden", description="Durable garden gloves", image_url="https://picsum.photos/seed/gardengloves/500/300"),
                Product(name="Plant Stand", price=39.99, category="Home & Garden", description="Tiered plant stand for indoor plants", image_url="https://picsum.photos/seed/plantstand/500/300"),
                Product(name="Garden Lights", price=44.99, category="Home & Garden", description="Solar-powered garden lights set", image_url="https://picsum.photos/seed/gardenlights/500/300"),
                Product(name="Compost Bin", price=59.99, category="Home & Garden", description="Outdoor compost bin for organic waste", image_url="https://picsum.photos/seed/compostbin/500/300"),
                Product(name="Garden Rake", price=19.99, category="Home & Garden", description="Steel garden rake for leaves", image_url="https://picsum.photos/seed/gardenrake/500/300"),
                
                # Sports & Outdoors (20 products)
                Product(name="Yoga Mat", price=29.99, category="Sports & Outdoors", description="Non-slip yoga mat for home workouts", image_url="https://picsum.photos/seed/yogamat/500/300"),
                Product(name="Dumbbells Set", price=89.99, category="Sports & Outdoors", description="Adjustable dumbbells set 5-50 lbs", image_url="https://picsum.photos/seed/dumbbells/500/300"),
                Product(name="Treadmill", price=599.99, category="Sports & Outdoors", description="Folding treadmill with LCD display", image_url="https://picsum.photos/seed/treadmill/500/300"),
                Product(name="Bicycle", price=299.99, category="Sports & Outdoors", description="Mountain bike with 21-speed gears", image_url="https://picsum.photos/seed/bicycle/500/300"),
                Product(name="Tennis Racket", price=79.99, category="Sports & Outdoors", description="Professional tennis racket with case", image_url="https://picsum.photos/seed/tennisracket/500/300"),
                Product(name="Basketball", price=24.99, category="Sports & Outdoors", description="Official size basketball", image_url="https://picsum.photos/seed/basketball/500/300"),
                Product(name="Soccer Ball", price=19.99, category="Sports & Outdoors", description="Size 5 soccer ball", image_url="https://picsum.photos/seed/soccerball/500/300"),
                Product(name="Golf Clubs Set", price=199.99, category="Sports & Outdoors", description="Complete golf club set with bag", image_url="https://picsum.photos/seed/golfclubs/500/300"),
                Product(name="Fishing Rod", price=69.99, category="Sports & Outdoors", description="Spinning fishing rod and reel combo", image_url="https://picsum.photos/seed/fishingrod/500/300"),
                Product(name="Tent", price=149.99, category="Sports & Outdoors", description="4-person camping tent", image_url="https://picsum.photos/seed/tent/500/300"),
                Product(name="Sleeping Bag", price=59.99, category="Sports & Outdoors", description="3-season sleeping bag", image_url="https://picsum.photos/seed/sleepingbag/500/300"),
                Product(name="Backpack", price=89.99, category="Sports & Outdoors", description="Hiking backpack with hydration bladder", image_url="https://picsum.photos/seed/hikingbackpack/500/300"),
                Product(name="Hiking Boots", price=129.99, category="Sports & Outdoors", description="Waterproof hiking boots", image_url="https://picsum.photos/seed/hikingboots/500/300"),
                Product(name="Water Bottle", price=19.99, category="Sports & Outdoors", description="Insulated water bottle 32oz", image_url="https://picsum.photos/seed/waterbottle/500/300"),
                Product(name="Resistance Bands", price=24.99, category="Sports & Outdoors", description="Set of 5 resistance bands", image_url="https://picsum.photos/seed/resistancebands/500/300"),
                Product(name="Jump Rope", price=14.99, category="Sports & Outdoors", description="Adjustable jump rope for cardio", image_url="https://picsum.photos/seed/jumprope/500/300"),
                Product(name="Foam Roller", price=29.99, category="Sports & Outdoors", description="High-density foam roller for recovery", image_url="https://picsum.photos/seed/foamroller/500/300"),
                Product(name="Swimming Goggles", price=19.99, category="Sports & Outdoors", description="Anti-fog swimming goggles", image_url="https://picsum.photos/seed/swimminggoggles/500/300"),
                Product(name="Baseball Glove", price=49.99, category="Sports & Outdoors", description="Leather baseball glove", image_url="https://picsum.photos/seed/baseballglove/500/300"),
                Product(name="Volleyball", price=34.99, category="Sports & Outdoors", description="Official volleyball", image_url="https://picsum.photos/seed/volleyball/500/300"),
                Product(name="Badminton Set", price=39.99, category="Sports & Outdoors", description="Complete badminton set with rackets", image_url="https://picsum.photos/seed/badmintonset/500/300"),
                
                # Books & Media (20 products)
                Product(name="Kindle E-reader", price=89.99, category="Books & Media", description="6-inch Kindle with built-in light", image_url="https://picsum.photos/seed/kindle/500/300"),
                Product(name="Bluetooth Headphones", price=79.99, category="Books & Media", description="Over-ear wireless headphones", image_url="https://picsum.photos/seed/bluetoothheadphones/500/300"),
                Product(name="Portable Speaker", price=59.99, category="Books & Media", description="Waterproof portable speaker", image_url="https://picsum.photos/seed/portablespeaker/500/300"),
                Product(name="Vinyl Record Player", price=199.99, category="Books & Media", description="3-speed turntable with speakers", image_url="https://picsum.photos/seed/recordplayer/500/300"),
                Product(name="Guitar", price=299.99, category="Books & Media", description="Acoustic guitar for beginners", image_url="https://picsum.photos/seed/guitar/500/300"),
                Product(name="Piano Keyboard", price=399.99, category="Books & Media", description="61-key digital piano", image_url="https://picsum.photos/seed/pianokeyboard/500/300"),
                Product(name="Microphone Stand", price=29.99, category="Books & Media", description="Adjustable microphone stand", image_url="https://picsum.photos/seed/microphonestand/500/300"),
                Product(name="DJ Controller", price=199.99, category="Books & Media", description="USB DJ controller for beginners", image_url="https://picsum.photos/seed/djcontroller/500/300"),
                Product(name="Camera Tripod", price=49.99, category="Books & Media", description="Aluminum camera tripod", image_url="https://picsum.photos/seed/cameratripod/500/300"),
                Product(name="GoPro Camera", price=299.99, category="Books & Media", description="Action camera with waterproof case", image_url="https://picsum.photos/seed/gopro/500/300"),
                Product(name="Photo Printer", price=149.99, category="Books & Media", description="Portable photo printer", image_url="https://picsum.photos/seed/photoprinter/500/300"),
                Product(name="DVD Player", price=39.99, category="Books & Media", description="Portable DVD player", image_url="https://picsum.photos/seed/dvdplayer/500/300"),
                Product(name="CD Player", price=29.99, category="Books & Media", description="Portable CD player with headphones", image_url="https://picsum.photos/seed/cdplayer/500/300"),
                Product(name="Cassette Player", price=19.99, category="Books & Media", description="Retro cassette player", image_url="https://picsum.photos/seed/cassetteplayer/500/300"),
                Product(name="Radio", price=34.99, category="Books & Media", description="AM/FM radio with alarm clock", image_url="https://picsum.photos/seed/radio/500/300"),
                Product(name="MP3 Player", price=49.99, category="Books & Media", description="8GB MP3 player with screen", image_url="https://picsum.photos/seed/mp3player/500/300"),
                Product(name="Voice Recorder", price=39.99, category="Books & Media", description="Digital voice recorder", image_url="https://picsum.photos/seed/voicerecorder/500/300"),
                Product(name="Karaoke Machine", price=79.99, category="Books & Media", description="Portable karaoke machine with microphone", image_url="https://picsum.photos/seed/karaokemachine/500/300"),
                Product(name="Metronome", price=24.99, category="Books & Media", description="Digital metronome for musicians", image_url="https://picsum.photos/seed/metronome/500/300"),
                Product(name="Tuner", price=19.99, category="Books & Media", description="Guitar tuner with clip", image_url="https://picsum.photos/seed/tuner/500/300"),
                Product(name="Music Stand", price=34.99, category="Books & Media", description="Adjustable music stand", image_url="https://picsum.photos/seed/musicstand/500/300"),
                Product(name="Instrument Case", price=44.99, category="Books & Media", description="Hard case for musical instruments", image_url="https://picsum.photos/seed/instrumentcase/500/300"),
                
                # Toys & Games (20 products)
                Product(name="Board Game", price=29.99, category="Toys & Games", description="Classic strategy board game", image_url="https://picsum.photos/seed/boardgame/500/300"),
                Product(name="Puzzle Set", price=19.99, category="Toys & Games", description="1000-piece jigsaw puzzle", image_url="https://picsum.photos/seed/puzzle/500/300"),
                Product(name="LEGO Set", price=49.99, category="Toys & Games", description="Building blocks set for kids", image_url="https://picsum.photos/seed/lego/500/300"),
                Product(name="Remote Control Car", price=39.99, category="Toys & Games", description="High-speed RC car", image_url="https://picsum.photos/seed/rccar/500/300"),
                Product(name="Drone", price=89.99, category="Toys & Games", description="Mini drone with camera", image_url="https://picsum.photos/seed/drone/500/300"),
                Product(name="Video Game Console", price=299.99, category="Toys & Games", description="Gaming console with controller", image_url="https://picsum.photos/seed/gameconsole/500/300"),
                Product(name="Gaming Controller", price=59.99, category="Toys & Games", description="Wireless gaming controller", image_url="https://picsum.photos/seed/gamingcontroller/500/300"),
                Product(name="Card Game", price=14.99, category="Toys & Games", description="Popular card game for families", image_url="https://picsum.photos/seed/cardgame/500/300"),
                Product(name="Chess Set", price=24.99, category="Toys & Games", description="Wooden chess set with board", image_url="https://picsum.photos/seed/chessset/500/300"),
                Product(name="Dart Board", price=34.99, category="Toys & Games", description="Electronic dart board", image_url="https://picsum.photos/seed/dartboard/500/300"),
                Product(name="Pool Table", price=599.99, category="Toys & Games", description="Mini pool table for home", image_url="https://picsum.photos/seed/pooltable/500/300"),
                Product(name="Ping Pong Set", price=79.99, category="Toys & Games", description="Table tennis set with net", image_url="https://picsum.photos/seed/pingpong/500/300"),
                Product(name="Foosball Table", price=199.99, category="Toys & Games", description="Mini foosball table", image_url="https://picsum.photos/seed/foosball/500/300"),
                Product(name="Air Hockey Table", price=299.99, category="Toys & Games", description="Tabletop air hockey game", image_url="https://picsum.photos/seed/airhockey/500/300"),
                Product(name="Arcade Machine", price=399.99, category="Toys & Games", description="Retro arcade machine with games", image_url="https://picsum.photos/seed/arcademachine/500/300"),
                Product(name="Slot Car Track", price=69.99, category="Toys & Games", description="Electric slot car racing set", image_url="https://picsum.photos/seed/slotcar/500/300"),
                Product(name="Model Kit", price=19.99, category="Toys & Games", description="Plastic model building kit", image_url="https://picsum.photos/seed/modelkit/500/300"),
                Product(name="Science Kit", price=34.99, category="Toys & Games", description="Educational science experiment kit", image_url="https://picsum.photos/seed/sciencekit/500/300"),
                Product(name="Art Set", price=24.99, category="Toys & Games", description="Complete art supplies set", image_url="https://picsum.photos/seed/artset/500/300"),
                Product(name="Building Blocks", price=39.99, category="Toys & Games", description="Magnetic building blocks set", image_url="https://picsum.photos/seed/buildingblocks/500/300"),
                Product(name="Robot Kit", price=79.99, category="Toys & Games", description="Programmable robot building kit", image_url="https://picsum.photos/seed/robotkit/500/300"),
                Product(name="Magic Set", price=29.99, category="Toys & Games", description="Magic tricks kit for beginners", image_url="https://picsum.photos/seed/magicset/500/300"),
                
                # Keep the original 6 products
                Product(name="Laptop", price=999.99, category="Electronics", description="High-performance laptop with 16GB RAM", image_url="https://picsum.photos/seed/laptop/500/300"),
                Product(name="Smartphone", price=699.99, category="Electronics", description="Latest model with 128GB storage", image_url="https://picsum.photos/seed/smartphone/500/300"),
                Product(name="Headphones", price=199.99, category="Electronics", description="Wireless noise-cancelling headphones", image_url="https://picsum.photos/seed/headphones/500/300"),
                Product(name="Smart Watch", price=299.99, category="Electronics", description="Fitness tracker with heart rate monitor", image_url="https://picsum.photos/seed/watch/500/300"),
                Product(name="Tablet", price=499.99, category="Electronics", description="10-inch tablet with retina display", image_url="https://picsum.photos/seed/tablet/500/300"),
                Product(name="Camera", price=799.99, category="Electronics", description="Professional DSLR camera with 4K video", image_url="https://picsum.photos/seed/camera/500/300")
            ]
            for product in products:
                db.session.add(product)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8080) 