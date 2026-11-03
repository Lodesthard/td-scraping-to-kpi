# Réflexions — TD3, du scraping à un KPI mesurable

Réponses aux questions de réflexion des étapes 1 à 6, basées sur l'extraction réelle du 2026-11-03 (12 offres Indeed, qwen3:8b).

## 1. Pourquoi un échec silencieux de `robots.txt` est pire qu'un échec bruyant (CM3)

Une étape qui plante s'arrête et me prévient : en lançant `scrape_demo.py`, j'ai
eu une `NameResolutionError` sur `fr.wikipedia.org` (DNS momentanément
indisponible). J'ai compris tout de suite qu'aucune donnée n'avait été récupérée.
À l'inverse, `rp.read()` derrière un proxy renvoie « tout est interdit » sans
erreur : le pipeline conclut faussement quelque chose sur les *règles d'accès*
elles-mêmes, et cette fausse conclusion se retrouve dans la trace de provenance
(« vérifié : interdit ») comme si c'était un fait. L'argument de provenance du CM3,
c'est de pouvoir dire d'où vient une donnée et à quelles conditions on l'a obtenue.
Un contrôle de conformité qui échoue en silence produit une provenance fausse, ce
qui est pire que pas de provenance du tout. Dans l'autre sens, la même panne
silencieuse pourrait aussi faire croire qu'on a vérifié alors que non.

## 2. France Travail vs. échantillon jobspy : la vraie différence de risque

L'API France Travail est de la donnée publique sous licence de réutilisation :
le droit de copier, transformer et republier est écrit noir sur blanc. Mon
`jobs_sample.csv` vient d'Indeed via jobspy (les 12 offres analysées ont toutes
`site = indeed`). Les CGU d'Indeed interdisent l'extraction automatisée et la
redistribution, et les descriptions sont des textes rédigés par les entreprises
(droit d'auteur). Le risque n'est donc pas technique, il est juridique et
contractuel : je détiens localement une copie que je n'ai pas le droit de
diffuser. Le statut public/privé change le risque mais pas la règle. Un dépôt
public *redistribue* à tout le monde, c'est l'acte interdit. Un dépôt privé
limite l'exposition, mais reste une copie hébergée chez un tiers (GitHub),
partageable avec des collaborateurs, et qui devient publique au moindre changement
de visibilité. C'est pour ça que le `.gitignore` exclut ces fichiers quel que soit
le statut du dépôt.

## 3. Pourquoi « texte libre → compétences » convient à un LLM, et le suivi de candidatures non (CM5)

Extraire des compétences d'une description, c'est interpréter du langage naturel
désordonné (français/anglais, listes, paragraphes, jargon) : aucune règle fixe ne le
fait bien, et une erreur du modèle reste vérifiable en relisant le texte source.
Un enregistrement de mes propres actions (quelle candidature j'ai envoyée, à quelle
date) est un **fait** dont je suis la seule source de vérité : il n'y a rien à
interpréter. Un LLM ne peut qu'y ajouter un risque d'invention, sans aucun gain.
La distinction du CM5 : un LLM a sa place quand il transforme une entrée ambiguë
en structure *contrôlable*, pas quand il remplacerait l'enregistrement d'un fait
certain par une supposition.

## 4. Incohérence de mise en forme : prédiction et vérification

**Prédiction :** la même compétence avec une casse ou une forme différente d'un
appel à l'autre (« Computer Vision » / « computer vision », « CI/CD » / « CI/CD
pipelines », « AWS » / « Amazon Web Services »).

**Trouvé dans mon `extracted.json` :** oui.
- `"Computer Vision"` (CarCutter) et `"Computer vision"` (Diffusely). Dans
  `kpi.json`, elles apparaissent comme deux compétences comptées 1 fois chacune
  au lieu d'une compétence comptée 2 fois.
- Variante de forme : `"CI/CD"` (Astemo), `"GitLab CI/CD"` (Hilti) et
  `"CI/CD pipelines"` (GE Vernova) désignent la même pratique sous trois libellés.

