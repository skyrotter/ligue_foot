# ⚽ Ligue Foot — Home Assistant Integration

Intégration Home Assistant pour suivre la **Ligue 1** et la **Ligue 2** en temps réel.
Données gratuites via ESPN, sans clé API.

[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/skyrotter/ligue_foot.svg)](https://github.com/skyrotter/ligue_foot/releases)

---

## 🚀 Installation

### Via HACS (recommandé)

1. **Ajoute le dépôt custom dans HACS** :
2.    - Va dans Home Assistant : **Paramètres → Appareils & Services → HACS**
      -    - Clique sur les 3 points (⋮) en haut à droite → **Dépôts custom**
           -    - Ajoute cette URL : `https://github.com/skyrotter/ligue_foot`
                -    - Sélectionne la catégorie : **Intégration**
                 
                     - 2. **Installe l'intégration** :
                       3.    - Cherche "Ligue Foot" dans HACS
                             -    - Clique sur "Ligue Foot"
                                  -    - Clique sur le bouton **Installer**
                                       -    - **Redémarre Home Assistant**
                                        
                                            - ### Configuration
                                        
                                            - Après installation :
                                        
                                            - 1. Va dans **Paramètres → Appareils & Services → Ajouter une intégration → Ligue Foot**
                                              2. 2. Choisis la ligue (Ligue 1 ou Ligue 2)
                                                 3. 3. Choisis ton équipe favorite
                                                    4. 4. Répète depuis l'étape 1 pour ajouter d'autres équipes
                                                      
                                                       5. ---
                                                      
                                                       6. ## 📦 Ce que tu obtiens par équipe
                                                      
                                                       7. ### Capteurs
                                                       8. | Entité | Description |
                                                       9. |---|---|
                                                       10. | `sensor.xxx_prochain_match` | Date + détails du prochain match |
                                                       11. | `sensor.xxx_classement` | Position dans le classement + tableau complet |
                                                       12. | `sensor.xxx_forme` | 5 derniers résultats (W/D/L) |
                                                       13. | `sensor.xxx_sync` | État de synchronisation ESPN |
                                                      
                                                       14. ### Capteurs binaires
                                                       15. | Entité | Description |
                                                       16. |---|---|
                                                       17. | `binary_sensor.xxx_match_en_cours` | ON si un match est live |
                                                       18. | `binary_sensor.xxx_match_aujourd_hui` | ON si un match a lieu aujourd'hui |
                                                       19. | `binary_sensor.xxx_match_demain` | ON si un match a lieu demain |
                                                      
                                                       20. ### Calendrier
                                                       21. - `calendar.xxx_ligue_1` — Calendrier des matchs (intégrable dans le dashboard calendrier HA)
                                                          
                                                           - ---

                                                           ## 🔔 Notifications & automatisations

                                                           ### Blueprints inclus
                                                           - **Rappel avant match** — Notifie X minutes avant le coup d'envoi
                                                           - - **But !** — Notifie à chaque but, avec animation lumières (Hue, Ambilight…)
                                                            
                                                             - ### Événements HA disponibles
                                                             - ```yaml
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
                                                               - - **Ambilight** (Philips TV)
                                                                 - - Tout autre équipement Zigbee, Z-Wave, Wi-Fi
                                                                  
                                                                   - ---

                                                                   ## ⚙️ Options

                                                                   Après installation, configure dans **Paramètres → Appareils & Services → Ligue Foot → Configurer** :

                                                                   - Notifications : coup d'envoi, but, carton rouge, fin de match
                                                                   - - Service de notification (ex: `notify.mobile_app_mon_telephone`)
                                                                     - - Plage de silence (ex: 23:00–07:00)
                                                                      
                                                                       - ---

                                                                       ## 🛠️ Dépannage

                                                                       | Problème | Solution |
                                                                       |---|---|
                                                                       | `sensor.sync` = `rate_limited` | ESPN a temporairement limité les requêtes. Les données reprennent automatiquement. |
                                                                       | `sensor.sync` = `provider_unavailable` | ESPN est hors ligne. Vérifie ta connexion et attends. |
                                                                       | Calendrier vide | Redémarre HA (pas seulement recharger l'intégration) après une mise à jour. |

                                                                       ---

                                                                       ## 📝 Licence

                                                                       GPL-3.0 — [@skyrotter](https://github.com/skyrotter)
