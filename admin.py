import functools
from datetime import datetime

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from select import select
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

import secrets
import string

import requests
from  datetime import datetime

api = '104548b7e9844531ad4f603265603027'

bp=Blueprint('admin', __name__,url_prefix='/admin')

def comparer_score(score_pari_dom,score_pari_ext,score_reel_dom,score_reel_ext):
    if score_reel_dom is None or score_reel_ext is None:
        return 0
    else:
        if score_pari_dom==score_reel_dom and score_pari_ext==score_reel_ext:
            return 2
        elif score_pari_dom>score_pari_ext and score_reel_dom>score_reel_ext:
            return 1
        elif score_pari_dom<score_pari_ext and score_reel_dom<score_reel_ext:
            return 1
        elif score_pari_dom==score_pari_ext and score_reel_dom==score_reel_ext:
            return 1
        else :
            return 0

@bp.route('/joueurs',methods=['GET','POST'])
def joueurs():
    db=get_db()

    if request.method == 'POST':
        print(request.form)
        nom=request.form['nom']
        role=request.form['role']
        alphabet = string.ascii_letters + string.digits
        token=''.join(secrets.choice(alphabet) for i in range(10))
        error=None

        if not nom:
            error='Il faut tout remplir.'
        if error is None:
            # db.execute('INSERT INTO user (nom,token,role) VALUES (?,?,?)',(nom,token,role))
            db.execute('INSERT INTO user (nom, token, role) VALUES (?, ?, ?)', (nom, token, role))
            db.commit()
            return redirect(url_for('admin.joueurs'))
        flash(error)
    joueurs=db.execute('SELECT * FROM user').fetchall()

    return render_template('admin/joueurs.html',joueurs=joueurs)


@bp.route('/joueurs/modifier_role/<int:id_user>', methods=['POST'])
def modifier_role(id_user):
    db = get_db()

    nouveau_role = request.form.get('role')

    if nouveau_role is not None:
        db.execute(
            'UPDATE user SET role = ? WHERE id_user = ?',
            (nouveau_role, id_user)
        )
        db.commit()
        flash("Rôle mis à jour !")

    return redirect(url_for('admin.joueurs'))

@bp.route('/validation_pari', methods=['GET','POST'])
def validation_pari():
    db=get_db()

    paris_admin_unique=db.execute('SELECT * FROM single_bet WHERE statut_pari=2 ').fetchall()

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
    ticket_data = db.execute('SELECT id_ticket FROM ticket_commun WHERE statut = 0').fetchone()
    id_du_ticket_actuel = ticket_data['id_ticket'] if ticket_data else None

    return render_template('admin/validation_pari.html',paris_admin_unique=paris_admin_unique,noms_joueurs=noms_joueurs,tableau_final=tableau_final,id_du_ticket_actuel=id_du_ticket_actuel)

@bp.route('/modifier_resultat_unique', methods=['POST'])
def modifier_resultat_unique():
    db=get_db()
    resultat=request.form['nouveau_resultat']
    id_single_bet=request.form['id_single_bet']

    if id_single_bet is not None:
        db.execute(
            'UPDATE single_bet SET statut_pari = ? WHERE id_single_bet = ?',(resultat, id_single_bet)
        )
        db.commit()
    db.execute(
        'DELETE FROM single_bet WHERE statut_pari = ?',(3,)
    )
    db.commit()
    return redirect(url_for('admin.validation_pari'))


@bp.route('/selection_matchs',methods=['GET','POST'])
def selection_matchs():
    return render_template('admin/selection_matchs.html')

@bp.route('/api/sauvegarder',methods=['POST'])
def sauvegarder_match():
    db=get_db()
    data=request.json

    try:
        db.execute(''' INSERT INTO matchs_selectionnes  (api_id_match, equipe_domicile, equipe_exterieur)
        VALUES (?,?,?) ''', (data['id'],data['home'],data['away'])  )
        db.commit()
        return {"status":"succes","message":"Match sauvé !"}
    except Exception as e:
        print(f"ERREUR SQL REELLE : {e}")
        return {"status":"error", "message":"Déjà sauvé"},400


