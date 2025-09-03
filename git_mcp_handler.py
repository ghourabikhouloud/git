# import subprocess
# import json
# import os

# class GitMCPHandler:
#     """
#     Gère la communication avec le github-mcp-server s'exécutant dans un conteneur Docker via stdio.
#     Cette classe est responsable du cycle de vie du processus Docker.
#     """
#     def __init__(self, github_pat: str):
#         """
#         Initialise le handler avec un Token d'Accès Personnel GitHub.
        
#         Args:
#             github_pat: Le token nécessaire pour que le MCP server s'authentifie auprès de l'API GitHub.
#         """
#         if not github_pat:
#             raise ValueError("Un Token d'Accès Personnel GitHub (PAT) est requis.")
#         self.github_pat = github_pat
#         self.process = None
#         self.request_id = 0
        
#     def start_server(self):
#         """
#         Démarre le conteneur Docker 'ghcr.io/github/github-mcp-server' en tant que sous-processus.
#         Le mode 'Dynamic Tool Discovery' est activé pour une flexibilité maximale.
#         """
#         command = [
#             "docker", "run", "-i", "--rm",
#             "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={self.github_pat}",
#             # Active la découverte dynamique d'outils, ce qui est la meilleure pratique
#             "-e", "GITHUB_DYNAMIC_TOOLSETS=1", 
#             "ghcr.io/github/github-mcp-server"
#         ]
        
#         print("[GitMCPHandler] Démarrage du conteneur Docker en mode DYNAMIC...")
#         try:
#             self.process = subprocess.Popen(
#                 command,
#                 stdin=subprocess.PIPE,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE,
#                 text=True,
#                 bufsize=1,
#                 encoding='utf-8'
#             )
#             print("[GitMCPHandler] Conteneur Docker démarré avec succès.")
#         except FileNotFoundError:
#             print("\nERREUR: La commande 'docker' n'a pas été trouvée. Docker Desktop est-il installé et en cours d'exécution ?")
#             raise
#         except Exception as e:
#             print(f"\nERREUR: Échec du démarrage du conteneur Docker : {e}")
#             raise




import subprocess
import json
import os
import time

