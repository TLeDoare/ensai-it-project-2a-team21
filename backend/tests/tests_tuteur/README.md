# Corpus de test — détection et anonymisation de PII

Ce corpus sert à tester, contre des documents administratifs réalistes, un
pipeline de détection et d'anonymisation de données personnelles (PII —
*Personally Identifiable Information* : noms, adresses, téléphones, numéros
de sécurité sociale, IBAN…) dans des textes en français.

Il est composé de deux éléments :

```
documents/          68 fichiers .txt / .md à soumettre à votre pipeline
grille_verite/       la référence à laquelle comparer vos résultats
├── ground_truth_spans.csv     une ligne par PII attendue
├── ground_truth_spans.json    la même information, groupée par document
└── manifest_documents.csv     une ligne par document (métadonnées)
```

> **Toutes les données sont fictives.** Noms, adresses, IBAN, NIR, numéros de
> téléphone, plaques d'immatriculation et numéros de passeport sont inventés.
> Les IBAN et les NIR respectent la structure et la clé de contrôle réelles
> (modulo 97), ce qui les rend utilisables pour tester une regex de
> validation, mais ils ne correspondent à aucun compte ni à aucune personne
> réels. Les noms d'organismes suivent le modèle d'organismes publics réels
> sans en désigner un en particulier. La seule identité réelle du corpus est
> celle d'Emmanuel Macron, dans un unique document, comme exemple neutre d'une
> personnalité publique (voir plus bas, cercle 3).

## Comment l'utiliser

