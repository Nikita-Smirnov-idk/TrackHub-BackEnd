from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from datetime import datetime, timedelta
import jwt
import os

from users.models import CustomUser
from django.template.loader import render_to_string



def send_email_to_user(email):
    user = CustomUser.objects.get(email=email)

    # Создание токена для email
    token_payload = {
        'user_id': user.id,
        'exp': datetime.now() + timedelta(hours=24),
    }
    token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm='HS256')

    # Ссылка для iOS приложения
    confirm_url = f"TrackHub://verify-email?token={token}"

    current_dir = os.path.dirname(os.path.abspath(__file__))

    html_content = render_to_string("email/email.html", {"confirm_url": confirm_url})

    subject = "Подтверждение регистрации"

    # Create the email object
    email_message = EmailMultiAlternatives(
        subject=subject,
        body="Подтвердите ваш email, используя HTML-версию письма.",  # Plain text fallback
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email],
    )
    
    # Attach the HTML content
    email_message.attach_alternative(html_content, "text/html")
    
    # Send email
    email_message.send()