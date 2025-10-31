# AGENTS.md - Moonwakewares E-commerce Project

## Build/Lint/Test Commands

### Testing
- **All tests**: `cd moon_ecommerce && python manage.py test`
- **Single app tests**: `cd moon_ecommerce && python manage.py test store`
- **Single test method**: `cd moon_ecommerce && python manage.py test store.tests.TestClass.test_method`
- **Verbose output**: `cd moon_ecommerce && python manage.py test --verbosity=2`

### Linting
- No linting tools currently configured (Ruff mentioned in .gitignore but not set up)

### Development Server
- **Start server**: `cd moon_ecommerce && python manage.py runserver`
- **With specific port**: `cd moon_ecommerce && python manage.py runserver 8001`

## Code Style Guidelines

### Imports
- Group Django imports first, then third-party, then local imports
- Use explicit imports: `from django.shortcuts import render, get_object_or_404`
- Avoid wildcard imports (`from module import *`)

### Naming Conventions
- **Classes**: PascalCase (e.g., `Jewelry`, `Cart`, `CartItem`)
- **Functions/Methods**: snake_case (e.g., `get_cart`, `add_to_cart`)
- **Variables**: snake_case (e.g., `cart_item`, `total_price`)
- **Constants**: UPPER_CASE (e.g., `STATUS_CHOICES`)

### Django Models
- Use descriptive field names with appropriate field types
- Add `blank=True, null=True` for optional fields
- Implement `__str__` methods for readable representations
- Use `@property` decorators for calculated fields (e.g., `total_price`)
- Define `Meta` class for ordering when needed

### Views
- Use function-based views with clear, descriptive names
- Apply appropriate decorators (`@login_required`, etc.)
- Use Django shortcuts (`get_object_or_404`, `redirect`)
- Handle both GET and POST requests appropriately
- Use Django messages for user feedback

### Error Handling
- Use try/except blocks for external API calls (Square payments)
- Log errors with appropriate log levels using `logger`
- Provide user-friendly error messages via Django messages
- Redirect to appropriate pages on errors

### Security
- Never commit sensitive data (.env files, secrets)
- Use Django's built-in authentication and authorization
- Validate all user inputs through forms or manual validation
- Use HTTPS in production

### Database
- Use migrations for all model changes: `python manage.py makemigrations`
- Apply migrations: `python manage.py migrate`
- Use PostgreSQL in production, SQLite for development

### Virtual Environment
- Activate: `source moon/bin/activate` (note: uses 'moon' not 'venv')
- Install dependencies: `pip install -r requirements.txt`