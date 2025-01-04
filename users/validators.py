from django.core.exceptions import ValidationError
import re


def password_validator(password):
    errors = []

    # Check length
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter.")

    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter.")

    # Check for a digit
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit.")

    # Check for spaces (should not contain spaces)
    if re.search(r'\s', password):
        errors.append("Password must not contain spaces.")

    if errors:
        raise ValidationError(errors)
