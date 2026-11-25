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
| ER1-03 | le prompt demande des types que le vérificateur rejette | Fixé |
| ER1-04 | le gestionnaire d'erreur 422 renvoie et journalise le corps brut des requêtes | Fixé : ni les logs ni la réponse 422 ne contiennent les valeurs envoyées ; seuls le champ, le message et le type d'erreur sont renvoyés |
| ER1-05 | surface web, documentation et protections frontend désactivées | Justifié : CORS et XSRF désactivés pour fonctionner derrière le proxy d'Onyxia, à réactiver en production |
| ER2-01 | consommation non bornée, atteignable sans compte légitime | Fixé |
| ER2-02 | la clé est obligatoire pour démarrer, même sans LLM | Fixé : le client LLM n'est créé qu'au moment d'un appel au LLM |
| ER3-01 | réinitialisation de la base sans authentification et comptes par défaut commités | Fixé pour la réinitialisation (administrateur uniquement) ; comptes de test justifiés pour la démonstration |
| ER3-02 | hachage de mot de passe inadapté | Fixé |
| ER3-03 | jetons de session permanents, stockés en clair, sans révocation | Fixé |
| ER3-04 | aucune protection contre la force brute, aucune politique de mot de passe | Partiellement fixé : politique de mot de passe imposée (8 caractères, majuscule, minuscule, chiffre, caractère spécial) ; pas de limite du nombre d'essais, limite assumée |
| ER3-05 | liste complète des utilisateurs exposée au rôle superviseur | Justifié |
| INJ-01 | le filtre d'injection décrit dans le rapport n'existe pas | Fixé |
| INJ-02 | aucun jeu adversarial exécuté, aucune CI | Fixé, et justifié |
| INJ-03 | la vérification de sortie ne peut pas détecter une omission | Fixé |
| INJ-04 | délimitation contournable et prompt contradictoire | Fixé |
| INJ-05 | aucune trace des tentatives d'injection dans la journalisation F4 | Fixé |
| INJ-06 | sur-caviardage et consommation pilotables par le document | Justifié |
| GEN-01 | le flux principal de caviardage est cassé à ce commit | Fixé |
| GEN-02 | architecture et asynchronisme | Fixé : regex et LLM lancés en parallèle (asyncio.gather), regex dans des fils séparés |
| GEN-03 | qualité de la détection | Fixé : 97 % de rappel et 100 % de précision avec gemma4-26b-moe (jeu d'essai de 32 données, 3 passages) |
| GEN-04 | tests et CI | Fixé : 182 tests unitaires lancés par la CI (couverture 84 % ; 210 tests et 92 % de couverture avec les tests DAO) |
| GEN-05 | robustesse et validation des entrées | Fixé : taille maximale (413), encodage UTF-8 (415), validation Pydantic des e-mails et mots de passe |
| GEN-06 | dépendances | Fixé : versions figées dans uv.lock |
| GEN-07 | reproductibilité et configuration | Fixé : .env.example, uv.lock et procédure d'installation complète dans le README |
| GEN-08 | empreinte du document original | Fixé : HMAC-SHA256 avec une clé secrète (DOC_HASH_SECRET) |
