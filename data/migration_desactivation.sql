-- Migration F1 : désactivation des comptes.
-- À exécuter une seule fois sur une base créée avant l'ajout de la colonne active.
-- Les comptes existants restent actifs (valeur par défaut TRUE).
ALTER TABLE Person
ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT TRUE;