@bp.route('/api/get_matchs/<league_id>')
def get_matchs(league_id):
    # L'URL doit être exacte : /v4/competitions/{ID}/matches
    url = f"https://api.football-data.org/v4/competitions/{league_id}/matches"
    headers = {'X-Auth-Token': '104548b7e9844531ad4f603265603027'}  # Remplace par ta vraie clé

    # On filtre pour n'avoir que les matchs d'aujourd'hui
    params = {
        'dateFrom': datetime.today().strftime('%Y-%m-%d'),
        'dateTo': datetime.today().strftime('%Y-%m-%d')
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        # L'API renvoie parfois une erreur si on n'a pas accès à la ligue
        if response.status_code != 200:
            return {"error": data.get('message', 'Erreur API')}, response.status_code

        return data  # Contient la clé 'matches'
    except Exception as e:
        return {"error": str(e)}, 500


@bp.route('/api/get_selection')
def get_selection():
    db = get_db()
    # On récupère les matchs déjà sauvés dans TA base SQLite
    rows = db.execute('SELECT * FROM matchs_selectionnes').fetchall()

    # On transforme les lignes SQL en liste de dictionnaires pour le JSON
    selection = [dict(row) for row in rows]
    return {"selection": selection}


@bp.route('/api/supprimer/<api_id>', methods=['POST'])
def supprimer_match(api_id):
    db = get_db()
    db.execute('DELETE FROM matchs_selectionnes WHERE api_id_match = ?', (api_id,))
    db.commit()
    return {"status": "success"}


@bp.route('/api/valider_selection_officielle', methods=['POST'])
def valider_selection_officielle():
    db = get_db()

    # 1. On récupère les matchs que tu as mis dans la sidebar
    selection = db.execute('SELECT * FROM matchs_selectionnes').fetchall()

    if not selection:
        return {"status": "error", "message": "Aucun match sélectionné"}, 400

    try:
        # 2. On crée le ticket parent
        cursor = db.execute('INSERT INTO ticket_commun (statut) VALUES (0)')
        id_ticket = cursor.lastrowid

        # 3. On bascule les matchs de la sidebar vers le ticket officiel
        for m in selection:
            db.execute('''
                INSERT INTO ticket_details (id_ticket, equipe_domicile, equipe_exterieur, api_id_match)
                VALUES (?, ?, ?, ?)
            ''', (id_ticket, m['equipe_domicile'], m['equipe_exterieur'], m['api_id_match']))

        # 4. On vide la table temporaire
        db.execute('DELETE FROM matchs_selectionnes')

        db.commit()
        return {"status": "succes", "message": "Le combiné a été publié !"}

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}, 500


