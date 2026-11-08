# Wireless Tags pour Home Assistant

Intégration **custom** (HACS) pour [wirelesstag.net](https://wirelesstag.net) / mytaglist.com, avec configuration **via l’UI** — plus besoin d’éditer `configuration.yaml`.

L’intégration officielle Home Assistant (`wirelesstag`) reste limitée au YAML. Ce dépôt propose une alternative installable en quelques clics.

## Fonctionnalités

- Config flow UI (e-mail + mot de passe)
- Découverte automatique de tous les tags du compte
- Capteurs : température, humidité, humidité du sol, luminosité, température ambiante
- Capteurs binaires : présence, mouvement, porte, froid/chaleur, trop sec/humide, fuite, batterie…
- Interrupteurs arm/disarm pour activer le monitoring (utile surtout pour le mouvement / les portes)
- Mises à jour cloud push + polling de secours configurable
- Traductions FR / EN

## Installation (HACS)

1. HACS → **⋮** → *Custom repositories*
2. URL : `https://github.com/nicdive/HA-wirelesstags`
3. Catégorie : **Integration**
4. Installer **Wireless Tags**, puis redémarrer Home Assistant
5. *Paramètres → Appareils et services → Ajouter une intégration → Wireless Tags*
6. Saisir vos identifiants wirelesstag.net

## Installation manuelle

Copier le dossier `custom_components/wirelesstags` dans le dossier `custom_components` de votre Home Assistant, puis redémarrer.

```text
config/
  custom_components/
    wirelesstags/
      __init__.py
      ...
```

## Configuration

Après l’ajout de l’intégration :

1. Chaque tag apparaît comme un **appareil**
2. Les entités supportées par le tag sont créées automatiquement
3. Options de l’intégration : intervalle de polling (le push cloud met déjà à jour en temps quasi réel)

> Pour recevoir les événements mouvement / porte en push, arme le switch **Armer mouvement** du tag concerné.

## Différence avec l’intégration native

| | Native (`wirelesstag`) | Cette intégration (`wirelesstags`) |
|---|---|---|
| Installation | Intégrée à HA | HACS / manuel |
| Configuration | YAML | UI |
| Découverte des tags | Conditions listées à la main | Automatique |
| Domaine | `wirelesstag` | `wirelesstags` |

Les deux peuvent coexister, mais ce n’est pas recommandé (doublons d’entités). Désactivez l’entrée YAML native si vous passez à cette version.

## Dépannage

- Vérifier e-mail / mot de passe sur [wirelesstag.net](https://www.wirelesstag.net)
- Si le Tag Manager est hébergé sur un autre sous-domaine cloud (ex. `my.wirelesstag.net`), la lib `wirelesstagpy` suit en général la redirection après login
- Logs : *Paramètres → Système → Journaux*, filtre `wirelesstags` / `wirelesstagpy`

## Licence

MIT. Wireless Sensor Tags est une marque de Cao Gadgets LLC.