Le cas CarCutter / Diffusely est encore plus parlant : les deux descriptions sont
**identiques à 99,7 %** (même annonce publiée sous deux noms d'entreprise). Avec le
même prompt et le même modèle, l'une donne « Computer Vision » sans Python, l'autre
« Computer vision » avec Python. L'incohérence ne vient donc pas des données mais
de l'extraction elle-même.

## 5. La passe critique : pourquoi c'est du human-in-the-loop, et pourquoi sur `extracted.json` (CM5)

C'est du human-in-the-loop parce qu'un humain compare la sortie brute du modèle au
texte source *avant* qu'elle ne serve à une décision, et peut la corriger. Elle doit
porter sur `extracted.json` car c'est le seul fichier où chaque compétence est encore
rattachée à son offre. Dans `kpi.json`, une hallucination ou un oubli est déjà fondu
dans un pourcentage : impossible de savoir quelle offre est fausse, ni même qu'il y a
une erreur.

En relisant moi-même `extracted.json` face aux textes complets, j'ai trouvé trois
erreurs réelles :
- **Doublon** : CarCutter et Diffusely sont la même annonce, comptée deux fois
  (elle gonfle « AI », « 360° video », « SaaS », « Docker »).
- **Oublis dus à la troncature** : `MAX_CHARS = 1500` ne donne au modèle que le
  début de chaque annonce, souvent la présentation de l'entreprise. Python apparaît
  dans le texte complet de **8 offres sur 12**, mais dans les 1 500 premiers
  caractères d'**une seule** (Astemo). BCG ressort avec une liste vide alors que son
  annonce demande Python plus loin.
- **Compétence non fondée** : Python est extrait pour Diffusely et le CEA alors
  qu'il n'apparaît pas dans les 1 500 caractères envoyés au modèle. C'est juste
  dans les faits (le texte complet le mentionne), mais le modèle l'a deviné, pas lu.

**Quatrième erreur, sur les fautes de frappe des annonces :** le modèle les traite
de façon incohérente.
- Chez Solutionix, le texte source dit « **Azrue** Active Directory » : le modèle
  a corrigé en silence et renvoyé « Azure Active Directory ».
- Chez Hilti, le texte dit « AWS **Bedrocks** » (puis « AWS Bedrock » plus loin) :
  le modèle a recopié la faute, « Bedrocks », et sans le préfixe « AWS ».

Dans le premier cas, la sortie ne recopie plus le texte : on ne peut plus vérifier
mot pour mot qu'une compétence vient de l'annonce. Dans le second cas, « Bedrocks »
et « Bedrock » deviendraient deux compétences distinctes dès qu'une autre annonce
écrit correctement le nom. Seule une relecture de `extracted.json` face au texte
source le montre ; dans `kpi.json`, les deux erreurs sont invisibles.

## 6. Ma compétence cible, et quel KPI je croirais (CM2)

**Mon choix, avant de voir le chiffre : « AI ».** Les intitulés de l'échantillon
(Computer Vision, Forward Deployed AI Engineer, generative AI au CEA, AI/Geometry
chez Synopsys) montrent que l'IA est la demande qui monte. Pour un comité
pédagogique, c'est la question stratégique : faut-il renforcer l'IA dans la
maquette ?

**Résultats :** « python » = 25 % (3/12), « AI » = 41,7 % (5/12).

**Je ne ferais confiance à aucun des deux** pour dire au comité « les étudiants
doivent apprendre X ». Le KPI Python est faux d'un facteur 2,7 à cause de la
troncature (25 % mesuré contre 67 % dans les textes complets). Le KPI AI compte deux
fois la même annonce (36 % une fois dédoublonné), repose sur une recherche de
sous-chaîne (« ai » matcherait aussi « Maintenance », « Email » ou « Tailwind »), et
mesure sur 12 annonces Indeed alors que l'échantillon complet en contient 531. Un
chiffre défendable demanderait au minimum le texte complet, un dédoublonnage, la
normalisation des libellés et un échantillon plus large.

## 7. Que peut-on reconstituer à partir de `kpi.json` seul ? (CM3/CM6)

`kpi.json` ne contient ni titre, ni entreprise, ni URL, ni texte : ces champs sont
dans `extracted.json` mais `compute_kpi()` ne les recopie volontairement pas. Il ne
publie que des comptages. C'est un choix de conception délibéré pour les champs
d'identification.

Mais l'anonymat n'est pas total, et là c'est de la chance : `top_skills` publie aussi
des compétences rares, comptées 1 ou 2 fois. « 360° video » + « Computer Vision » +
« SaaS » suffisent à retrouver l'annonce CarCutter/Diffusely par une recherche sur
Indeed. « HIL » + « CAPL » + « FlexRay » désigneraient de même l'offre Astemo. Pour
le garantir vraiment, il faudrait ne publier que les compétences présentes dans au
moins *k* offres (par ex. k = 3), comme un seuil de k-anonymat.

## 8. À qui s'adresse ce tableau de bord ? (CM1)

En l'état, il s'adresse **à moi et à l'enseignant** : le titre « Scraping to KPI
lab » et la description qui renvoie à `data/extracted.json` et `compute_kpi.py`
parlent du TP, pas d'une décision. Le lien vers `extracted.json` pointe même vers un
fichier qui n'est pas publié, donc inaccessible au lecteur. Pour un comité
pédagogique, je remplacerais la description par :

> « Part des offres d'ingénieur récentes (échantillon de 12 annonces Indeed,
> novembre 2026) qui demandent des compétences en IA : indicateur exploratoire pour
> décider s'il faut renforcer l'IA dans la maquette, à confirmer sur un échantillon
> plus large. »

