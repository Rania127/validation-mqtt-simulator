# Rapport d'anomalies — Simulateur MQTTSim

**Projet :** Validation de MQTTSim — UE Réseaux de Télécommunications  
**Master Systèmes Télécom — USTHB**  
**Anomalies identifiées :** 3 (2 majeures, 1 mineure)  
**Anomalies résolues :** 0 — remises à l'équipe de développement

---

## Synthèse

| ID | Titre | Sévérité | Cas de test | Statut |
|---|---|---|---|---|
| Bug 1 | Messages QoS 1 perdus après reconnexion | Majeure | TC-12 | Ouvert |
| Bug 2 | Topic invalide accepté sans erreur | Mineure | TC-18 | Ouvert |
| Bug 3 | Perte de messages sous charge (100 clients) | Majeure | TC-24 | Ouvert |

---

## Bug 1 — Messages QoS 1 perdus après reconnexion

**Sévérité :** Majeure  
**Cas de test :** TC-12  
**Date de découverte :** Semaine 4

### Spécification violée

Section 4.1 — *"Lorsqu'un client se reconnecte avec clean_session=False, le broker doit lui livrer tous les messages QoS 1 publiés pendant sa déconnexion sur les topics auxquels il était souscrit."*

### Étapes de reproduction

1. Créer un subscriber avec `clean_session=False` et `client_id="sub_persistent"`
2. Connecter le subscriber et le souscrire au topic `alertes` en QoS 1
3. Déconnecter le subscriber
4. Publier un message QoS 1 sur `alertes` avec payload `SURTENSION`
5. Reconnecter le subscriber
6. Appeler `get_received(timeout=2.0)`

### Résultat observé

La liste retournée est vide. Le message SURTENSION n'est pas livré.

### Résultat attendu

Le message SURTENSION doit être présent dans la liste des messages reçus après la reconnexion.

### Analyse

Le paramètre `clean_session` est bien transmis lors de la connexion. Cependant, la file d'attente des messages en attente est vidée à la déconnexion quel que soit le flag. La cause probable est que la méthode `_clear_session()` est appelée inconditionnellement à chaque déconnexion.

### Suggestion de correction

Conditionner le nettoyage de session au flag `clean_session` :

```python
def on_client_disconnect(self, client_id):
    session = self.sessions[client_id]
    if session.clean_session:
        self._clear_session(client_id)
    else:
        self._preserve_pending(client_id)
```

### Impact

Dans un contexte industriel réel, ce bug entraîne la perte silencieuse d'alarmes critiques envoyées pendant une interruption réseau.

---

## Bug 2 — Topic invalide accepté sans erreur

**Sévérité :** Mineure  
**Cas de test :** TC-18  
**Date de découverte :** Semaine 3

### Spécification violée

Standard MQTT 3.1.1, section 4.7 — *"Le caractère '#' n'est valide dans un filtre de topic que s'il est le dernier caractère du filtre, précédé d'un séparateur '/'."*

### Étapes de reproduction

1. Connecter un client au broker
2. Appeler `client.subscribe("capteurs/#/temp", qos=0)`
3. Observer le comportement

### Résultat observé

La souscription est acceptée sans exception. Le comportement lors de la réception est ensuite imprévisible.

### Résultat attendu

Une exception doit être levée avec un message indiquant que le topic est invalide.

### Analyse

Absence de validation du format du filtre de topic avant souscription. La fonction `subscribe()` ne vérifie pas la position du caractère `#`.

### Suggestion de correction

Ajouter une validation avant d'enregistrer le filtre :

```python
def _validate_topic_filter(self, topic: str):
    parts = topic.split('/')
    for i, part in enumerate(parts):
        if '#' in part and (i != len(parts) - 1 or part != '#'):
            raise ValueError(f"Topic invalide : '{topic}'")
```

---

## Bug 3 — Perte de messages sous forte charge

**Sévérité :** Majeure  
**Cas de test :** TC-24  
**Date de découverte :** Semaine 4

### Spécification violée

Section 6.2 — *"Le simulateur doit supporter jusqu'à 100 clients simultanés en publication sans perte de message."*

### Étapes de reproduction

1. Connecter un subscriber au topic `charge/test100` en QoS 1
2. Lancer 100 threads Python, chacun créant un ClientSim, publiant un message QoS 1, puis se déconnectant
3. Attendre la fin des 100 threads
4. Compter les messages reçus par le subscriber

### Résultat observé

Le nombre de messages reçus varie entre 91 et 97 selon les exécutions. Le résultat n'est jamais identique d'un run à l'autre.

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

### Résultat attendu

100 messages reçus à chaque exécution, sans variabilité.

### Analyse

Le caractère non déterministe de la perte est le signe caractéristique d'une race condition. La file d'attente des messages entrants du broker est probablement partagée entre les threads sans mécanisme de synchronisation.

### Suggestion de correction

Remplacer la structure de données de la file par une `queue.Queue` Python, qui est thread-safe par conception :

```python
import queue

class BrokerSim:
    def __init__(self):
        self._incoming = queue.Queue()
```

### Impact

En conditions industrielles, ce bug provoquerait des pertes de données lors des pics de charge, précisément dans les situations les plus critiques.

---

*Rapport rédigé par l'équipe de validation — Master Télécom USTHB*