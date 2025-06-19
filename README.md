# E-Commerce Store

A modern Flask-based e-commerce application with user authentication, shopping cart functionality, and product categorization.

## Features

- **User Authentication**: Register, login, and logout functionality
- **Product Catalog**: 106+ products across 6 categories
- **Category Filtering**: Filter products by category
- **Shopping Cart**: Add/remove items from cart
- **Checkout System**: Complete purchase process with shipping information
- **Responsive Design**: Modern UI with Bootstrap 5
- **Left Sidebar Navigation**: Clean and intuitive navigation

## Categories

- **Electronics** (26 products): Laptops, smartphones, accessories, smart devices
- **Clothing** (20 products): Apparel, shoes, accessories
- **Home & Garden** (20 products): Kitchen appliances, garden tools, outdoor furniture
- **Sports & Outdoors** (20 products): Fitness equipment, sports gear, camping items
- **Books & Media** (20 products): E-readers, musical instruments, cameras, audio equipment
- **Toys & Games** (20 products): Board games, puzzles, gaming consoles, educational toys

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Images**: Picsum Photos for placeholder images

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/drgittest/cursortest01.git
   cd cursortest01
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask flask-sqlalchemy flask-login werkzeug
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your browser and go to: http://localhost:8080
   - Register a new account or login to start shopping

## Project Structure

```
cursortest01/
├── app.py                 # Main Flask application
├── templates/             # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── home.html         # Product catalog page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── cart.html         # Shopping cart page
│   └── checkout.html     # Checkout page
├── instance/             # Database files (auto-generated)
├── venv/                 # Virtual environment (excluded from git)
├── .gitignore           # Git ignore file
└── README.md            # This file
```

## Database Models

- **User**: User accounts with authentication
- **Product**: Product catalog with categories
- **CartItem**: Shopping cart items
- **Order**: Customer orders
- **OrderItem**: Individual items in orders

## Features in Detail

### User Authentication
- Secure password hashing with Werkzeug
- Session management with Flask-Login
- Protected routes for authenticated users

### Product Management
- 106 products with realistic pricing
- Category-based organization
- Product images, descriptions, and pricing
- Category filtering functionality

### Shopping Experience
- Add products to cart
- View cart contents
- Remove items from cart
- Complete checkout process
- Order history tracking

### UI/UX Features
- Responsive Bootstrap 5 design
- Left sidebar navigation
- Category badges on products
- Price display
- Flash messages for user feedback

## Development

The application runs in debug mode by default. For production deployment:

1. Set `debug=False` in `app.py`
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Configure proper database (PostgreSQL, MySQL)
4. Set up environment variables for secrets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Screenshots

- **Home Page**: Product catalog with category filtering
- **Shopping Cart**: Cart management interface
- **Checkout**: Order completion process
- **User Authentication**: Login and registration pages

## Future Enhancements

- Payment gateway integration
- Product reviews and ratings
- Wishlist functionality
- Admin panel for product management
- Email notifications
- Advanced search and filtering
- Mobile app development 