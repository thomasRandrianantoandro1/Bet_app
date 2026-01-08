import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp=Blueprint('auth', __name__,url_prefix='/auth')

@bp.route('/login/<token>')
def connetion_token(token):
    db=get_db()
    user=db.execute('SELECT * FROM user WHERE token=?', (token,)).fetchone()
    if user is None:
        return "Connexion Invalide",403

    session.clear()
    session['user_id']=user['id_user']
    return redirect(url_for('pari.pari_unique'))


@bp.before_app_request
def before_request():
    user_id=session.get('user_id')
    if user_id is None:
        g.user=None
    else:
        g.user=get_db().execute('SELECT * FROM user WHERE id_user=?', (user_id,)).fetchone()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return "Accès refusé. Veuillez utilisez votre lien unique.",401
        return view(**kwargs)
    return wrapped_view


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return "Accès refusé. Veuillez vous connecter.", 401

        if not g.user['role']:
            return "Accès réservé à l'administrateur.", 403

        return view(**kwargs)

    return wrapped_view