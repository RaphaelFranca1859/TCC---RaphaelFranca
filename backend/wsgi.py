"""Ponto de entrada para servidores WSGI:  gunicorn --chdir backend wsgi:app"""
from app import create_app

app = create_app()