class GitMCPHandler:
    """
    Gère la communication avec le github-mcp-server s'exécutant dans un conteneur Docker via stdio.
    Cette classe est responsable du cycle de vie du processus Docker.
    """
    def __init__(self, github_pat: str):
        """
        Initialise le handler avec un Token d'Accès Personnel GitHub.
        
        Args:
            github_pat: Le token nécessaire pour que le MCP server s'authentifie auprès de l'API GitHub.
        """
        if not github_pat:
            raise ValueError("Un Token d'Accès Personnel GitHub (PAT) est requis.")
        self.github_pat = github_pat
        self.process = None  # Le processus Popen pour le conteneur Docker
        self.request_id = 0  # Compteur pour les ID des requêtes JSON-RPC
        
    def start_server(self):
        """
        Démarre le conteneur Docker 'ghcr.io/github/github-mcp-server' en tant que sous-processus.
        Le mode 'Dynamic Tool Discovery' est activé pour une flexibilité maximale.
        """
        command = [
            "docker", "run", "-i", "--rm", # '-i' pour stdin interactif, '--rm' pour supprimer le conteneur à l'arrêt
            "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={self.github_pat}",
            "-e", "GITHUB_DYNAMIC_TOOLSETS=1", 
            "ghcr.io/github/github-mcp-server"
        ]
        
        print("[GitMCPHandler] Démarrage du conteneur Docker en mode DYNAMIC...")
        try:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, # Capture stderr pour le débogage
                text=True, # Pour que stdin/stdout/stderr soient des objets texte
                bufsize=1, # Line-buffered for stdout (important for readline)
                encoding='utf-8'
            )
            print("[GitMCPHandler] Conteneur Docker démarré avec succès.")

            # Attendre que le serveur MCP soit prêt. Lire stderr peut donner des indices.
            startup_timeout = 60 # secondes
            start_time = time.time()
            server_ready = False
            print("[GitMCPHandler] Attente de la sortie de démarrage du serveur MCP (max 60s)...")
            while time.time() - start_time < startup_timeout:
                line = self.process.stderr.readline() # Lire la sortie d'erreur du MCP
                if "GitHub MCP Server running on stdio" in line: # MODIFICATION ICI : Détection spécifique
                    print(f"[GitMCPHandler] MCP Server output (stderr): {line.strip()}")
                    server_ready = True
                    break
                elif line:
                    print(f"[GitMCPHandler] MCP Server output (stderr): {line.strip()}") # Afficher les logs de démarrage
                if self.process.poll() is not None: # Si le processus s'est terminé prématurément
                    stderr_output = self.process.stderr.read()
                    raise RuntimeError(f"Le conteneur Docker MCP s'est terminé prématurément. Code de sortie: {self.process.returncode}\nStderr:\n{stderr_output}")
                time.sleep(0.05) # Attendre un peu avant de relire (plus rapide que 0.5)

            if not server_ready:
                raise RuntimeError(f"Le serveur MCP n'a pas indiqué être prêt après {startup_timeout} secondes.")
            
            print("[GitMCPHandler] Serveur MCP semble prêt. Tentative d'envoi d'une requête initiale pour confirmer et maintenir le serveur actif...")
            # Envoyer une requête initiale (par exemple, tools/list) pour maintenir le serveur MCP actif
            # et vérifier la communication JSON-RPC.
            try:
                self.send_request(method="tools/list", params={}, timeout=10) # Timeout court pour cette requête de démarrage
                print("[GitMCPHandler] Requête initiale 'tools/list' envoyée avec succès. Le serveur MCP est opérationnel.")
            except Exception as e:
                # Si le serveur répond avec une erreur à tools/list, il est peut-être mal configuré,
                # mais au moins il n'a pas planté directement.
                # Nous élevons l'erreur car cela indique un problème fondamental.
                raise RuntimeError(f"Le serveur MCP a démarré mais n'a pas répondu correctement à la requête initiale 'tools/list': {e}")


        except FileNotFoundError:
            print("\nERREUR: La commande 'docker' n'a pas été trouvée. Docker Desktop est-il installé et en cours d'exécution ?")
            raise
        except Exception as e:
            print(f"\nERREUR: Échec du démarrage du conteneur Docker : {e}")
            raise

    def stop_server(self):
        """Arrête le processus Docker MCP."""
        if self.process and self.process.poll() is None: # Vérifier si le processus est toujours en cours d'exécution
            print("[GitMCPHandler] Arrêt du conteneur Docker...")
            try:
                self.process.stdin.close() # Fermer stdin pour signaler la fin au serveur MCP
                self.process.terminate() # Envoie SIGTERM
                self.process.wait(timeout=10) # Attendre la fin du processus avec un timeout
                print("[GitMCPHandler] Conteneur Docker arrêté.")
            except subprocess.TimeoutExpired:
                print("[GitMCPHandler] Timeout expiré lors de l'arrêt, tuer le processus...")
                self.process.kill() # Envoie SIGKILL si terminate ne fonctionne pas
                self.process.wait()
            except Exception as e:
                print(f"ERREUR lors de l'arrêt du conteneur Docker : {e}")
            finally:
                self.process = None
        elif self.process:
            print("[GitMCPHandler] Le conteneur Docker était déjà arrêté.")
            self.process = None


    def send_request(self, method: str, params: dict, timeout: int = 30):
        """
        Envoie une requête JSON-RPC au serveur MCP via stdin et lit la réponse via stdout.
        
        Args:
            method: La méthode JSON-RPC à appeler (ex: "tools/list", "Repositories.create_or_update_file").
            params: Les paramètres de la méthode sous forme de dictionnaire.
            timeout: Le délai en secondes pour attendre une réponse.

        Returns:
            Le résultat de la requête JSON-RPC.
        
        Raises:
            RuntimeError: Si la communication échoue, si le processus n'est pas démarré,
                          ou si le serveur MCP renvoie une erreur.
        """
        if not self.process or self.process.poll() is not None:
            raise RuntimeError("Le processus du serveur MCP n'est pas en cours d'exécution ou s'est arrêté.")

        self.request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id
        }
        
        json_payload = json.dumps(payload) + "\n"
        
        print(f"[GitMCPHandler] Envoi de requête JSON-RPC via stdin pour la méthode {method} (ID: {self.request_id})")
        # print(f"[GitMCPHandler] Payload: {json_payload.strip()}") # Décommenter pour voir le payload envoyé

        try:
            self.process.stdin.write(json_payload)
            self.process.stdin.flush() # Assure que la donnée est envoyée au sous-processus

            start_time = time.time()
            response_line = ""
            while time.time() - start_time < timeout:
                # Vérifier si stdout est lisible avant de tenter de lire
                # Note: `readable()` n'est pas toujours fiable pour les pipes Popen sur toutes les plateformes/versions Python
                # On se repose principalement sur readline() qui bloquera ou retournera une chaîne vide
                # si rien n'est disponible pendant un court laps de temps.
                line = self.process.stdout.readline()
                if line:
                    response_line = line
                    break
                
                if self.process.poll() is not None:
                    stderr_output = self.process.stderr.read()
                    raise RuntimeError(f"Le serveur MCP s'est terminé pendant l'attente d'une réponse. Code de sortie: {self.process.returncode}\nStderr:\n{stderr_output}")
                
                time.sleep(0.05) # Petite pause pour ne pas surcharger le CPU
            
            if not response_line:
                raise RuntimeError(f"Le serveur MCP n'a pas répondu dans le délai imparti ({timeout}s) pour la requête {method}.")

            response_data = json.loads(response_line)
            
            if "error" in response_data:
                error_message = response_data["error"].get("message", "Erreur inconnue du serveur MCP")
                error_code = response_data["error"].get("code", -1)
                raise RuntimeError(f"Erreur du serveur MCP [{error_code}] pour la méthode {method}: {error_message}")
            
            if response_data.get("id") != self.request_id:
                print(f"[GitMCPHandler] Avertissement: ID de réponse ({response_data.get('id')}) ne correspond pas à l'ID de requête ({self.request_id}) pour la méthode {method}.")

            return response_data.get("result", {})

        except json.JSONDecodeError as e:
            print(f"[GitMCPHandler] Erreur de décodage JSON de la réponse du MCP pour la méthode {method}: {e}. Réponse brute: {response_line}")
            raise RuntimeError(f"Réponse JSON invalide du serveur MCP pour la méthode {method}: {e}") from e
        except Exception as e:
            print(f"Erreur de communication avec le serveur MCP pour la méthode {method}: {e}")
            if self.process.poll() is not None:
                stderr_output = self.process.stderr.read()
                print(f"[GitMCPHandler] Erreur Standard du MCP (stderr) lors de la requête:\n{stderr_output}")
            raise RuntimeError(f"Échec de la communication avec le serveur MCP pour la méthode {method}.") from e
