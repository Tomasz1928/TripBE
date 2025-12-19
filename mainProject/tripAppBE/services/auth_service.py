from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError


def register_user(username, password):
    if User.objects.filter(username=username).exists():
        return None
    user = User.objects.create(username=username, password=make_password(password))
    return user


def login_user(request, username, password):
    user = authenticate(request, username=username, password=password)
    if not user:
        raise ValidationError("Invalid login")
    login(request, user)
    return True


def logout_user(request):
    logout(request)


def session(request):
    return request.user.is_authenticated
