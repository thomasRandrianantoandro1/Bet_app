import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from auth import login_required
from .db import get_db

bp = Blueprint('historique', __name__, url_prefix='/historique')

@bp.route('/pari_unique', methods=['GET', 'POST'])
@login_required
def pari_unique():
    db=get_db()

    historique= db.execute(
        """
        SELECT p.id_single_bet, p.intitule, p.cote, p.mise, p.statut_pari, p.preneur_id, u1.nom AS nom_createur, u2.nom AS nom_preneur, p.resultat
        FROM single_bet p 
        LEFT JOIN user u1 ON p.createur_id = u1.id_user 
        LEFT JOIN user u2 ON p.preneur_id = u2.id_user 
        WHERE p.statut_pari = 1 
        ORDER BY p.date_de_creation DESC
        """
                           ).fetchall()

    return render_template('historique/pari_unique.html', historique=historique)