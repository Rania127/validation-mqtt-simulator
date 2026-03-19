"""
Tests fonctionnels du simulateur MQTTSim
========================================
Projet de semestre — UE Réseaux de Télécommunications
Master Systèmes Télécom — USTHB

Référence : Standard MQTT 3.1.1
Outil     : pytest
"""

import time
import threading
import pytest
from mqtt_sim import BrokerSim, ClientSim


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def broker():
    """Démarre un broker propre avant chaque test, l'arrête après."""
    b = BrokerSim()
    b.start()
    yield b
    b.stop()


@pytest.fixture
def broker_with_clients(broker):
    """Broker + un publisher et un subscriber déjà connectés."""
    pub = ClientSim(broker, client_id="pub_fixture")
    sub = ClientSim(broker, client_id="sub_fixture")
    sub.connect()
    pub.connect()
    yield broker, pub, sub
    pub.disconnect()
    sub.disconnect()


# ---------------------------------------------------------------------------
# Module 1 — Connexion / déconnexion (TC-01 à TC-04)
# ---------------------------------------------------------------------------

class TestConnexion:

    def test_connexion_nominale(self, broker):
        """TC-01 : connexion avec ID unique → CONNACK code 0."""
        client = ClientSim(broker, client_id="client_unique")
        result = client.connect()
        assert result.return_code == 0, f"CONNACK attendu 0, reçu {result.return_code}"
        client.disconnect()

    def test_id_duplique_deconnecte_premier_client(self, broker):
        """TC-02 : deux clients avec le même ID → le premier est déconnecté."""
        client_a = ClientSim(broker, client_id="client_duplique")
        client_a.connect()

        client_b = ClientSim(broker, client_id="client_duplique")
        client_b.connect()

        assert not client_a.is_connected(), "Client A aurait dû être déconnecté"
        assert client_b.is_connected(), "Client B devrait être connecté"
        client_b.disconnect()

    def test_deconnexion_propre(self, broker):
        """TC-03 : DISCONNECT propre → session nettoyée (clean_session=True)."""
        client = ClientSim(broker, client_id="client_clean", clean_session=True)
        client.connect()
        client.disconnect()
        assert not client.is_connected()

    def test_deconnexion_brutale_detectee(self, broker):
        """TC-04 : fermeture socket sans DISCONNECT → broker détecte la perte."""
        client = ClientSim(broker, client_id="client_brutal")
        client.connect()
        client.force_close()  # ferme le socket sans envoyer DISCONNECT
        time.sleep(0.5)       # laisse le broker détecter
        assert broker.is_client_known("client_brutal") is False


# ---------------------------------------------------------------------------
# Module 2 — Publication QoS 0 (TC-06 à TC-09)
# ---------------------------------------------------------------------------

class TestQoS0:

    def test_publication_nominale_qos0(self, broker):
        """TC-06 : message QoS 0 publié → reçu exactement une fois."""
        sub = ClientSim(broker, client_id="sub_qos0")
        sub.connect()
        sub.subscribe("capteurs/temp", qos=0)

        pub = ClientSim(broker, client_id="pub_qos0")
        pub.connect()
        pub.publish("capteurs/temp", payload="23.5", qos=0)

        messages = sub.get_received(timeout=1.0)
        assert len(messages) == 1, f"Attendu 1 message, reçu {len(messages)}"
        assert messages[0].payload == "23.5"
        sub.disconnect()
        pub.disconnect()

    def test_publication_sans_subscriber(self, broker):
        """TC-07 : publication sur topic sans subscriber → aucune erreur."""
        pub = ClientSim(broker, client_id="pub_seul")
        pub.connect()
        # Ne doit pas lever d'exception
        pub.publish("topic/sans/subscriber", payload="data", qos=0)
        pub.disconnect()

    def test_payload_vide(self, broker):
        """TC-08 : payload vide autorisé par le standard MQTT 3.1.1."""
        sub = ClientSim(broker, client_id="sub_vide")
        sub.connect()
        sub.subscribe("test/vide", qos=0)

        pub = ClientSim(broker, client_id="pub_vide")
        pub.connect()
        pub.publish("test/vide", payload="", qos=0)

        messages = sub.get_received(timeout=1.0)
        assert len(messages) == 1
        assert messages[0].payload == ""
        sub.disconnect()
        pub.disconnect()

    def test_payload_long(self, broker):
        """TC-09 : payload de 10 000 caractères reçu intégralement."""
        long_payload = "A" * 10_000
        sub = ClientSim(broker, client_id="sub_long")
        sub.connect()
        sub.subscribe("test/long", qos=0)

        pub = ClientSim(broker, client_id="pub_long")
        pub.connect()
        pub.publish("test/long", payload=long_payload, qos=0)

        messages = sub.get_received(timeout=2.0)
        assert len(messages) == 1
        assert len(messages[0].payload) == 10_000
        sub.disconnect()
        pub.disconnect()


