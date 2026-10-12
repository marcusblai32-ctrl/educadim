# Références, récompenses et avis — EducaDim

Cette fonctionnalité ajoute le parrainage, les points, les demandes de retrait,
les avis modérés et le carrousel de l’équipe sans remplacer les autres écrans.
Les données restent conservées quand une fonction est désactivée.

## Activation des fonctions

Après les migrations, ouvrez **Administration → Récompenses** (`/fr/parrainage/admin/flags/`)
ou **Administration Django → Activations de fonctionnalités**. Les six
commutateurs contrôlent indépendamment :

- `referral_system` : codes et suivi des invitations.
- `points_system` : soldes, transactions, remises et conversion en points.
- `discount_system` : remise configurable sur les cours payants.
- `rating_system` : soumission, modération et affichage des avis.
- `staff_carousel` : profils actifs sur la page d’accueil.
- `withdrawal_system` : demandes et traitement administratif des retraits.

Un indicateur désactivé masque ses liens et sections, rend ses pages
indisponibles et bloque les opérations associées. Les lignes déjà enregistrées
ne sont pas supprimées.

## Parrainage et récompenses

Un utilisateur connecté trouve son lien dans **Mes points**. Le visiteur
enregistre l’invitation en suivant le lien et le code est appliqué à sa prochaine
inscription. Le système rejette l’auto-parrainage et ne rattache pas un compte
déjà lié à un autre parrain.

Une récompense d’achat n’est déclenchée que lorsqu’une inscription payante
MonCash/NatCash passe de `pending` à `active`, c’est-à-dire après vérification.
Les inscriptions gratuites, les abonnements et les inscriptions manuelles ne
créent pas de récompense d’achat. Le montant est le prix du cours, après la
remise de points configurée au moment de la confirmation.

Les paramètres de `/fr/parrainage/admin/config/` règlent le mode points,
espèces ou les deux, les points d’inscription/premier achat/achats suivants,
les pourcentages de récompense, le seuil et le pourcentage de remise, et le
minimum de retrait. Les niveaux de conversion points → HTG sont gérés dans
**Niveaux**; aucun taux monétaire n’est prérempli. Un utilisateur peut demander
soit la conversion de points, soit le retrait de son solde en espèces déjà
crédité.

Les récompenses et transactions sont idempotentes par identifiant d’inscription
et conservées dans leur historique. Les demandes utilisent une réservation de
points : un refus restitue les points; une approbation enregistre le statut,
mais le paiement MonCash/NatCash est effectué manuellement hors de l’application.

## Avis des apprenants

Les avis soumis restent en attente. Un administrateur les approuve dans
**Administration Django → Avis**. Seuls les avis approuvés apparaissent dans
le carrousel de la page d’accueil. La fenêtre de demande d’avis est limitée
localement à une fois par semaine par navigateur.

## Équipe

Gérez les profils dans **Administration Django → Membres du personnel**. Seuls
les membres actifs apparaissent, selon `display_order`, dans le carrousel de la
page d’accueil. La photo est facultative.

## Vérifications de déploiement

Appliquez les migrations avec `python manage.py migrate --run-syncdb`, puis exécutez
`python manage.py test referrals`. Configurez les niveaux de retrait et les
pourcentages métier avant d’activer ces fonctions en production.