## 9. Mon second KPI : part des offres demandant au moins un fournisseur cloud

**Définition** (`compute_cloud_kpi()` dans `scripts/compute_kpi.py`) : proportion
d'offres *distinctes* dont les compétences extraites citent au moins un fournisseur
cloud public (AWS, Azure, GCP). Elle diffère du KPI de l'étape 4 sur trois points :
- **dédoublonnage** par intitulé avant le calcul (CarCutter/Diffusely comptés une
  seule fois) : 11 offres au lieu de 12 ;
- **liste fermée d'alias** par fournisseur (nom + services phares sans ambiguïté :
  `S3`, `SageMaker`, `Redshift`, `CloudWatch`, `BigQuery`…) au lieu d'une seule
  chaîne ; j'ai volontairement exclu `Glue`, `Lambda` ou `Athena` (qui ne veulent
  dire AWS qu'en contexte) et `Intune` (Microsoft, mais pas une compétence Azure) ;
- **mot entier** au lieu de sous-chaîne : « ai » ne peut plus matcher
  « Maintenance ».

**Résultat :** 27,3 % (3/11) — AWS 2, Azure 1, GCP 0.

**Contrôle sur le texte complet** (fait en local sur `jobs_sample.csv`, non publié) :
même règle appliquée aux descriptions entières → **3/11 aussi**. Le chiffre ne
bouge pas, mais le détail est faux : Hilti cite aussi Azure plus loin dans
l'annonce (Azure devrait valoir 2), et l'AWS de CarCutter n'est pas dans les 1 500
caractères envoyés au modèle — il l'a deviné, exactement comme Python pour le CEA.

**Comparaison.** Le KPI « AI » de l'étape 4 repose sur un mot vague, une
sous-chaîne et un doublon, et je l'ai vu passer de 41,7 % à 36 % rien qu'en
retirant ce doublon ; le KPI cloud a une définition fermée et vérifiable, et il
donne le même résultat sur l'extraction tronquée et sur le texte complet. C'est
donc à lui que je ferais confiance pour une vraie décision (par ex. « faut-il un
module cloud dans la maquette ? »), mais seulement comme ordre de grandeur : sur
11 annonces, une offre de plus ou de moins déplace le chiffre de 9 points.
