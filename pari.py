import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from .auth import login_required
from .db import get_db

bp = Blueprint('pari', __name__, url_prefix='/pari')


@bp.route('/pari_unique', methods=('GET', 'POST'))
@login_required
def pari_unique():
    db=get_db()

    if request.method == 'POST':
        intitule=request.form['intitule']
        cote=request.form['cote']
        mise=request.form['mise']
        id_parieur=g.user['id_user']
        error = None

        if not intitule:
            error="Il faut tout remplir."
        if error is None:
            db.execute('INSERT INTO single_bet (intitule, cote, mise, createur_id) VALUES (?,?,?,?)', (intitule, cote, mise, id_parieur))
            db.commit()
            return redirect(url_for('pari.pari_unique'))
        flash(error)



    """ Vérification du token 
    """


    paris = db.execute(
        """ SELECT p.id_single_bet, p.intitule, p.cote, p.mise, p.statut_pari, p.preneur_id, u1.nom AS nom_createur, u2.nom AS nom_preneur, p.createur_id 
        FROM single_bet p 
        LEFT JOIN user u1 ON p.createur_id = u1.id_user 
        LEFT JOIN user u2 ON p.preneur_id = u2.id_user
        WHERE p.statut_pari = 0 
        ORDER BY p.date_de_creation DESC
        """
    ).fetchall()

    return render_template('pari/pari_unique.html', paris=paris)

@bp.route('/prendre_un_pari',methods=['POST'])
@login_required
def prendre_un_pari():
    db=get_db()
    id_pari=request.form['id_du_pari']
    id_preneur=g.user['id_user']

    pari=db.execute('UPDATE single_bet SET preneur_id= ? WHERE id_single_bet = ?', (id_preneur, id_pari))
    db.commit()

    return redirect(url_for('pari.pari_unique'))



