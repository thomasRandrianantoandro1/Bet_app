import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp=Blueprint('admin', __name__,url_prefix='/admin')

# @bp.route('/selection_matchs',methods=['GET','POST'])
# def selection_matchs():
#     db=get_db()

