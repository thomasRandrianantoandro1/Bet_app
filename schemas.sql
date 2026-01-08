DROP TABLE IF EXISTS single_bet;
DROP TABLE IF EXISTS bet;
DROP TABLE IF EXISTS matchs;
DROP TABLE IF EXISTS player;
DROP TABLE IF EXISTS user;


CREATE TABLE user (
    id_user INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT  NOT NULL,
    token TEXT UNIQUE NOT NULL,
    role INTEGER NOT NULL
);

CREATE TABLE matchs (

    id_match INTEGER PRIMARY KEY,
    domicile TEXT UNIQUE NOT NULL,
    exterieur TEXT UNIQUE NOT NULL,
    score_domicile INTEGER NOT NULL,
    score_exterieur INTEGER NOT NULL

);

CREATE TABLE bet(
    id_bet INTEGER PRIMARY KEY AUTOINCREMENT,
    somme_mise INTEGER NOT NULL

);

CREATE TABLE single_bet(
   id_single_bet INTEGER PRIMARY KEY AUTOINCREMENT,
   intitule TEXT NOT NULL,
   cote REAL NOT NULL,
   mise INTEGER NOT NULL,
   createur_id INTEGER NOT NULL,
   preneur_id INTEGER,
   statut_pari INTEGER DEFAULT 0,
   resultat INTEGER DEFAULT 0,
   date_de_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


   FOREIGN  KEY (createur_id) REFERENCES user (id_user),
   FOREIGN  KEY (preneur_id) REFERENCES user (id_user)
);