# ---------------------------------------------------------------------------
# Module 3 — QoS 1 (TC-10 à TC-13)
# ---------------------------------------------------------------------------

class TestQoS1:

    def test_qos1_nominal(self, broker):
        """TC-10 : QoS 1 nominal → un seul message reçu, PUBACK envoyé."""
        sub = ClientSim(broker, client_id="sub_q1_ok")
        sub.connect()
        sub.subscribe("capteurs/temp", qos=1)

        pub = ClientSim(broker, client_id="pub_q1_ok")
        pub.connect()
        pub.publish("capteurs/temp", payload="24.1", qos=1)

        messages = sub.get_received(timeout=2.0)
        assert len(messages) == 1, "Exactement un message attendu en QoS 1"
        assert messages[0].payload == "24.1"
        sub.disconnect()
        pub.disconnect()

    def test_qos1_retransmission_sans_ack(self, broker):
        """TC-11 : si le subscriber ne renvoie pas PUBACK, le broker retransmet."""
        sub = ClientSim(broker, client_id="sub_no_ack", drop_ack=True)
        sub.connect()
        sub.subscribe("capteurs/temp", qos=1)

        pub = ClientSim(broker, client_id="pub_retrans")
        pub.connect()
        pub.publish("capteurs/temp", payload="retrans", qos=1)

        # On attend la retransmission (timeout broker ~ 1-2 s)
        messages = sub.get_received(timeout=4.0)
        assert len(messages) >= 1, "Le broker aurait dû retransmettre"
        sub.disconnect()
        pub.disconnect()

    def test_qos1_livraison_apres_reconnexion(self, broker):
        """
        TC-12 : messages publiés pendant déconnexion livrés à la reconnexion.
        RÉSULTAT ATTENDU : PASS
        RÉSULTAT OBSERVÉ : FAIL → voir rapport/anomalies.md Bug #1
        """
        sub = ClientSim(broker, client_id="sub_persistent", clean_session=False)
        sub.connect()
        sub.subscribe("alertes", qos=1)
        sub.disconnect()  # déconnexion simulée

        pub = ClientSim(broker, client_id="pub_offline")
        pub.connect()
        pub.publish("alertes", payload="SURTENSION", qos=1)
        pub.disconnect()

        # Reconnexion — le broker doit livrer le message mis en file
        sub.reconnect()
        messages = sub.get_received(timeout=2.0)
        assert any(m.payload == "SURTENSION" for m in messages), \
            "Message perdu pendant la déconnexion (Bug #1 — voir anomalies.md)"
        sub.disconnect()

    def test_qos1_pas_livraison_clean_session(self, broker):
        """TC-13 : clean_session=True → messages perdus à la reconnexion (comportement normal)."""
        sub = ClientSim(broker, client_id="sub_clean", clean_session=True)
        sub.connect()
        sub.subscribe("alertes", qos=1)
        sub.disconnect()

        pub = ClientSim(broker, client_id="pub_clean")
        pub.connect()
        pub.publish("alertes", payload="MSG_PERDU", qos=1)
        pub.disconnect()

        sub.reconnect()
        messages = sub.get_received(timeout=1.5)
        assert len(messages) == 0, "Session clean : aucun message ne doit être livré"
        sub.disconnect()


# ---------------------------------------------------------------------------
# Module 4 — QoS 2 (TC-14, TC-15)
# ---------------------------------------------------------------------------

class TestQoS2:

    def test_qos2_livraison_exactement_une_fois(self, broker):
        """TC-14 : QoS 2 → handshake complet, un seul message reçu."""
        sub = ClientSim(broker, client_id="sub_q2")
        sub.connect()
        sub.subscribe("commandes", qos=2)

        pub = ClientSim(broker, client_id="pub_q2")
        pub.connect()
        pub.publish("commandes", payload="RESET", qos=2)

        messages = sub.get_received(timeout=3.0)
        assert len(messages) == 1, \
            f"QoS 2 doit livrer exactement une fois, reçu {len(messages)}"
        assert messages[0].payload == "RESET"
        sub.disconnect()
        pub.disconnect()