@bp.route('/vainqueur_pari_combine/<int:id_ticket>')
def vainqueur_pari_combine(id_ticket):
    db = get_db()

    # 1. RÉCUPÉRATION DES SCORES RÉELS (API)
    # On récupère les IDs des matchs liés à ce ticket spécifique
    details = db.execute('SELECT api_id_match FROM ticket_details WHERE id_ticket = ?', (id_ticket,)).fetchall()
    if not details:
        flash("Aucun match trouvé pour ce ticket.")
        return redirect(url_for('admin.validation_pari'))

    ids_match_str = ",".join([str(d['api_id_match']) for d in details])
    url = f"https://api.football-data.org/v4/matches?ids={ids_match_str}"
    headers = {'X-Auth-Token': '104548b7e9844531ad4f603265603027'}  # Utilise ta variable api_key

    try:
        response = requests.get(url, headers=headers).json()
        matchs_api = response.get('matches', [])

        scores_reels = {}
        for m in matchs_api:
            s_dom = m['score']['fullTime']['home']
            s_ext = m['score']['fullTime']['away']

            # Sécurité : On vérifie si l'API a bien les scores et si le match est fini
            if m['status'] != 'FINISHED' or s_dom is None:
                flash(f"Impossible de valider : le match {m['homeTeam']['name']} n'est pas terminé.")
                return redirect(url_for('admin.validation_pari'))

            scores_reels[m['id']] = {'dom': s_dom, 'ext': s_ext}

        # 2. CALCUL DES POINTS ET MISE À JOUR DE L'HISTORIQUE INDIVIDUEL
        # On récupère tous les paris des joueurs pour ce ticket
        paris = db.execute('SELECT * FROM pari_des_joueurs WHERE id_ticket = ?', (id_ticket,)).fetchall()

        stats_joueurs = {}  # Structure : { id_user: {'pts': 0, 'exacts': 0} }

        for p in paris:
            u_id = p['id_user']
            if u_id not in stats_joueurs:
                stats_joueurs[u_id] = {'pts': 0, 'exacts': 0}

            # On récupère le score réel correspondant au match du pari
            reel = scores_reels.get(p['api_id_match'])
            if reel:
                # Utilisation de ta fonction de comparaison
                res_pts = comparer_score(p['score_dom'], p['score_ext'], reel['dom'], reel['ext'])

                # Mise à jour des compteurs pour le classement
                stats_joueurs[u_id]['pts'] += res_pts
                if res_pts == 2:
                    stats_joueurs[u_id]['exacts'] += 1

                # --- HISTORISATION INDIVIDUELLE ---
                # On enregistre le résultat (0, 1 ou 2) directement dans la ligne du pari
                db.execute('''
                    UPDATE pari_des_joueurs 
                    SET resultat = ? 
                    WHERE id_pari_joueur = ?
                ''', (res_pts, p['id_pari_joueur']))

        if not stats_joueurs:
            flash("Aucun pari n'a pu être traité.")
            return redirect(url_for('admin.validation_pari'))

        # 3. DÉTERMINATION DU VAINQUEUR (TIE-BREAKER)
        # On trie : Points (DESC), puis Scores Exacts (DESC)
        classement = sorted(
            stats_joueurs.items(),
            key=lambda x: (x[1]['pts'], x[1]['exacts']),
            reverse=True
        )

        id_gagnant = classement[0][0]  # L'ID du premier (le meilleur)
        best_pts = classement[0][1]['pts']
        best_exacts = classement[0][1]['exacts']

        # 4. CLÔTURE DU TICKET (VERS LA TABLE HISTORIQUE)
        # On enregistre le gagnant et on passe le statut à 1 (Fermé)
        db.execute('''
            UPDATE ticket_commun 
            SET id_gagnant = ?, statut = 1 
            WHERE id_ticket = ?
        ''', (id_gagnant, id_ticket))

        participants_ids = stats_joueurs.keys()
        for p_id in participants_ids:
            db.execute('''
                INSERT OR IGNORE INTO ticket_participants (id_ticket, id_user, mise)
                VALUES (?, ?, 20)
            ''', (id_ticket, p_id))
            
        db.commit()
        ticket = db.execute('SELECT id_ticket FROM ticket_commun WHERE statut = 0 ORDER BY id_ticket DESC').fetchone()

        id_ticket_actuel = ticket['id_ticket'] if ticket else None

        # Récupérer le nom du gagnant pour le message flash
        nom_gagnant = db.execute('SELECT nom FROM user WHERE id_user = ?', (id_gagnant,)).fetchone()['nom']
        flash(f"Félicitations à {nom_gagnant} ! Victoire avec {best_pts} pts et {best_exacts} scores exacts.")

    except Exception as e:
        db.rollback()
        flash(f"Erreur lors de la validation : {str(e)}")

    return redirect(url_for('admin.validation_pari'))