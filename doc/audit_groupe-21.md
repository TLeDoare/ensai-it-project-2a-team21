**Tableau de bord**

| Gravité | Nombre de constats |
|---|---|
| Critique | 1 |
| Élevée | 9 |
| Moyenne | 12 |
| Faible | 4 |

| Code audit | Description | Réaction |
|-|---|-|
| ER1-01 | le texte intégral de chaque document est écrit en clair dans le fichier de log | Fixé |
| ER1-02 | mode dégradé silencieux (fail-open) | Fixé |
| ER1-03 | le prompt demande des types que le vérificateur rejette | ... |
| ER1-04 | le gestionnaire d'erreur 422 renvoie et journalise le corps brut des requêtes | Fixé |
| ER1-05 | surface web, documentation et protections frontend désactivées | ... |
| ER2-01 | consommation non bornée, atteignable sans compte légitime | Fixé |
| ER2-02 | la clé est obligatoire pour démarrer, même sans LLM | Justifié |
| ER3-01 | réinitialisation de la base sans authentification et comptes par défaut commités | Justifié |
| ER3-02 | hachage de mot de passe inadapté | Fixé |
| ER3-03 | jetons de session permanents, stockés en clair, sans révocation | ... |
| ER3-04 | aucune protection contre la force brute, aucune politique de mot de passe | Justifié |
| ER3-05 | liste complète des utilisateurs exposée au rôle superviseur | Justifié |
| INJ-01 | le filtre d'injection décrit dans le rapport n'existe pas | ... |
| INJ-02 | aucun jeu adversarial exécuté, aucune CI | Fixé, et justifié |
| INJ-03 | la vérification de sortie ne peut pas détecter une omission | ... |
| INJ-04 | délimitation contournable et prompt contradictoire | ... |
| INJ-05 | aucune trace des tentatives d'injection dans la journalisation F4 | Fixé |
| INJ-06 | sur-caviardage et consommation pilotables par le document | Justifié |
| GEN-01 | le flux principal de caviardage est cassé à ce commit | Fixé |
| GEN-02 | architecture et asynchronisme | ... |
| GEN-03 | qualité de la détection | Fixé à 20% |
| GEN-04 | tests et CI | En cours de réglage et justifié |
| GEN-05 | robustesse et validation des entrées | ... |
| GEN-06 | dépendances | ... |
| GEN-07 | reproductibilité et configuration | ne comprends pas |
| GEN-08 | empreinte du document original | Fixé ? |