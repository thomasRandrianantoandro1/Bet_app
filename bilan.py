from flask import Blueprint, render_template

from .auth import login_required
from .db import get_db

bp = Blueprint('bilan', __name__, url_prefix='/bilan')


@bp.route('/')
def index():
    db = get_db()
    # Récupération de tous les utilisateurs pour initialiser le dictionnaire
    users = db.execute('SELECT id_user, nom FROM user').fetchall()

    bilans = {u['id_user']: {'nom': u['nom'], 'solde': 0} for u in users}
    dettes_croisees = {}

    def ajouter_dette(debiteur, creancier, montant):
        if debiteur == creancier or montant <= 0: return
        key = (debiteur, creancier)
        dettes_croisees[key] = dettes_croisees.get(key, 0) + montant

    # --- 1. PARIS UNIQUES (Variables) ---
    # On calcule les gains selon le statut_pari (1 pour créateur gagne, 0 pour preneur gagne)
    paris_uniques = db.execute('''
        SELECT createur_id, preneur_id, cote, mise, statut_pari 
        FROM single_bet 
        WHERE preneur_id IS NOT NULL AND statut_pari IN (0, 1)
    ''').fetchall()

    for p in paris_uniques:
        gain_net = p['mise'] * (p['cote'] - 1)
        if p['statut_pari'] == 1:
            ajouter_dette(p['preneur_id'], p['createur_id'], gain_net)
            bilans[p['createur_id']]['solde'] += gain_net
            bilans[p['preneur_id']]['solde'] -= gain_net
        elif p['statut_pari'] == 0:
            ajouter_dette(p['createur_id'], p['preneur_id'], p['mise'])
            bilans[p['createur_id']]['solde'] -= p['mise']
            bilans[p['preneur_id']]['solde'] += p['mise']

    # --- 2. COMBINÉS (Mise fixe 20$) ---
    # Chaque perdant doit 20$ au gagnant identifié dans id_gagnant
    tickets_clos = db.execute('SELECT id_ticket, id_gagnant FROM ticket_commun WHERE statut = 1').fetchall()

    for t in tickets_clos:
        participants = db.execute('SELECT id_user FROM ticket_participants WHERE id_ticket = ?',
                                  (t['id_ticket'],)).fetchall()
        for part in participants:
            if part['id_user'] != t['id_gagnant']:
                ajouter_dette(part['id_user'], t['id_gagnant'], 20)
                bilans[t['id_gagnant']]['solde'] += 20
                bilans[part['id_user']]['solde'] -= 20

    # --- 3. SIMPLIFICATION DES DETTES ---
    dettes_finales = []
    traites = set()
    for (deb, cre), mt in dettes_croisees.items():
        if (deb, cre) in traites: continue
        inverse_mt = dettes_croisees.get((cre, deb), 0)
        diff = mt - inverse_mt

        if diff > 0:
            dettes_finales.append({'debiteur': bilans[deb]['nom'], 'creancier': bilans[cre]['nom'], 'montant': diff})
        elif diff < 0:
            dettes_finales.append(
                {'debiteur': bilans[cre]['nom'], 'creancier': bilans[deb]['nom'], 'montant': abs(diff)})
        traites.add((deb, cre))
        traites.add((cre, deb))

    return render_template('historique/bilan.html', bilans=bilans.values(), dettes=dettes_finales)