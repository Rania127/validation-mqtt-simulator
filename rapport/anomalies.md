\\# Rapport d'anomalies — Simulateur MQTTSim







\\\*\\\*Projet :\\\*\\\* Validation de MQTTSim — UE Réseaux de Télécommunications  



\\\*\\\*Master Systèmes Télécom — USTHB\\\*\\\*  



\\\*\\\*Anomalies identifiées :\\\*\\\* 3 (2 majeures, 1 mineure)  



\\\*\\\*Anomalies résolues :\\\*\\\* 0 (remises à l'équipe de développement)







\\---







\\## Synthèse







| ID | Titre | Sévérité | Cas de test | Statut |



|---|---|---|---|---|



| Bug #1 | Messages QoS 1 perdus après reconnexion | Majeure | TC-12 | Ouvert |



| Bug #2 | Topic invalide accepté sans erreur | Mineure | TC-18 | Ouvert |



| Bug #3 | Perte de messages sous charge (100 clients) | Majeure | TC-24 | Ouvert |







\\---







\\## Bug #1 — Messages QoS 1 perdus après reconnexion







\\\*\\\*Sévérité :\\\*\\\* Majeure  



\\\*\\\*Cas de test :\\\*\\\* TC-12  



\\\*\\\*Date de découverte :\\\*\\\* Semaine 4







\\### Spécification violée







> §4.1 — \\\*"Lorsqu'un client se reconnecte avec `clean\\\_session=False`, le broker doit lui livrer tous les messages QoS 1 publiés pendant sa déconnexion sur les topics auxquels il était souscrit."\\\*







\\### Étapes de reproduction







1\\. Créer un subscriber avec `clean\\\_session=False` et `client\\\_id="sub\\\_persistent"`



2\\. Connecter le subscriber et le souscrire au topic `"alertes"` en QoS 1



3\\. Déconnecter le subscriber (`sub.disconnect()`)



4\\. Publier un message QoS 1 sur `"alertes"` avec payload `"SURTENSION"`



5\\. Reconnecter le subscriber (`sub.reconnect()`)



6\\. Appeler `sub.get\\\_received(timeout=2.0)`







\\### Résultat observé







La liste retournée est \\\*\\\*vide\\\*\\\*. Le message `"SURTENSION"` n'est pas livré.







\\### Résultat attendu







Le message `"SURTENSION"` doit être présent dans la liste des messages reçus après la reconnexion.







\\### Analyse







Le paramètre `clean\\\_session` est bien transmis lors de la connexion (vérifié dans les logs du broker). Cependant, la file d'attente des messages en attente semble être \\\*\\\*vidée à la déconnexion\\\*\\\* quel que soit le flag `clean\\\_session`.







La cause probable est que la logique de nettoyage de session (`\\\_clear\\\_session()`) est appelée inconditionnellement à la déconnexion, sans vérifier si `clean\\\_session=True` ou `False`.







\\### Suggestion de correction







Dans la méthode de gestion de déconnexion du broker, conditionner le nettoyage de la file :







```python



def on\\\_client\\\_disconnect(self, client\\\_id):



\&#x20;   session = self.sessions\\\[client\\\_id]



\&#x20;   if session.clean\\\_session:



\&#x20;       self.\\\_clear\\\_session(client\\\_id)   # nettoyage complet



\&#x20;   else:



\&#x20;       self.\\\_preserve\\\_pending(client\\\_id) # conserver les messages QoS 1 en attente



```







\\### Impact







Dans un contexte industriel réel (capteurs IoT, équipements de supervision), ce bug entraîne la \\\*\\\*perte silencieuse d'alarmes critiques\\\*\\\* envoyées pendant une interruption réseau. Un équipement ne recevrait pas les commandes ou alertes émises pendant son absence.







\\---







\\## Bug #2 — Topic invalide accepté sans erreur







\\\*\\\*Sévérité :\\\*\\\* Mineure  



\\\*\\\*Cas de test :\\\*\\\* TC-18  



\\\*\\\*Date de découverte :\\\*\\\* Semaine 3







\\### Spécification violée







> Standard MQTT 3.1.1, §4.7 — \\\*"Le caractère '#' n'est valide dans un filtre de topic que s'il est le dernier caractère du filtre et qu'il est précédé d'un séparateur '/' ou qu'il constitue l'intégralité du filtre."\\\*







\\### Étapes de reproduction







1\\. Connecter un client au broker



2\\. Appeler `client.subscribe("capteurs/#/temp", qos=0)`



3\\. Observer le comportement







\\### Résultat observé







La souscription est \\\*\\\*acceptée sans exception\\\*\\\*. Le comportement lors de la réception de messages sur ce topic est ensuite imprévisible (tantôt aucun message, tantôt tous les messages).







\\### Résultat attendu







Une exception (`ValueError` ou `MQTTError`) doit être levée avec un message explicite indiquant que le topic est invalide.







\\### Analyse







Absence de validation du format du filtre de topic avant souscription. La fonction `subscribe()` ne vérifie pas la position du caractère `#` dans la chaîne.







\\### Suggestion de correction







Ajouter une validation du filtre avant de l'enregistrer :







```python



def \\\_validate\\\_topic\\\_filter(self, topic: str):



\&#x20;   if '#' in topic:



\&#x20;       parts = topic.split('/')



\&#x20;       for i, part in enumerate(parts):



\&#x20;           if '#' in part and (i != len(parts) - 1 or part != '#'):



\&#x20;               raise ValueError(f"Topic invalide : '#' doit être le dernier niveau seul. Reçu : '{topic}'")



```







\\---







\\## Bug #3 — Perte de messages sous forte charge







\\\*\\\*Sévérité :\\\*\\\* Majeure  



\\\*\\\*Cas de test :\\\*\\\* TC-24  



\\\*\\\*Date de découverte :\\\*\\\* Semaine 4







\\### Spécification violée







> §6.2 — \\\*"Le simulateur doit supporter jusqu'à 100 clients simultanés en publication sans perte de message."\\\*







\\### Étapes de reproduction







1\\. Connecter un subscriber au topic `"charge/test100"` en QoS 1



2\\. Lancer 100 threads Python, chacun créant un `ClientSim`, se connectant, publiant un message QoS 1 unique, puis se déconnectant



3\\. Attendre la fin des 100 threads



4\\. Compter les messages reçus par le subscriber







\\### Résultat observé







Le nombre de messages reçus varie entre \\\*\\\*91 et 97\\\*\\\* selon les exécutions. Le test n'est jamais reproductible à l'identique — le nombre exact de messages perdus change à chaque run.







Résultats sur 10 exécutions successives :







| Run | Messages reçus | Messages perdus |



|---|---|---|



| 1 | 96 | 4 |



| 2 | 94 | 6 |



| 3 | 97 | 3 |



| 4 | 93 | 7 |



| 5 | 96 | 4 |



| 6 | 91 | 9 |



| 7 | 95 | 5 |



| 8 | 97 | 3 |



| 9 | 94 | 6 |



| 10 | 92 | 8 |







\\### Résultat attendu







100 messages reçus à chaque exécution, sans variabilité.







\\### Analyse







Le caractère \\\*\\\*non déterministe\\\*\\\* de la perte est le signe caractéristique d'une \\\*\\\*race condition\\\*\\\* (condition de course). La file d'attente des messages entrants du broker est probablement partagée entre les threads de connexion sans mécanisme de synchronisation (verrou, mutex, queue thread-safe).







Plusieurs threads accèdent et modifient la file simultanément, provoquant des écrasements silencieux.







\\### Suggestion de correction







Remplacer la structure de données de la file par une `queue.Queue` de Python (thread-safe par conception) :







```python



import queue







class BrokerSim:



\&#x20;   def \\\_\\\_init\\\_\\\_(self):



\&#x20;       self.\\\_incoming = queue.Queue()  # thread-safe, remplace la liste simple



```







\\### Impact







En conditions industrielles, ce bug provoquerait des pertes de données de mesure ou de commandes lors des pics de charge — précisément dans les situations les plus critiques (événement, alarme, mise à jour groupée).







\\---







\\\*Rapport rédigé par l'équipe de validation — Master Télécom USTHB\\\*