Pour chaque fichier de `documents/`, faites traiter son contenu par votre
pipeline et comparez la liste de PII obtenue à celle attendue pour ce document
dans `ground_truth_spans.csv` (ou `ground_truth_spans.json`, structurée par
document si c'est plus pratique pour votre code).

Une comparaison rigoureuse suppose de retrouver, pour chaque PII attendue,
une correspondance dans vos résultats sur le même **type** et sensiblement la
même **position** (au minimum un recouvrement du texte détecté avec le span
attendu — l'égalité stricte des positions est un critère plus strict que vous
pouvez choisir d'exiger ou non). Les PII détectées par vous mais absentes de
la grille sont des faux positifs ; celles de la grille absentes de vos
résultats sont des faux négatifs.

## Typologie des PII

La grille classe chaque PII selon trois niveaux, du plus consensuel au plus
discutable. C'est la convention adoptée **pour construire ce corpus** — elle
reflète des choix de conception, pas une norme. Rien n'oblige votre propre
projet à retenir la même liste de types ni le même découpage : à vous de
fixer vos propres règles de décision, y compris pour trancher différemment
sur tel ou tel cas-limite. Les colonnes `cercle` et `detection_attendue` de
la grille existent pour que vous puissiez filtrer ou repondérer les résultats
selon la politique que vous aurez choisie, pas pour l'imposer.

### Cercle 1 — PII les plus consensuelles

| Type | Exemple dans le corpus | Occurrences |
|---|---|---|
| `PERSON` | `Nathalie Roux` | 87 |
| `ADDRESS_FULL` | `27 rue Pasteur, 69003 Lyon` | 27 |
| `PHONE` | `06 24 68 72 56` | 27 |
| `EMAIL` | `farid.ouattara@ddets-test.gouv.fr` | 12 |
| `NIR` | `2 60 03 56 823 513 72` | 5 |
| `IBAN` | `FR76 2362 1172 6909 6654 2870 788` | 4 |

Ce sont les PII les plus directement identifiantes, indépendamment du
contexte : un format libre pour les noms et adresses, un format normalisé (et
vérifiable par calcul de clé) pour le NIR et l'IBAN. C'est le groupe pour
lequel le consensus sur le statut de PII est le plus large — ce qui n'en fait
pas pour autant une liste figée : d'autres projets élargissent ou restreignent
cet ensemble selon leur contexte d'usage.

### Cercle 2 — PII dont le caractère identifiant dépend du contexte

| Type | Exemple dans le corpus | Occurrences |
|---|---|---|
| `ORG` | `Caisse d'allocations familiales du Rhône` | 36 |
| `LOCATION` | `Lyon` | 23 |
| `DATE_OF_BIRTH` | `23 septembre 1984` | 11 |
| `LICENSE_PLATE` | `ZT-138-HH` | 4 |
| `PASSPORT` | `71FL86105` | 4 |

Leur caractère identifiant dépend du contexte : une commune de quelques
centaines d'habitants est identifiante, une métropole beaucoup moins ; une
organisation publique nationale l'est moins qu'une petite structure locale.
Le corpus les traite comme des PII à part entière, sans prononcer de règle sur
ce genre de nuance (seuil de population, type d'organisation…) : c'est un
choix de conception que chaque projet doit faire et documenter pour son propre
compte.

**Convention pour `DATE_OF_BIRTH`** : le span couvre uniquement la date
(`23 septembre 1984`), pas le mot déclencheur (« née le », « né le ») qui la
précède — c'est la date qui serait masquée, pas la tournure grammaticale.

### Cercle 3 — cas-limites

| Type | Exemple dans le corpus | Occurrences |
|---|---|---|
| `INTERNAL_ID` | `dossier n°2025-0451` | 24 |
| `JOB_TITLE` | `chef du service comptabilité` | 18 |
| `RELATIVE` | `mon fils` | 8 |
| `PUBLIC_FIGURE` | `Emmanuel Macron` | 1 |

ID de dossier internes, fonctions professionnelles, liens de parenté et
figures publiques sont des cas de discussion plus que des PII consensuelles :
un identifiant de dossier seul, sans nom associé, est un pseudo-identifiant ;
une fonction seule, sans organisation associée, est peu identifiante ; une
personnalité publique n'est pas une PII au sens strict, sa fonction étant
publique par nature. Le corpus les inclut malgré tout, précisément parce
qu'ils sont discutables : c'est l'occasion de décider, et de justifier, si
votre projet les traite comme des PII ou non — dans un sens comme dans
l'autre.

### Ce que `cercle` et `detection_attendue` signifient — et ne signifient pas

Ces deux colonnes documentent la manière dont **ce corpus a été construit**,
pas une exigence à satisfaire. Elles vous permettent de savoir, pour chaque
span, dans quel groupe de la typologie ci-dessus il a été rangé au moment de
la conception de la grille, et rien de plus. Que votre pipeline détecte tel
type de cercle 2 ou 3, ou choisisse de ne pas détecter tel type de cercle 1,
est un résultat à interpréter à la lumière de votre propre politique — pas un
écart à corriger. Ce sont ces colonnes qui vous permettent de recalculer vos
métriques selon la politique que vous avez retenue, plutôt que selon celle
implicite à la grille.

### Convention d'imbrication — le span le plus englobant gagne

Quand une PII de cercle 1 ou 2 en contient une autre, seule la plus englobante
est enregistrée dans la grille : dans `27 rue Pasteur, 69003 `**`Lyon`**, la
ville n'a pas de span `LOCATION` séparé puisqu'elle est comprise dans
l'`ADDRESS_FULL` ; dans `Mairie de `**`Quimper`**, il n'y a pas non plus de
span `LOCATION` séparé pour la ville comprise dans l'`ORG`. C'est une
convention délibérée, pas un oubli. Un détecteur qui émet en plus un span
`LOCATION` pour la ville imbriquée n'est pas nécessairement en tort — à
documenter dans vos propres règles — mais ne doit pas être compté comme un
faux positif strict sans lecture attentive du contexte.

## `ground_truth_spans.csv` — colonnes

| Colonne | Signification |
|---|---|
| `doc_id` | nom du fichier dans `documents/` |
| `span_id` | numéro de la PII dans ce document (ordre d'apparition) |
| `pii_type` | type de PII (voir ci-dessus) |
| `text` | texte exact de la PII (copie caractère pour caractère) |
| `start` / `end` | position dans le fichier, indices Python (0-indexé, `end` exclusif, sur la chaîne décodée en UTF-8) — `content[start:end] == text` |
| `cercle` | 1, 2 ou 3, selon la typologie ci-dessus |
| `detection_attendue` | libellé associé au cercle du span (`obligatoire`, `par_defaut (desactivable)`, `non_detectee_par_defaut (discutable)`) — décrit la convention retenue pour ce corpus, pas une exigence sur votre pipeline (voir « Ce que `cercle` et `detection_attendue` signifient » ci-dessus) |
| `note` | remarque ponctuelle sur ce span (occurrence répétée, cas de discussion…) |

## `manifest_documents.csv` — colonnes

Une ligne par document : `format` (`txt`/`md`), `categorie_longueur`
(`court`/`moyen`/`long`/`tres_long`), `nb_mots`, `nb_pii_total`,
`contient_pii` (`oui`/`non`), `type_document` (nature du document : courrier,
attestation, compte rendu de réunion…), et deux colonnes liées aux documents
de test de sécurité décrits plus bas : `test_adversarial` (`oui`/`non`) et
`type_attaque`.

## Documents sans PII

13 documents n'en contiennent aucune : procédures internes, foire aux
questions, règlement intérieur, mode opératoire logiciel, consignes
d'évacuation, charte d'accueil. Ils n'ont aucune ligne dans
`ground_truth_spans.csv` et portent `contient_pii = non` dans le manifeste. Un
bon détecteur doit y renvoyer une liste vide — ce sont vos tests de faux
positifs. Le mode opératoire logiciel en particulier (catégorie `long`,
vocabulaire technique, beaucoup de majuscules et de références numériques) est
pensé pour être le plus piégeux des treize.

## Documents de test de sécurité

17 documents, repérables par `test_adversarial = oui` dans le manifeste, sont
destinés à tester la résistance de votre pipeline à des tentatives de
manipulation glissées **dans le contenu du document lui-même** — et non dans
la façon dont vous interrogez votre propre système. Si votre pipeline s'appuie
sur un modèle de langage à un moment de la détection, un texte malveillant
recopié dans un document (un commentaire libre, une citation, une pièce
jointe retranscrite) peut chercher à détourner son comportement : lui faire
ignorer une instruction, changer de tâche, ou produire un résultat conforme en
apparence mais vide de tout contenu.

Ces 17 documents couvrent plusieurs familles de tentatives : instruction
directe de type « ignore les consignes précédentes », fausse autorité
(commentaire qui se présente comme une instruction système), tentative de
sortie de cadre (fermeture de balise falsifiée, changement de rôle demandé au
modèle), bascule de langue, bloc de code imitant une instruction système,
demande de réécriture du document avant analyse, submersion sous du texte
répétitif, format de sortie corrompu par une clé supplémentaire, faux exemple
présenté comme une consigne, condition narrative (« si tu lis ceci... »),
instruction encodée (base64), et mise en situation hypothétique indirecte.

Certains de ces documents sont des cas nus, centrés sur une unique PII
entourée du texte de la tentative. D'autres dissimulent la même tentative
dans un document administratif réaliste — signalement, réclamation, fiche de
renseignement — avec des PII différentes, pour vérifier que la résistance de
votre pipeline ne tient pas seulement à la reconnaissance d'un cas appris par
cœur.

Dans tous les cas, l'invariant à vérifier est le même : les PII réelles du
document doivent rester détectées malgré la tentative, et le texte de la
tentative ne doit ni apparaître comme une PII inventée dans votre résultat, ni
faire dévier le format de sortie attendu de votre pipeline.

## Longueur des documents

| Catégorie | Seuil (mots) | Documents |
|---|---|---|
| `court` | < 40 | 24 |
| `moyen` | 40–180 | 35 |
| `long` | 180–500 | 6 |
| `tres_long` | > 500 | 3 |

Les deux vrais documents longs sont un rapport annuel d'activité et un
rapport d'audit interne, dont la longueur vient du contenu et non d'un motif
répété. Le troisième document `tres_long` est un cas de test de sécurité par
submersion : sa longueur vient d'un bloc de texte répétitif inséré à dessein,
ce n'est pas un document à lire mais un test de résistance au bruit.

> **Calculez vos métriques par document plutôt qu'en poolant tout le
> corpus.** Le document le plus dense ne concentre que 4,8 % des PII du
> corpus, donc un pooling global reste raisonnable ici — mais une
> précision/rappel unique, calculée sur l'ensemble, mélange des documents de
> nature très différente (un SMS de douze mots, un rapport de plusieurs
> pages) et masque les écarts de comportement entre les deux. Ce sont
> précisément ces écarts qui sont informatifs sur votre détecteur. Le
> manifeste fournit `categorie_longueur` et `type_document` pour ventiler vos
> résultats.
