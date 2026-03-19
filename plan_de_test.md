\# Plan de test — Simulateur MQTT



\*\*Projet :\*\* Validation de MQTTSim

\*\*UE :\*\* Réseaux de Télécommunications — Master Télécom USTHB

\*\*Référence :\*\* Standard MQTT 3.1.1

\*\*Nombre de cas :\*\* 26

\*\*Résultat global :\*\* 22 PASS / 3 FAIL / 1 ambiguïté de spec



\---



\## Légende



| Statut | Signification |

|---|---|

| ✅ PASS | Comportement conforme à la spec |

| ❌ FAIL | Comportement non conforme — anomalie documentée |

| ⚠️ AMBIG | Spécification ambiguë — clarification demandée |



\---



\## Module 1 — Connexion et déconnexion



| ID | Intitulé | Condition initiale | Action | Résultat attendu | Statut |

|---|---|---|---|---|---|

| TC-01 | Connexion nominale | Broker démarré | Client se connecte avec ID unique | Connexion acceptée, CONNACK reçu avec code 0 | ✅ PASS |

| TC-02 | Connexion avec ID déjà utilisé | Client A connecté avec ID "client\_01" | Client B se connecte avec le même ID | Client A déconnecté, Client B accepté | ✅ PASS |

| TC-03 | Déconnexion propre | Client connecté | Client envoie DISCONNECT | Connexion fermée proprement, session nettoyée si clean\_session=True | ✅ PASS |

| TC-04 | Déconnexion brutale | Client connecté | Fermeture socket sans DISCONNECT | Broker détecte la perte, publie le LWT si configuré | ✅ PASS |

| TC-05 | ID client vide | Broker démarré | Connexion avec client\_id="" | Connexion refusée (CONNACK code 2) ou ID auto-généré | ⚠️ AMBIG |



\---



\## Module 2 — Publication et réception (QoS 0)



| ID | Intitulé | Condition initiale | Action | Résultat attendu | Statut |

|---|---|---|---|---|---|

| TC-06 | Publication QoS 0 nominale | Subscriber actif sur "capteurs/temp" | Publisher envoie message QoS 0 | Message reçu une fois par le subscriber | ✅ PASS |

| TC-07 | QoS 0 sans subscriber | Aucun subscriber sur le topic | Publication QoS 0 | Message ignoré, aucune erreur levée | ✅ PASS |

| TC-08 | Payload vide | Subscriber actif | Publication avec payload="" | Message reçu, payload vide | ✅ PASS |

| TC-09 | Payload long (10 000 caractères) | Subscriber actif | Publication payload > 10k chars | Message reçu intégralement | ✅ PASS |



\---



\## Module 3 — Qualité de service QoS 1



| ID | Intitulé | Condition initiale | Action | Résultat attendu | Statut |

|---|---|---|---|---|---|

| TC-10 | QoS 1 nominal — ACK reçu | Subscriber actif | Publication QoS 1 | Message reçu, PUBACK envoyé, une seule livraison | ✅ PASS |

| TC-11 | QoS 1 — retransmission si pas d'ACK | Subscriber configuré drop\_ack=True | Publication QoS 1 | Broker retransmet après timeout | ✅ PASS |

| TC-12 | QoS 1 — livraison après reconnexion | Subscriber déconnecté (clean\_session=False) | Publication pendant déconnexion, puis reconnexion | Message livré à la reconnexion | ❌ FAIL → Bug #1 |

| TC-13 | QoS 1 — pas de livraison après reconnexion (clean\_session=True) | Subscriber déconnecté (clean\_session=True) | Publication pendant déconnexion, puis reconnexion | Message non livré (session nettoyée) | ✅ PASS |



\---



\## Module 4 — Qualité de service QoS 2



| ID | Intitulé | Condition initiale | Action | Résultat attendu | Statut |

|---|---|---|---|---|---|

| TC-14 | QoS 2 nominal — livraison exactement une fois | Subscriber actif | Publication QoS 2 | Handshake PUBREC/PUBREL/PUBCOMP complet, un seul message reçu | ✅ PASS |

| TC-15 | QoS 2 — interruption après PUBREC | Publication QoS 2 en cours | Déconnexion après PUBREC, avant PUBREL | À la reconnexion, handshake repris depuis PUBREL | ✅ PASS |



\---



\## Module 5 — Topics et wildcards



| ID | Intitulé | Condition initiale | Action | Résultat attendu | Statut |

|---|---|---|---|---|---|

| TC-16 | Wildcard "+" sur un niveau | Subscriber sur "capteurs/+/temp" | Publications sur "capteurs/A/temp" et "capteurs/B/temp" | Les deux messages reçus | ✅ PASS |

| TC-17 | Wildcard "#" en fin de topic | Subscriber sur "capteurs/#" | Publication sur "capteurs/temp/zone1" | Message reçu | ✅ PASS |

| TC-18 | Wildcard "#" en milieu de topic | Broker démarré | subscribe("capteurs/#/temp") | Exception levée (topic invalide selon MQTT 3.1.1 §4.7) | ❌ FAIL → Bug #2 |

| TC-19 | Topic avec espaces | Broker démarré | Publication sur "mon topic" | Exception levée (caractère interdit) | ✅ PASS |

| TC-20 | Topic vide | Broker démarré | Publication sur "" | Exception levée | ✅ PASS |



\---



\## Module 6 — Sessions persistantes et reconnexion



| ID | Intitulé | Condition initiale | Action | Résultat attendu | Statut |

|---|---|---|---|---|---|

| TC-21 | Souscription persistante | Client connecté avec clean\_session=False | Déconnexion puis reconnexion sans re-souscrire | Souscriptions précédentes conservées | ✅ PASS |

| TC-22 | Souscription non persistante | Client connecté avec clean\_session=True | Déconnexion puis reconnexion | Souscriptions perdues, doit re-souscrire | ✅ PASS |



\---



\## Module 7 — Robustesse et charge



| ID | Intitulé | Condition initiale | Action | Résultat attendu | Statut |

|---|---|---|---|---|---|

| TC-23 | 10 clients simultanés | Broker démarré | 10 clients publient en parallèle | Aucun message perdu | ✅ PASS |

| TC-24 | 100 clients simultanés | Broker démarré | 100 clients publient en parallèle | Aucun message perdu (spec §6.2) | ❌ FAIL → Bug #3 |

| TC-25 | 1 000 messages en séquence | 1 client connecté | Publication de 1 000 messages QoS 1 | Tous reçus, dans l'ordre | ✅ PASS |

| TC-26 | Stabilité sur 5 minutes | Broker + 5 clients actifs | Fonctionnement continu sans action | Aucun crash, aucune fuite mémoire observable | ✅ PASS |



\---



\## Synthèse



| Module | Total | PASS | FAIL |

|---|---|---|---|

| Connexion / déconnexion | 5 | 4 | 0 (1 ambiguïté) |

| Publication QoS 0 | 4 | 4 | 0 |

| QoS 1 | 4 | 3 | 1 |

| QoS 2 | 2 | 2 | 0 |

| Topics / wildcards | 5 | 4 | 1 |

| Sessions | 2 | 2 | 0 |

| Robustesse | 4 | 3 | 1 |

| \*\*Total\*\* | \*\*26\*\* | \*\*22\*\* | \*\*3\*\* |