# ----------
# import subprocess
# import time
# import os
# import requests

# class GitMCPHandler:
#     def __init__(self, github_pat):
#         self.github_pat = github_pat
#         self.container_id = None
#         self.mcp_server_url = None
#         self.host_port = 8085
#         self.container_port = 8084

#     def start_server(self):
#         docker_executable_path = "C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker.exe"

#         command = [
#             docker_executable_path, "run", "-d",
#             "-p", f"{self.host_port}:{self.container_port}",
#             "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={self.github_pat}",
#             "-e", "GITHUB_DYNAMIC_TOOLSETS=1",
#             "ghcr.io/github/github-mcp-server"
#         ]

#         print("[GitMCPHandler] Démarrage du conteneur Docker en mode DYNAMIC...")
#         try:
#             print(f"[GitMCPHandler] PATH dans le processus Python: {os.environ.get('PATH')}")
#             print(f"[GitMCPHandler] Exécution de la commande: {' '.join(command)}")

#             result = subprocess.run(
#                 command,
#                 capture_output=True,
#                 text=True,
#                 check=True,
#                 env=os.environ.copy() # <-- AJOUTER CETTE LIGNE
#             )
#             self.container_id = result.stdout.strip()
#             self.mcp_server_url = f"http://127.0.0.1:{self.host_port}"
#             print(f"[GitMCPHandler] Conteneur Docker démarré avec succès. ID: {self.container_id}")
#             print(f"[GitMCPHandler] Serveur MCP accessible à l'adresse : {self.mcp_server_url}")

