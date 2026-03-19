\\# Validation d'un simulateur de protocole MQTT







Projet de semestre — UE Réseaux de Télécommunications  



Master Systèmes Télécom — USTHB  



Durée : 6 semaines | Équipe : 2 personnes







\\---







\\## Contexte







Dans le cadre de l'UE Réseaux de Télécommunications, nous avons joué le rôle d'une équipe QA externe chargée de valider un simulateur Python de protocole MQTT (Message Queuing Telemetry Transport).







Le logiciel testé — `MQTTSim` — simule un broker MQTT et plusieurs clients capteurs. Il implémente les niveaux de qualité de service QoS 0, 1 et 2 définis dans le standard \\\*\\\*MQTT 3.1.1\\\*\\\*, ainsi que la gestion des sessions persistantes et des reconnexions.







MQTT est un protocole de messagerie léger très utilisé dans l'IoT industriel : capteurs connectés, bornes de recharge, automates, équipements de supervision énergétique.







\\---







\\## Objectifs







\\- Analyser les spécifications du simulateur et le standard MQTT 3.1.1



\\- Rédiger un plan de test couvrant les comportements nominaux et les cas limites



\\- Automatiser les vérifications avec `pytest`



\\- Identifier, documenter et analyser les anomalies détectées







\\---







\\## Résultats







| Indicateur | Valeur |



|---|---|



| Cas de test rédigés | 26 |



| Cas PASS | 22 |



| Cas FAIL | 3 |



| Anomalies documentées | 3 (dont 2 majeures) |



| Ambiguïtés de spec identifiées | 1 |







\\---







\\## Structure du dépôt







```



validation-mqtt-simulator/



├── README.md                  ← ce fichier



├── plan\\\_de\\\_test.md            ← les 26 cas de test détaillés



├── test\\\_mqtt\\\_sim.py           ← tests automatisés avec pytest



└── rapport/



\&#x20;   └── anomalies.md           ← fiches détaillées des 3 anomalies



```







\\---







\\## Technologies utilisées







\\- \\\*\\\*Python 3.11\\\*\\\*



\\- \\\*\\\*pytest\\\*\\\* — framework de tests automatisés



\\- \\\*\\\*Standard MQTT 3.1.1\\\*\\\* — référence de conformité



\\- \\\*\\\*Git / GitHub\\\*\\\* — versionnement







\\---







\\## Compétences mises en œuvre







\\- Lecture et analyse d'une spécification technique



\\- Rédaction d'un plan de test (cas nominaux, limites, erreurs)



\\- Automatisation de tests fonctionnels avec pytest



\\- Analyse et documentation d'anomalies (reproduction, cause, suggestion)



\\- Identification d'ambiguïtés dans une spec







\\---







\\\*Projet réalisé dans le cadre du Master Systèmes Télécom — USTHB\\\*





