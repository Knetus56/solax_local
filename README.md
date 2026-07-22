# SolaX Local - Intégration Home Assistant

Une intégration [Home Assistant](https://www.home-assistant.io/) pour contrôler et monitorer votre onduleur **SolaX** en local via le protocole HTTP.

## 🌟 Fonctionnalités

- 📊 **Monitoring en temps réel** : Puissance MPPT, production d'énergie, température
- 🔄 **Contrôle de l'onduleur** : Allumage/extinction via switch
- 📈 **Tracking de production** : Production du jour et cumulative
- 🕐 **Historique** : Timestamp de la dernière mise à jour
- 🌍 **Support multi-inverter** : X1 Micro 2-in-1 et autres
- 🔐 **Connexion locale** : Pas de cloud, entièrement en local
- 🇫🇷 **Interface localisée** : Français et anglais

## 📋 Capteurs (Sensors)

| Capteur | Description | Unité |
|---------|-------------|-------|
| `mppt1` | Puissance MPPT 1 | W |
| `mppt2` | Puissance MPPT 2 | W |
| `mppt_total` | Puissance totale MPPT | W |
| `temp` | Température de l'onduleur | °C |
| `prod_auj` | Production du jour | kWh |
| `prod_total` | Production totale cumulative | kWh |
| `mode` | Mode de fonctionnement | WaitMode/CheckMode/NormalMode |
| `ip` | Adresse IP de l'onduleur | - |
| `num_inverter` | Numéro de série | - |
| `last_update` | Dernière mise à jour | timestamp |

## 🔌 Entités de Contrôle

- **Binary Sensor** : État en ligne/hors ligne
- **Switch** : Allumage/extinction de l'onduleur

## 🚀 Installation

### Prérequis

- Home Assistant 2023.12+
- Accès réseau à l'onduleur SolaX
- Adresse IP et numéro de série de l'onduleur

### Via HACS (recommandé)

1. Ouvrir Home Assistant
2. Aller à **HACS** > **Intégrations**
3. Chercher "SolaX Local"
4. Cliquer **Installer**
5. Redémarrer Home Assistant

### Installation manuelle

1. Télécharger la dernière [version](https://github.com/Knetus56/solax_local/releases)
2. Extraire dans `custom_components/solax_local/`
3. Redémarrer Home Assistant

## ⚙️ Configuration

### Via interface Home Assistant

1. **Paramètres** > **Appareils et services** > **Intégrations**
2. Cliquer **Créer une intégration**
3. Chercher et sélectionner **SolaX Local**
4. Remplir les informations :
   - **IP** : Adresse IP de l'onduleur (ex: `192.168.1.100`)
   - **Type d'onduleur** : Sélectionner le modèle
   - **Numéro de série** : Numéro de série de l'onduleur
   - **Intervalle de scan** (optionnel) : Fréquence de mise à jour en secondes (défaut: 300s)

## 🔧 Configuration avancée

### Intervalle de mise à jour

Par défaut, l'intégration interroge l'onduleur toutes les **300 secondes** (5 minutes). Vous pouvez l'ajuster lors de la configuration.

### Entités DIAGNOSTIC

Les entités suivantes sont masquées par défaut (onglet Avancé) :
- État du mode
- Adresse IP
- Numéro de série
- Dernière mise à jour

Pour les afficher : **Paramètres** > **Appareils et services** > Sélectionner le device > **Afficher les entités masquées**


### Les capteurs affichent "Inconnu"

- Vérifier que l'adresse IP est correcte
- Vérifier que l'onduleur est **en ligne** et **alimenté**
- Vérifier la **connectivité réseau** entre HA et l'onduleur
- Augmenter l'`intervalle de scan` en cas de timeout réseau

### L'intégration ne charge pas

- Vérifier les logs : **Paramètres** > **Système** > **Journaux**
- Chercher les erreurs de connexion
- Redémarrer Home Assistant

### Le device n'affiche pas le modèle

- Cela signifie que le modèle sélectionné n'est pas reconnu
- Vérifier la sélection lors de la configuration



## 📦 Versions

- **v1.1.0** (2026-07-22) - Fix clés MPPT et initialisation du modèle

## 📄 Licence

Ce projet est sous licence [MIT](LICENSE)

## 🙏 Remerciements

- https://github.com/CurlyMoo grace a son reverse ici : https://github.com/squishykid/solax/issues/191
