from website import create_app
from flask import Flask, jsonify, request, redirect, url_for
from flask_login import current_user
import os
import json
from website import type

app = create_app()

if __name__ == '__main__':
    if type =='testing':
        app.run(debug=True)
    elif type == 'production':
        app.run()
        