#             max_retries = 30
#             retry_delay = 1

#             print("[GitMCPHandler] Attente de la disponibilité du serveur MCP...")
#             for i in range(max_retries):
#                 try:
#                     test_response = requests.post(
#                         f"{self.mcp_server_url}/",
#                         json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
#                         timeout=5
#                     )
#                     test_response.raise_for_status()

#                     print(f"[GitMCPHandler] Serveur MCP disponible après {i+1} tentatives.")
#                     return
#                 except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
#                     print(f"[GitMCPHandler] Tentative {i+1}/{max_retries}: Connexion au serveur MCP échouée ({e}). Nouvelle tentative dans {retry_delay}s...")
#                     time.sleep(retry_delay)
#                 except requests.exceptions.RequestException as e:
#                     print(f"[GitMCPHandler] Tentative {i+1}/{max_retries}: Serveur MCP a répondu avec une erreur HTTP: {e}. Nouvelle tentative dans {retry_delay}s...")
#                     time.sleep(retry_delay)
#                 except Exception as e:
#                     print(f"[GitMCPHandler] Tentative {i+1}/{max_retries}: Erreur inattendue lors de la connexion au MCP: {e}. Nouvelle tentative dans {retry_delay}s...")
#                     time.sleep(retry_delay)

#             raise RuntimeError(f"Le serveur MCP n'a pas démarré ou n'est pas devenu disponible après {max_retries} tentatives.")

#         except subprocess.CalledProcessError as e:
#             print(f"\nERREUR: Échec de l'exécution de la commande Docker. Code de sortie : {e.returncode}")
#             print(f"Stdout: {e.stdout}")
#             print(f"Stderr: {e.stderr}")
#             raise
#         except FileNotFoundError:
#             print("\nERREUR: La commande 'docker' n'a pas été trouvée. Docker Desktop est-il installé et en cours d'exécution ?")
#             raise
#         except Exception as e:
#             print(f"\nERREUR: Échec du démarrage du conteneur Docker : {e}")
#             raise

#     def stop_server(self):
#         if hasattr(self, 'container_id') and self.container_id:
#             print(f"[GitMCPHandler] Arrêt du conteneur Docker (ID: {self.container_id})...")
#             try:
#                 subprocess.run(["docker", "stop", self.container_id], check=True)
#                 print("[GitMCPHandler] Conteneur Docker arrêté.")
#             except subprocess.CalledProcessError as e:
#                 print(f"ERREUR lors de l'arrêt du conteneur Docker : {e}")
#             finally:
#                 self.container_id = None
#                 self.mcp_server_url = None

#     def send_request(self, method: str, params: dict):
#         if not self.mcp_server_url:
#             raise RuntimeError("Le processus du serveur n'est pas en cours d'exécution ou l'URL n'est pas définie.")

#         print(f"[GitMCPHandler] Tentative d'envoi de requête à {self.mcp_server_url} pour la méthode {method}")

#         payload = {
#             "jsonrpc": "2.0",
#             "method": method,
#             "params": params,
#             "id": 1
#         }

#         try:
#             response = requests.post(self.mcp_server_url, json=payload, timeout=30)
#             response.raise_for_status()

#             response_data = response.json()
#             if "error" in response_data:
#                 error_message = response_data["error"].get("message", "Erreur inconnue du serveur MCP")
#                 error_code = response_data["error"].get("code", -1)
#                 raise RuntimeError(f"Erreur du serveur MCP [{error_code}]: {error_message}")
            
#             return response_data.get("result", {})

#         except requests.exceptions.Timeout:
#             raise RuntimeError("Le serveur MCP n'a pas répondu dans le délai imparti.")
#         except requests.exceptions.ConnectionError as e:
#             raise RuntimeError(f"Impossible de se connecter au serveur MCP à {self.mcp_server_url}: {e}")
#         except requests.exceptions.RequestException as e:
#             raise RuntimeError(f"Erreur lors de la communication HTTP avec le serveur MCP: {e}")
#         except Exception as e:
#             print(f"Erreur de communication avec le serveur MCP à {self.mcp_server_url}: {e}")
#             raise RuntimeError("Échec de la communication avec le serveur MCP.") from e





