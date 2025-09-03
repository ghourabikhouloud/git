import requests
import json
import time

AGENT_URL = "http://localhost:8006/v1/tasks/send"

def send_git_command(prompt: str):
    """
    Envoie une commande en langage naturel au Git Agent et affiche la réponse.
    """
    print(f"\n--- Envoi de la commande : '{prompt}' ---")
    
    payload = {
        "taskId": f"client-test-{int(time.time())}",
        "message": {
            "role": "user",
            "parts": [{"text": prompt}]
        }
    }
    
    try:
        response = requests.post(AGENT_URL, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()  # Lève une exception pour les codes d'erreur 4xx/5xx
        
        print("Réponse du serveur (200 OK):")
        # Affiche la réponse joliment formatée
        response_data = response.json()
        agent_message = response_data['task']['messages'][0]['parts'][0]['text']
        print(agent_message)
        
    except requests.exceptions.RequestException as e:
        print(f"Erreur de connexion à l'agent : {e}")
        if e.response:
            print(f"Détails de l'erreur : {e.response.text}")

if __name__ == "__main__":
    # Scénarios de test pour valider le Git Agent
    commands_to_test = [
        "Affiche le statut du projet",
        "Commit les changements avec le message 'Refactorisation du module de login'",
        "Push les commits sur la branche main de mon remote origin"
        # "Pull les derniers changements depuis la branche develop du remote upstream" # Exemple plus complexe
    ]
    
    for command in commands_to_test:
        send_git_command(command)
        time.sleep(1) # Petite pause entre les requêtes