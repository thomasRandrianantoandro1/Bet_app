-- Suppression des tables dans l'ordre inverse des dépendances
DROP TABLE IF EXISTS pari_des_joueurs;
DROP TABLE IF EXISTS ticket_participants;
DROP TABLE IF EXISTS ticket_details;
DROP TABLE IF EXISTS ticket_commun;
DROP TABLE IF EXISTS single_bet;
DROP TABLE IF EXISTS matchs_selectionnes;
DROP TABLE IF EXISTS user;

-- Création des tables
CREATE TABLE user (
    id_user INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    role INTEGER NOT NULL
);

CREATE TABLE matchs_selectionnes (
    id_match INTEGER PRIMARY KEY AUTOINCREMENT,
    api_id_match INTEGER UNIQUE NOT NULL,
    equipe_domicile TEXT NOT NULL,
    equipe_exterieur TEXT NOT NULL
);

CREATE TABLE single_bet (
   id_single_bet INTEGER PRIMARY KEY AUTOINCREMENT,
   intitule TEXT NOT NULL,
   cote REAL NOT NULL,
   mise INTEGER NOT NULL,
   createur_id INTEGER NOT NULL,
   preneur_id INTEGER,
   statut_pari INTEGER DEFAULT 0,
   resultat INTEGER DEFAULT 0,
   date_de_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   FOREIGN KEY (createur_id) REFERENCES user (id_user),
   FOREIGN KEY (preneur_id) REFERENCES user (id_user)
);

CREATE TABLE ticket_commun (
    id_ticket INTEGER PRIMARY KEY AUTOINCREMENT,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    statut INTEGER DEFAULT 0,
    id_gagnant INTEGER,
    FOREIGN KEY (id_gagnant) REFERENCES user (id_user)
);

CREATE TABLE ticket_details (
    id_detail INTEGER PRIMARY KEY AUTOINCREMENT,
    id_ticket INTEGER NOT NULL,
    equipe_domicile TEXT NOT NULL,
    equipe_exterieur TEXT NOT NULL,
    api_id_match INTEGER NOT NULL,
    FOREIGN KEY (id_ticket) REFERENCES ticket_commun (id_ticket)
);

CREATE TABLE ticket_participants (
    id_ticket INTEGER NOT NULL,
    id_user INTEGER NOT NULL,
    mise INTEGER NOT NULL DEFAULT 20,
    PRIMARY KEY (id_ticket, id_user),
    FOREIGN KEY (id_ticket) REFERENCES ticket_commun (id_ticket),
    FOREIGN KEY (id_user) REFERENCES user (id_user)
);

CREATE TABLE pari_des_joueurs (
    id_pari_joueur INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user INTEGER NOT NULL,
    id_ticket INTEGER NOT NULL,
    api_id_match INTEGER NOT NULL,
    score_dom INTEGER NOT NULL,
    score_ext INTEGER NOT NULL,
    vainqueur_match INTEGER NOT NULL,
    resultat INTEGER NOT NULL, -- 0 si le pari est pas bon 1 si le score est bon 2 si score exact
    FOREIGN KEY (id_user) REFERENCES user (id_user),
    FOREIGN KEY (id_ticket) REFERENCES ticket_commun(id_ticket)
);
