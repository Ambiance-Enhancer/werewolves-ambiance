# werewolves-ambiance

Yo, alors le but de ce repository c'est de créer un générateur de bruits ambiants lors d'une partie de Loup-Garous par **détection vocale**.
Dans un soucis de simplicité, nous commencerons par une partie en **français** uniquement !

## Composition du projet

Il y a plusieurs parties au projet :

- Détection vocale --> Retranscription texte
  
- Création d'une bibliothèques de sons ambiants --> A débattre du format. Pour commencer simple on peut simplement trouver des bruitages, musiques symboliques à jouer.
  
- Création d'une base de données : Afin d'intéragir entre la détection vocale et la bibliothèque de sons ambiants, on peut setup une petite base de données (SQLlite ou SQLAlchemy pour migrer vers Postgres).

- Suivi de la partie de loup-garou :
  1) On suit la partie de loup garou grâce à un input en début de parties des rôles composant la partie. Comme la partie est ordonnée on peut retrouver rapidement grâce à la détection vocale OU une interface type Deezer pour que le MJ puisse faire before / next.
  2) On ignore la composition car on peut la déduire avec les inputs vocaux (ainsi que l'ordre prédéfini des rôles). On peut entraîner un modèle qui trouve quel rôle est en train de jouer (RLHF envisageable et simple à mettre en place).
 
- Création d'une interface UI/UX.

- Lancement automatique de sons d'ambiance depuis l'appareil.

## Organisation

- 1 branche par ticket
- les noms des tickets dans les commits
- On se fait un ptit call de temps en temps
- Alexandre n'a pas le droit de merge.

## Bon on verra la suite
