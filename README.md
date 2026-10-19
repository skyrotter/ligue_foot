# ⚽ Ligue Foot — Home Assistant Integration

Intégration Home Assistant pour suivre la **Ligue 1** et la **Ligue 2** en temps réel.
Données gratuites via ESPN, sans clé API.

[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/skyrotter/ligue_foot.svg)](https://github.com/skyrotter/ligue_foot/releases)

---

## 🚀 Quick start

1. Installe l'intégration via **HACS**
2. Redémarre Home Assistant
3. Va dans **Paramètres → Appareils & Services → Ajouter une intégration → Ligue Foot**
4. Choisis la ligue (Ligue 1 ou Ligue 2)
5. Choisis ton équipe favorite
6. Répète depuis l'étape 3 pour ajouter d'autres équipes

---

## 📦 Ce que tu obtiens par équipe

### Capteurs
| Entité | Description |
|---|---|
| `sensor.xxx_prochain_match` | Date + détails du prochain match |
| `sensor.xxx_classement` | Position dans le classement + tableau complet |
| `sensor.xxx_forme` | 5 derniers résultats (W/D/L) |
| `sensor.xxx_sync` | État de synchronisation ESPN |

### Capteurs binaires
| Entité | Description |
|---|---|
| `binary_sensor.xxx_match_en_cours` | ON si un match est live |
| `binary_sensor.xxx_match_aujourd_hui` | ON si un match a lieu aujourd'hui |
| `binary_sensor.xxx_match_demain` | ON si un match a lieu demain |

### Calendrier
- `calendar.xxx_ligue_1` — Calendrier des matchs (intégrable dans le dashboard calendrier HA)

---

## 🔔 Notifications & automatisations

### Blueprints inclus
- **Rappel avant match** — Notifie X minutes avant le coup d'envoi
- **But !** — Notifie à chaque but, avec animation lumières (Hue, Ambilight…)

### Événements HA disponibles
```yaml
ligue_foot_goal
ligue_foot_kickoff
ligue_foot_match_finished
ligue_foot_red_card
```

### Exemple d'automatisation
```yaml
trigger:
  - platform: event
    event_type: ligue_foot_goal
action:
  - service: light.turn_on
    target:
      entity_id: light.salon
    data:
      flash: short
      color_name: green
```

---

## 💡 Compatibilité lumières

Fonctionne avec toutes les entités `light.*` de Home Assistant :
- **Philips Hue**
- **Ambilight** (Philips TV)
- Tout autre équipement Zigbee, Z-Wave, Wi-Fi

---

## ⚙️ Options

Après installation, configure dans **Paramètres → Appareils & Services → Ligue Foot → Configurer** :

- Notifications : coup d'envoi, but, carton rouge, fin de match
- Service de notification (ex: `notify.mobile_app_mon_telephone`)
- Plage de silence (ex: 23:00–07:00)

---

## 🛠️ Dépannage

| Problème | Solution |
|---|---|
| `sensor.sync` = `rate_limited` | ESPN a temporairement limité les requêtes. Les données reprennent automatiquement. |
| `sensor.sync` = `provider_unavailable` | ESPN est hors ligne. Vérifie ta connexion et attends. |
| Calendrier vide | Redémarre HA (pas seulement recharger l'intégration) après une mise à jour. |

---

## 📝 Licence

GPL-3.0 — [@skyrotter](https://github.com/skyrotter)
