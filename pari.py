import functools
from re import match

import requests
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
            db.execute('INSERT INTO single_bet (intitule, cote, mise, createur_id,statut_pari) VALUES (?,?,?,?,?)', (intitule, cote, mise, id_parieur,2))
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
        WHERE p.statut_pari = 2 
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

@bp.route('/pari_combine', methods=['GET', 'POST'])
@login_required
def pari_combine():
    db = get_db()
    id_user = g.user['id_user']  # Récupération de l'ID de l'utilisateur connecté

    # 1. On identifie d'abord le ticket actif (statut 0)
    ticket = db.execute(
        'SELECT id_ticket FROM ticket_commun WHERE statut = 0'
    ).fetchone()  #

    if not ticket:
        flash("Il n'y a aucun ticket ouvert actuellement.")
        return redirect(url_for('pari.pari_unique'))

    id_ticket_actuel = ticket['id_ticket']

    # 2. VÉRIFICATION : Le joueur a-t-il déjà parié sur ce ticket ?
    # On vérifie dans la table pari_des_joueurs si une entrée existe déjà
    deja_pari = db.execute(
        'SELECT 1 FROM pari_des_joueurs WHERE id_user = ? AND id_ticket = ?',
        (id_user, id_ticket_actuel)
    ).fetchone()  #

    if deja_pari:
        flash("Vous avez déjà validé vos pronostics pour ce ticket commun !")
        return redirect(url_for('pari.pari_des_joueurs'))
    if request.method == 'POST':
        # Récupération des listes de données du formulaire
        id_ticket = request.form.get('id_ticket')
        match_ids = request.form.getlist('api_id_match[]')
        scores_dom = request.form.getlist('score_domicile[]')
        scores_ext = request.form.getlist('score_exterieur[]')

        try:
            # 1. Enregistrer chaque match parié
            for m_id, s_dom, s_ext in zip(match_ids, scores_dom, scores_ext):
                # Détermination du vainqueur (1: dom, 2: ext, 0: nul)
                v_match = 0
                if int(s_dom) > int(s_ext):
                    v_match = 1
                elif int(s_dom) < int(s_ext):
                    v_match = 2

                db.execute(''' 
                    INSERT INTO pari_des_joueurs (id_user, id_ticket, api_id_match, score_dom, score_ext, vainqueur_match, resultat) 
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                ''', (id_user, id_ticket, m_id, s_dom, s_ext, v_match))

            # 2. Ajouter l'utilisateur aux participants pour le bilan (20$)
            db.execute('''
                INSERT OR IGNORE INTO ticket_participants (id_ticket, id_user, mise)
                VALUES (?, ?, 20)
            ''', (id_ticket, id_user))

            db.commit()
            flash("Votre combiné a été validé !")
            return redirect(url_for('pari.pari_des_joueurs'))

        except Exception as e:
            db.rollback()
            flash(f"Erreur lors de la validation : {str(e)}")

    # Affichage des matchs du ticket en cours (statut 0)
    matchs = db.execute(''' 
        SELECT td.id_detail, td.id_ticket, td.equipe_domicile, td.equipe_exterieur, td.api_id_match 
        FROM ticket_details td
        JOIN ticket_commun tc ON td.id_ticket = tc.id_ticket
        WHERE tc.statut = 0
    ''').fetchall()

    return render_template('pari/pari_combine.html', matchs=matchs)


@bp.route('/pari_des_joueurs',methods=['GET'])
@login_required
def pari_des_joueurs():
    db=get_db()
    paris=db.execute('''  SELECT u.nom,p.score_dom,p.score_ext,p.vainqueur_match, t.equipe_domicile, t.equipe_exterieur, t.equipe_domicile || ' vs ' || t.equipe_exterieur as match_label FROM pari_des_joueurs p
     LEFT JOIN user u ON p.id_user = u.id_user
 LEFT JOIN ticket_details t ON p.id_ticket = t.id_ticket AND p.api_id_match=t.api_id_match
     ''').fetchall()

    noms_joueurs = sorted(list(set(ligne['nom'] for ligne in paris if ligne['nom'])))
    tableau_final = {}
    for ligne in paris:
        match = ligne['match_label']
        nom = ligne['nom']
        score = f"{ligne['score_dom']} - {ligne['score_ext']}"

        if match not in tableau_final:
            tableau_final[match] = {}

        tableau_final[match][nom] = score

    return render_template('pari/pari_des_joueurs.html',
                           joueurs=noms_joueurs,
                           tableau=tableau_final)