# ---------------------------------------------------------------------------
# Module 5 — Topics et wildcards (TC-16 à TC-20)
# ---------------------------------------------------------------------------

class TestTopics:

    def test_wildcard_plus_un_niveau(self, broker):
        """TC-16 : wildcard '+' correspond à exactement un niveau de topic."""
        sub = ClientSim(broker, client_id="sub_wildcard")
        sub.connect()
        sub.subscribe("capteurs/+/temp", qos=0)

        pub = ClientSim(broker, client_id="pub_wildcard")
        pub.connect()
        pub.publish("capteurs/A/temp", payload="21.0", qos=0)
        pub.publish("capteurs/B/temp", payload="22.5", qos=0)
        pub.publish("capteurs/A/hum",  payload="60",   qos=0)  # ne doit PAS correspondre

        messages = sub.get_received(timeout=1.5)
        payloads = [m.payload for m in messages]
        assert "21.0" in payloads
        assert "22.5" in payloads
        assert "60" not in payloads, "Le wildcard '+' ne doit pas correspondre à 'hum'"
        sub.disconnect()
        pub.disconnect()

    def test_wildcard_diese_fin_topic(self, broker):
        """TC-17 : wildcard '#' en fin de topic → correspond à tous les sous-niveaux."""
        sub = ClientSim(broker, client_id="sub_diese")
        sub.connect()
        sub.subscribe("capteurs/#", qos=0)

        pub = ClientSim(broker, client_id="pub_diese")
        pub.connect()
        pub.publish("capteurs/temp/zone1", payload="data1", qos=0)
        pub.publish("capteurs/hum",        payload="data2", qos=0)

        messages = sub.get_received(timeout=1.5)
        assert len(messages) == 2
        sub.disconnect()
        pub.disconnect()

    def test_wildcard_diese_milieu_topic_invalide(self, broker):
        """
        TC-18 : '#' en milieu de topic → doit lever une exception.
        RÉSULTAT ATTENDU : ValueError ou équivalent
        RÉSULTAT OBSERVÉ : FAIL — aucune exception (Bug #2 — voir anomalies.md)
        """
        client = ClientSim(broker, client_id="sub_invalide")
        client.connect()
        with pytest.raises((ValueError, Exception)):
            client.subscribe("capteurs/#/temp", qos=0)
        client.disconnect()

    def test_topic_vide_interdit(self, broker):
        """TC-20 : topic vide → exception levée."""
        pub = ClientSim(broker, client_id="pub_topic_vide")
        pub.connect()
        with pytest.raises((ValueError, Exception)):
            pub.publish("", payload="data", qos=0)
        pub.disconnect()


# ---------------------------------------------------------------------------
# Module 7 — Robustesse (TC-23, TC-24)
# ---------------------------------------------------------------------------

class TestRobustesse:

    def test_10_clients_simultanement(self, broker):
        """TC-23 : 10 clients publient en parallèle → aucun message perdu."""
        NB = 10
        sub = ClientSim(broker, client_id="sub_charge_10")
        sub.connect()
        sub.subscribe("charge/test", qos=1)

        def publier(i):
            pub = ClientSim(broker, client_id=f"pub_charge_{i}")
            pub.connect()
            pub.publish("charge/test", payload=f"msg_{i}", qos=1)
            pub.disconnect()

        threads = [threading.Thread(target=publier, args=(i,)) for i in range(NB)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        messages = sub.get_received(timeout=3.0)
        assert len(messages) == NB, \
            f"Attendu {NB} messages, reçu {len(messages)}"
        sub.disconnect()

    def test_100_clients_simultanement(self, broker):
        """
        TC-24 : 100 clients publient en parallèle → aucun message perdu (spec §6.2).
        RÉSULTAT ATTENDU : 100 messages reçus
        RÉSULTAT OBSERVÉ : FAIL — entre 91 et 97 messages reçus (non déterministe)
        Race condition — voir rapport/anomalies.md Bug #3
        """
        NB = 100
        sub = ClientSim(broker, client_id="sub_charge_100")
        sub.connect()
        sub.subscribe("charge/test100", qos=1)

        def publier(i):
            pub = ClientSim(broker, client_id=f"pub100_{i}")
            pub.connect()
            pub.publish("charge/test100", payload=f"msg_{i}", qos=1)
            pub.disconnect()

        threads = [threading.Thread(target=publier, args=(i,)) for i in range(NB)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        messages = sub.get_received(timeout=5.0)
        assert len(messages) == NB, \
            f"Attendu {NB} messages, reçu {len(messages)} (Bug #3 — race condition)"
        sub.disconnect()