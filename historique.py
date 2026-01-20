import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from .auth import login_required
from .db import get_db

bp = Blueprint('historique', __name__, url_prefix='/historique')


@bp.route('/pari_unique', methods=['GET', 'POST'])
@login_required
def pari_unique():
    db = get_db()

    # 1. Historique des paris uniques (déjà présent)
    historique = db.execute(
        """
        SELECT p.id_single_bet, p.intitule, p.cote, p.mise, p.statut_pari, p.preneur_id, 
               u1.nom AS nom_createur, u2.nom AS nom_preneur, p.resultat
        FROM single_bet p 
        LEFT JOIN user u1 ON p.createur_id = u1.id_user 
        LEFT JOIN user u2 ON p.preneur_id = u2.id_user 
        WHERE p.statut_pari = 1 
        ORDER BY p.date_de_creation DESC
        """
    ).fetchall()

    # 2. Récupération des tickets clos (Archives)
    archives = db.execute('''
        SELECT tc.id_ticket, tc.date_creation, u.nom as vainqueur
        FROM ticket_commun tc
        JOIN user u ON tc.id_gagnant = u.id_user
        WHERE tc.statut = 1
        ORDER BY tc.date_creation DESC
    ''').fetchall()

    # 3. Récupération des détails des paris pour l'historique combiné
    # On crée un dictionnaire : { id_ticket: { "match": { "joueur": "score" } } }
    details_archives = {}

    paris_clos = db.execute('''
        SELECT p.id_ticket, u.nom, p.score_dom, p.score_ext, 
               t.equipe_domicile || ' vs ' || t.equipe_exterieur as match_label
        FROM pari_des_joueurs p
        JOIN user u ON p.id_user = u.id_user
        JOIN ticket_details t ON p.id_ticket = t.id_ticket AND p.api_id_match = t.api_id_match
        JOIN ticket_commun tc ON p.id_ticket = tc.id_ticket
        WHERE tc.statut = 1
    ''').fetchall()

    for ligne in paris_clos:
        id_t = ligne['id_ticket']
        if id_t not in details_archives:
            details_archives[id_t] = {}

        match = ligne['match_label']
        if match not in details_archives[id_t]:
            details_archives[id_t][match] = {}

        details_archives[id_t][match][ligne['nom']] = f"{ligne['score_dom']} - {ligne['score_ext']}"

    # On récupère aussi la liste des noms des joueurs pour les colonnes du tableau
    noms_joueurs = sorted(list(set(l['nom'] for l in paris_clos)))

    return render_template('historique/pari_unique.html',
                           historique=historique,
                           archives=archives,
                           details_archives=details_archives,
                           noms_joueurs=noms_joueurs)
