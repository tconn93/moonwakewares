# Moonwakewares.com

this project is an ecommerce site that I sold for a charity auction. Now it is time to put in the work.   


I am using django because the admin portal is already setup, when starting the project. 


## Project Overview

Moonwakewares is a Django-based e-commerce site for selling jewelry, created for a charity auction. The project uses Django's built-in admin portal for content management.

## Development Setup

### Virtual Environment
```bash
# Activate virtual environment (located in ./moon/)
source moon/bin/activate

# Deactivate when done
deactivate
```

### Running the Development Server
```bash
# From the project root
cd moon_ecommerce
python manage.py runserver

# The server will run at http://127.0.0.1:8000/
# Admin panel available at http://127.0.0.1:8000/admin/
```

### Database Migrations
```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

### Admin User Management
```bash
# Create superuser for admin access
python manage.py createsuperuser
```

### Running Tests
```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test store

# Run with verbose output
python manage.py test --verbosity=2
```

### Django Shell
```bash
# Open Django shell for testing/debugging
python manage.py shell
```

## Architecture

### Project Structure
- **moon_ecommerce/**: Django project directory
  - **moon_ecommerce/**: Project configuration package
    - `settings.py`: Django settings (SECRET_KEY, INSTALLED_APPS, middleware, REST framework config)
    - `urls.py`: Root URL configuration (includes admin and store URLs, serves media files)
  - **store/**: Main e-commerce application
    - `models.py`: Data models (Jewelry, Cart, CartItem)
    - `views.py`: View functions for product display and cart management
    - `urls.py`: Store URL patterns
    - `admin.py`: Customized Django admin interfaces
    - **templates/store/**: HTML templates (base.html, home.html, product_list.html, product_detail.html, cart_detail.html)
  - `manage.py`: Django management script
  - `db.sqlite3`: SQLite database
- **moon/**: Python virtual environment

### Data Models

**Jewelry**
- Core product model with name, description, price, image, and timestamp
- Images stored in `media/jewelry_images/`

**Cart**
- One-to-one relationship with User (nullable for anonymous users)
- Has `total_price` property that calculates sum of all cart items
- Tracks created_at and updated_at timestamps

**CartItem**
- Links Cart to Jewelry products with quantity
- Has `total_price` property (jewelry.price * quantity)

### Key Features

**Cart System**
- Supports both authenticated and anonymous users
- Anonymous carts use session keys
- Helper function `get_cart(request)` handles cart retrieval/creation
- Cart operations: add, update quantity, remove items
- Uses Django messages framework for user feedback

**Admin Customization**
- Jewelry admin: inline image previews, price editing, search/filter
- Cart admin: displays total price, prefetch optimization for performance
- CartItem admin: inline quantity editing

**REST Framework Integration**
- Configured with Token Authentication
- Default permission: IsAuthenticated
- Settings in `settings.py:107-114`

### Static and Media Files
- Static files URL: `/static/`
- Media files: `/media/` (configured in settings and root URLs)
- Media root: `moon_ecommerce/media/`

### Session Configuration
- Uses database-backed sessions (`django.contrib.sessions.backends.db`)
- Required for anonymous cart functionality

## Database Configuration

The application uses **PostgreSQL** hosted on a remote server. Database credentials are stored securely in `.env` file (not tracked in git).

**Important**: The `.env` file contains sensitive credentials and is excluded from version control via `.gitignore`.

### Environment Variables
The application uses `python-decouple` to manage configuration. Create a `.env` file in the project root with:

```
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=your_database_host
DB_PORT=5432
SECRET_KEY=your_django_secret_key
```

Required environment variables:
- `SECRET_KEY`: Django secret key
- `DB_NAME`: PostgreSQL database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database server IP/hostname
- `DB_PORT`: Database port (default: 5432)

## Important Notes

- Database: PostgreSQL on remote server
- Debug mode is ON (must be disabled for production)
- Credentials stored in `.env` file (not committed to git)
- Virtual environment named `moon/` (not the typical `venv/` name)
- PostgreSQL database names are case-sensitive
