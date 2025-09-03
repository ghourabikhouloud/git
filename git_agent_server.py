# import os
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# import google.generativeai as genai
# from dotenv import load_dotenv

# # Importe le handler qui pilote Docker
# from git_mcp_handler import GitMCPHandler

# # --- Configuration ---
# # Charge les variables depuis le fichier .env à la racine du projet
# load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# # Récupère les clés
# GITHUB_PAT = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# if not GITHUB_PAT or not GOOGLE_API_KEY:
#     raise ValueError("Les variables GITHUB_PERSONAL_ACCESS_TOKEN et GOOGLE_API_KEY doivent être définies dans le fichier .env")

# genai.configure(api_key=GOOGLE_API_KEY)

# # --- Initialisation ---
# app = FastAPI()
# mcp_handler = GitMCPHandler(github_pat=GITHUB_PAT)
# AVAILABLE_TOOLSETS_CACHE = None # Cache pour la liste des toolsets

# @app.on_event("startup")
# def startup_event():
#     mcp_handler.start_server()

# @app.on_event("shutdown")
# def shutdown_event():
#     mcp_handler.stop_server()

# # --- Modèle de Requête A2A ---
# class TaskRequest(BaseModel):
#     taskId: str
#     message: dict

# # --- Logique du Proxy Intelligent ---
# @app.post("/v1/tasks/send")
# async def send_task(request: TaskRequest):
#     global AVAILABLE_TOOLSETS_CACHE
#     user_prompt = request.message["parts"][0]["text"]
    
#     try:
#         # ÉTAPE 1: Découvrir les toolsets disponibles (une seule fois)
#         if AVAILABLE_TOOLSETS_CACHE is None:
#             print("[GitAgentProxy] Récupération des toolsets depuis le MCP Server...")
#             response = mcp_handler.send_request(method="mcp/listToolsets", params={})
#             AVAILABLE_TOOLSETS_CACHE = response.get('result', {}).get('toolsets', [])
#             print(f"[GitAgentProxy] Toolsets disponibles : {AVAILABLE_TOOLSETS_CACHE}")

#         if not AVAILABLE_TOOLSETS_CACHE:
#             raise RuntimeError("Impossible de récupérer les toolsets.")

#         # ÉTAPE 2: Laisser l'IA choisir le toolset le plus pertinent
#         prompt_for_selection = f"""
#         À partir du prompt utilisateur, choisis le toolset le plus approprié dans la liste suivante.
#         Ne réponds QUE par le nom exact du toolset (ex: 'repos' ou 'issues').

#         Prompt Utilisateur: "{user_prompt}"
#         Liste des Toolsets: {', '.join(AVAILABLE_TOOLSETS_CACHE)}
#         """
        
#         selection_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
#         selection_response = selection_model.generate_content(prompt_for_selection)
#         selected_toolset = selection_response.text.strip().replace("'", "").replace('"', '')
        
#         print(f"[GitAgentProxy] L'IA a sélectionné le toolset : '{selected_toolset}'")

#         if selected_toolset not in AVAILABLE_TOOLSETS_CACHE:
#              raise ValueError(f"L'IA a choisi un toolset invalide : '{selected_toolset}'")

#         # ÉTAPE 3: Activer le toolset et envoyer le prompt au MCP Server pour exécution
#         print(f"[GitAgentProxy] Activation de '{selected_toolset}' et envoi du prompt au MCP Server...")
#         final_response = mcp_handler.send_request(
#             method="mcp/performToolRequest",
#             params={
#                 "toolsets": [selected_toolset],
#                 "prompt": user_prompt
#             }
#         )

#         # ÉTAPE 4: Retourner le résultat au format A2A
#         return {
#             "task": {
#                 "taskId": request.taskId,
#                 "state": "completed",
#                 "messages": [{"role": "agent", "parts": [{"json": final_response.get('result', {})}]}]
#             }
#         }

#     except Exception as e:
#         print(f"Erreur lors du traitement de la tâche Git (via MCP) : {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# import json
# import os
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel, Field
# import google.generativeai as genai
# from dotenv import load_dotenv

# # On n'importe plus que le handler MCP
# from git_mcp_handler import GitMCPHandler

# # --- Configuration ---
# load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# GITHUB_PAT = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# if not GITHUB_PAT or not GOOGLE_API_KEY:
#     raise ValueError("GITHUB_PERSONAL_ACCESS_TOKEN et GOOGLE_API_KEY sont requis.")

# genai.configure(api_key=GOOGLE_API_KEY)

# # --- Initialisation de l'application et du handler MCP ---
# app = FastAPI()
# mcp_handler = GitMCPHandler(github_pat=GITHUB_PAT)
# AVAILABLE_TOOLS_CACHE = None
# ENABLED_TOOLSETS = set() # <--- Déclarez-le ici au niveau global du module

# @app.on_event("startup")
# def startup_event():
#     mcp_handler.start_server()

# @app.on_event("shutdown")
# def shutdown_event():
#     mcp_handler.stop_server()

# # --- Modèle de Requête A2A ---
# # Note: repo_path n'est plus nécessaire ici, l'agent travaille sur les dépôts distants
# class TaskRequest(BaseModel):
#     taskId: str
#     message: dict # On attend maintenant un dictionnaire 'message'

# # --- Endpoint de l'Agent (Logique du Proxy Intelligent) ---
# # @app.post("/v1/tasks/send")
# # async def send_task(request: TaskRequest):
# #     global AVAILABLE_TOOLSETS_CACHE
# #     user_prompt = request.message["parts"][0]["text"]
    
# #     try:
# #         # ÉTAPE 1: Découvrir les toolsets disponibles (une seule fois)
# #         if AVAILABLE_TOOLSETS_CACHE is None:
# #             print("[AgentProxy] Récupération des toolsets depuis le MCP Server...")
# #             response = mcp_handler.send_request(method="tools/list", params={})
# #             AVAILABLE_TOOLSETS_CACHE = response.get('result', {}).get('toolsets', [])
# #             print(f"[AgentProxy] Toolsets disponibles : {AVAILABLE_TOOLSETS_CACHE}")

# #         if not AVAILABLE_TOOLSETS_CACHE:
# #             raise RuntimeError("Impossible de récupérer les toolsets.")

# #         # ÉTAPE 2: Laisser l'IA choisir le toolset le plus pertinent
# #         prompt_for_selection = f"""
# #         À partir du prompt utilisateur, choisis le 'toolset' le plus approprié dans la liste suivante.
# #         Ne réponds QUE par le nom exact du toolset (ex: 'repos' ou 'issues' ou 'pull_requests').

# #         Prompt Utilisateur: "{user_prompt}"
# #         Liste des Toolsets: {', '.join(AVAILABLE_TOOLSETS_CACHE)}
# #         """
        
# #         selection_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
# #         selection_response = selection_model.generate_content(prompt_for_selection)
# #         selected_toolset = selection_response.text.strip().replace("'", "").replace('"', '')
        
# #         print(f"[AgentProxy] L'IA a sélectionné le toolset : '{selected_toolset}'")

# #         if selected_toolset not in AVAILABLE_TOOLSETS_CACHE:
# #              raise ValueError(f"L'IA a choisi un toolset invalide : '{selected_toolset}'")

# #         # ÉTAPE 3: Activer le toolset et envoyer le prompt au MCP Server pour exécution
# #         print(f"[AgentProxy] Activation de '{selected_toolset}' et envoi du prompt au MCP Server...")
# #         final_response = mcp_handler.send_request(
# #             method="mcp/performToolRequest",
# #             params={
# #                 "toolsets": [selected_toolset],
# #                 "prompt": user_prompt
# #             }
# #         )

# #         # ÉTAPE 4: Retourner le résultat au format A2A
# #         return {
# #             "taskId": request.taskId,
# #             "state": "completed",
# #             "result": final_response.get('result', {})
# #         }

# #     except Exception as e:
# #         print(f"Erreur lors du traitement de la tâche (via MCP) : {e}")
# #         raise HTTPException(status_code=500, detail=str(e))
# @app.post("/v1/tasks/send")
# async def send_task(request: TaskRequest):
#     global AVAILABLE_TOOLS_CACHE
#     user_prompt = request.message["parts"][0]["text"]
    
#     try:
#         # ÉTAPE 1: Découvrir les OUTILS EXECUTABLES disponibles (une seule fois)
#         if AVAILABLE_TOOLS_CACHE is None:
#             print("[AgentProxy] Construction de la liste des outils (gestion + spécifiques avec notation par points) pour l'IA...")
            
#             all_executable_tools = []
            
#             try:
#                 # 1. Obtenir la liste des outils de gestion directement exposés par 'tools/list'
#                 # Ces outils sont censés être directement appelables.
#                 # Simuler la réponse de mcp_handler.send_request
#                 response_tools_list = mcp_handler.send_request(method="tools/list", params={})
#                 management_tool_names = [tool.get('name') for tool in response_tools_list.get('tools', []) if tool.get('name')]
#                 all_executable_tools.extend(management_tool_names)
#                 print(f"[AgentProxy] Outils de gestion trouvés via 'tools/list' : {management_tool_names}")
                
#                 # 2. Ajouter les outils GitHub spécifiques que vous avez listés, 
#                 # en utilisant la notation "Catégorie.nom_outil"
                
#                 # Catégorie "Pull Requests"
#                 all_executable_tools.extend([
#                     "Pull Requests.add_comment_to_pending_review", 
#                     "Pull Requests.create_and_submit_pull_request_review", 
#                     "Pull Requests.create_pending_pull_request_review", 
#                     "Pull Requests.create_pull_request", 
#                     "Pull Requests.delete_pending_pull_request_review", 
#                     "Pull Requests.get_pull_request", 
#                     "Pull Requests.get_pull_request_comments", 
#                     "Pull Requests.get_pull_request_diff", 
#                     "Pull Requests.get_pull_request_files", 
#                     "Pull Requests.get_pull_request_reviews", 
#                     "Pull Requests.get_pull_request_status", 
#                     "Pull Requests.list_pull_requests", 
#                     "Pull Requests.merge_pull_request", 
#                     "Pull Requests.request_copilot_review", 
#                     "Pull Requests.search_pull_requests", 
#                     "Pull Requests.submit_pending_pull_request_review", 
#                     "Pull Requests.update_pull_request", 
#                     "Pull Requests.update_pull_request_branch",
#                 ])

#                 # Catégorie "Repositories"
#                 all_executable_tools.extend([
#                     "Repositories.create_branch", 
#                     "Repositories.create_or_update_file", 
#                     "Repositories.create_repository", 
#                     "Repositories.delete_file", 
#                     "Repositories.fork_repository", 
#                     "Repositories.get_commit", 
#                     "Repositories.get_file_contents", 
#                     "Repositories.get_latest_release", 
#                     "Repositories.get_release_by_tag", 
#                     "Repositories.get_tag", 
#                     "Repositories.list_branches", 
#                     "Repositories.list_commits", 
#                     "Repositories.list_releases", 
#                     "Repositories.list_tags", 
#                     "Repositories.push_files", 
#                     "Repositories.search_code", 
#                     "Repositories.search_repositories",
#                 ])
                
#             except Exception as e:
#                 print(f"[AgentProxy] Échec de la récupération dynamique des outils. Utilisation d'une liste fixe de secours : {e}")
#                 all_executable_tools = [
#                     "enable_toolset", "get_toolset_tools", "list_available_toolsets", 
#                     "Pull Requests.add_comment_to_pending_review", "Pull Requests.create_and_submit_pull_request_review", 
#                     "Pull Requests.create_pending_pull_request_review", "Pull Requests.create_pull_request", 
#                     "Pull Requests.delete_pending_pull_request_review", "Pull Requests.get_pull_request", 
#                     "Pull Requests.get_pull_request_comments", "Pull Requests.get_pull_request_diff", 
#                     "Pull Requests.get_pull_request_files", "Pull Requests.get_pull_request_reviews", 
#                     "Pull Requests.get_pull_request_status", "Pull Requests.list_pull_requests", 
#                     "Pull Requests.merge_pull_request", "Pull Requests.request_copilot_review", 
#                     "Pull Requests.search_pull_requests", "Pull Requests.submit_pending_pull_request_review", 
#                     "Pull Requests.update_pull_request", "Pull Requests.update_pull_request_branch",
#                     "Repositories.create_branch", "Repositories.create_or_update_file", "Repositories.create_repository", 
#                     "Repositories.delete_file", "Repositories.fork_repository", "Repositories.get_commit", "Repositories.get_file_contents", 
#                     "Repositories.get_latest_release", "Repositories.get_release_by_tag", "Repositories.get_tag", 
#                     "Repositories.list_branches", "Repositories.list_commits", "Repositories.list_releases", "Repositories.list_tags", 
#                     "Repositories.push_files", "Repositories.search_code", "Repositories.search_repositories"
#                 ]
            
#             AVAILABLE_TOOLS_CACHE = list(set(all_executable_tools)) 
#             print(f"[AgentProxy] Tous les outils exécutables disponibles pour l'IA : {AVAILABLE_TOOLS_CACHE}")

#         if not AVAILABLE_TOOLS_CACHE:
#             raise RuntimeError("Aucun outil exécutable disponible pour le traitement.")

#         # ÉTAPE 2: Laisser l'IA choisir l'OUTIL EXÉCUTABLE le plus pertinent (AVEC NOTATION PAR POINTS)
#         prompt_for_selection = f"""
#         À partir du prompt utilisateur, choisis le NOM EXACT (UN SEUL NOM) de l'outil exécutable le plus approprié dans la liste suivante.
#         Les outils sont nommés avec la catégorie suivie d'un point et du nom de l'action (ex: 'Repositories.create_or_update_file').
#         Par exemple, si la tâche est de créer un fichier, choisis 'Repositories.create_or_update_file'. Si c'est de rechercher un dépôt, choisis 'Repositories.search_repositories'.
#         Si la tâche est de lister les toolsets disponibles, choisis 'list_available_toolsets'.

#         Réponds UNIQUEMENT par le NOM EXACT (un mot ou une phrase courte si c'est le nom de l'outil) de l'outil sélectionné, sans explication, ni texte additionnel, ni sauts de ligne.

#         Prompt Utilisateur: "{user_prompt}"
#         Liste des Outils Exécutables: {', '.join(AVAILABLE_TOOLS_CACHE)}
#         """
        
#         selection_model = genai(model_name="gemini-1.5-flash") # Utilisation du Mock
#         selection_response = selection_model.generate_content(prompt_for_selection)
        
#         selected_tool_raw = selection_response.text.strip()
#         selected_tool_cleaned = selected_tool_raw.replace("'", "").replace('"', '')
#         selected_tool = selected_tool_cleaned 
        
#         print(f"[AgentProxy] L'IA a sélectionné l'outil : '{selected_tool}'")

#         if selected_tool not in AVAILABLE_TOOLS_CACHE:
#              raise ValueError(f"L'IA a choisi un outil invalide : '{selected_tool}' parmi {AVAILABLE_TOOLS_CACHE}")

#         # ÉTAPE 3: Laisser l'IA extraire les paramètres spécifiques pour l'outil sélectionné
#         extracted_params = {}
        
#         param_extraction_prompt = f"""
#         À partir du prompt utilisateur: "{user_prompt}" et sachant que l'outil sélectionné est '{selected_tool}', 
#         extrais les paramètres nécessaires pour cet outil.
#         Formate la sortie comme un objet JSON PUR (sans '```json' ni '```' ou tout autre texte explicatif).

#         Exemples pour l'outil 'Repositories.create_or_update_file':
#         Prompt: "Dans le dépôt 'ghourabikhouloud/Centre-Commerciale-web-distribu-', crée un nouveau fichier nommé 'test.txt' avec le contenu 'hello world' et fais un commit directement sur la branche 'main' avec le message 'Ajout du fichier de test via l'agent'."
#         Sortie JSON attendue:
#         {{
#             "owner": "ghourabikhouloud",
#             "repo": "Centre-Commerciale-web-distribu-",
#             "path": "test.txt",
#             "content": "hello world",
#             "message": "Ajout du fichier de test via l'agent",
#             "branch": "main" 
#         }}
        
#         Exemples pour l'outil 'Repositories.get_file_contents':
#         Prompt: "Obtiens le contenu du fichier 'src/main.js' dans 'myuser/myrepo'."
#         Sortie JSON attendue:
#         {{
#             "owner": "myuser",
#             "repo": "myrepo",
#             "path": "src/main.js",
#             "branch": "main" 
#         }}

#         Exemples pour l'outil 'Repositories.create_repository':
#         Prompt: "Crée un nouveau dépôt privé nommé 'mon-nouveau-repo' pour 'monutilisateur'."
#         Sortie JSON attendue:
#         {{
#             "name": "mon-nouveau-repo",
#             "private": true
#             "owner": "monutilisateur" 
#         }}

#         Exemples pour l'outil 'Pull Requests.create_pull_request':
#         Prompt: "Ouvre une nouvelle pull request de la branche 'feature-x' vers 'main' dans 'monutilisateur/monrepo' avec le titre 'Ajouter la fonctionnalité X' et la description 'Ceci ajoute une nouvelle fonctionnalité'."
#         Sortie JSON attendue:
#         {{
#             "owner": "monutilisateur",
#             "repo": "monrepo",
#             "head": "feature-x",
#             "base": "main",
#             "title": "Ajouter la fonctionnalité X",
#             "body": "Ceci ajoute une nouvelle fonctionnalité"
#         }}

#         Exemples pour l'outil 'list_available_toolsets':
#         Prompt: "Liste tous les toolsets disponibles."
#         Sortie JSON attendue:
#         {{}}

#         Assure-toi que les valeurs 'owner' et 'repo' sont toujours extraites du format 'owner/repo' ou identifiées séparément.
#         Si une branche n'est pas spécifiée pour les opérations de fichier/commit, utilise 'main' par défaut si l'outil le permet.
#         Si aucun paramètre n'est nécessaire, retourne un objet JSON vide {{}}.
#         Ne retourne AUCUN texte supplémentaire, seulement l'objet JSON.
#         """
        
#         params_model = genai(model_name="gemini-1.5-flash") # Utilisation du Mock
#         params_response = params_model.generate_content(param_extraction_prompt)

#         try:
#             cleaned_json_string = params_response.text.strip()
#             if cleaned_json_string.startswith("```json"):
#                 cleaned_json_string = cleaned_json_string[len("```json"):].strip()
#             if cleaned_json_string.endswith("```"):
#                 cleaned_json_string = cleaned_json_string[:-len("```")].strip()
            
#             if not cleaned_json_string:
#                 extracted_params = {}
#             else:
#                 extracted_params = json.loads(cleaned_json_string)
#             print(f"[AgentProxy] Paramètres extraits par l'IA : {extracted_params}")
#         except json.JSONDecodeError as e:
#             print(f"[AgentProxy] L'IA n'a pas renvoyé un JSON valide pour les paramètres. Erreur: {e}. Réponse brute: {params_response.text}")
#             raise ValueError(f"L'IA n'a pas pu extraire les paramètres de manière valide. Réponse brute: {params_response.text}")

#         # ÉTAPE 4: Envoyer la requête à l'outil sélectionné via un appel DIRECT
#         print(f"[AgentProxy] Exécution de l'outil '{selected_tool}' via un appel direct avec les paramètres : {extracted_params}")
        
#         # --- DÉBUT DE LA CORRECTION ---
#         method_to_call_mcp = selected_tool
#         # Si le nom de l'outil contient un point (c'est-à-dire une catégorie),
#         # extraire seulement le nom de l'action après le dernier point.
#         if '.' in selected_tool:
#             method_to_call_mcp = selected_tool.split('.')[-1]
#             print(f"[AgentProxy] Le nom de la méthode envoyé au MCP a été ajusté à : '{method_to_call_mcp}' (original: '{selected_tool}')")
#         # --- FIN DE LA CORRECTION ---

#         final_response = mcp_handler.send_request(
#             method=method_to_call_mcp, # Utiliser le nom de méthode ajusté
#             params=extracted_params 
#         )

#         # ÉTAPE 5: Retourner le résultat au format A2A
#         return {
#             "taskId": request.taskId,
#             "state": "completed",
#             "result": final_response 
#         }

#     except Exception as e:
#         print(f"Erreur lors du traitement de la tâche (via MCP) : {e}")
#         error_detail = str(e)
#         raise HTTPException(status_code=500, detail=error_detail)


import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import google.generativeai as genai
from dotenv import load_dotenv

# On n'importe plus que le handler MCP
from git_mcp_handler import GitMCPHandler

# --- Configuration ---
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

GITHUB_PAT = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GITHUB_PAT or not GOOGLE_API_KEY:
    raise ValueError("GITHUB_PERSONAL_ACCESS_TOKEN et GOOGLE_API_KEY sont requis.")

genai.configure(api_key=GOOGLE_API_KEY)

# --- Initialisation de l'application et du handler MCP ---
app = FastAPI()
mcp_handler = GitMCPHandler(github_pat=GITHUB_PAT)
AVAILABLE_TOOLS_CACHE = None
# ENABLED_TOOLSETS n'est plus strictement nécessaire pour la logique actuelle
# car le MCP gère l'activation dynamique, mais on peut le laisser si on prévoit d'autres usages.
ENABLED_TOOLSETS = set() 

@app.on_event("startup")
def startup_event():
    mcp_handler.start_server()

@app.on_event("shutdown")
def shutdown_event():
    mcp_handler.stop_server()

# --- Modèle de Requête A2A ---
class TaskRequest(BaseModel):
    taskId: str
    message: dict

@app.post("/v1/tasks/send")
async def send_task(request: TaskRequest):
    global AVAILABLE_TOOLS_CACHE, ENABLED_TOOLSETS
    user_prompt = request.message["parts"][0]["text"]
    
    try:
        # ÉTAPE 1: Découvrir les OUTILS EXECUTABLES disponibles (une seule fois)
        if AVAILABLE_TOOLS_CACHE is None:
            print("[AgentProxy] Construction de la liste des outils (gestion + spécifiques avec notation par points) pour l'IA...")
            
            all_executable_tools = []
            try:
                response_tools_list = mcp_handler.send_request(method="tools/list", params={})
                # Le serveur MCP renvoie les noms d'outils complets et qualifiés via tools/list
                management_tool_names = [tool.get('name') for tool in response_tools_list.get('tools', []) if tool.get('name')]
                all_executable_tools.extend(management_tool_names)
                print(f"[AgentProxy] Outils de gestion trouvés via 'tools/list' : {management_tool_names}")
                
                # Catégorie Pull Requests - Ajout manuel de la liste complète des noms qualifiés
                all_executable_tools.extend([
                    "Pull Requests.add_comment_to_pending_review", 
                    "Pull Requests.create_and_submit_pull_request_review", 
                    "Pull Requests.create_pending_pull_request_review", 
                    "Pull Requests.create_pull_request", 
                    "Pull Requests.delete_pending_pull_request_review", 
                    "Pull Requests.get_pull_request", 
                    "Pull Requests.get_pull_request_comments", 
                    "Pull Requests.get_pull_request_diff", 
                    "Pull Requests.get_pull_request_files", 
                    "Pull Requests.get_pull_request_reviews", 
                    "Pull Requests.get_pull_request_status", 
                    "Pull Requests.list_pull_requests", 
                    "Pull Requests.merge_pull_request", 
                    "Pull Requests.request_copilot_review", 
                    "Pull Requests.search_pull_requests", 
                    "Pull Requests.submit_pending_pull_request_review", 
                    "Pull Requests.update_pull_request", 
                    "Pull Requests.update_pull_request_branch",
                ])

                # Catégorie Repositories - Ajout manuel de la liste complète des noms qualifiés
                all_executable_tools.extend([
                    "Repositories.create_branch", 
                    "Repositories.create_or_update_file", 
                    "Repositories.create_repository", 
                    "Repositories.delete_file", 
                    "Repositories.fork_repository", 
                    "Repositories.get_commit", 
                    "Repositories.get_file_contents", 
                    "Repositories.get_latest_release", 
                    "Repositories.get_release_by_tag", 
                    "Repositories.get_tag", 
                    "Repositories.list_branches", 
                    "Repositories.list_commits", 
                    "Repositories.list_releases", 
                    "Repositories.list_tags", 
                    "Repositories.push_files", 
                    "Repositories.search_code", 
                    "Repositories.search_repositories",
                ])
                
            except Exception as e:
                print(f"[AgentProxy] Échec de la récupération dynamique des outils. Utilisation d'une liste fixe de secours : {e}")
                # La liste de secours DOIT aussi utiliser les noms qualifiés complets pour correspondre à l'IA
                all_executable_tools = [
                    "enable_toolset", "get_toolset_tools", "list_available_toolsets", # Outils de gestion
                    "Pull Requests.add_comment_to_pending_review", "Pull Requests.create_and_submit_pull_request_review", 
                    "Pull Requests.create_pending_pull_request_review", "Pull Requests.create_pull_request", 
                    "Pull Requests.delete_pending_pull_request_review", "Pull Requests.get_pull_request", 
                    "Pull Requests.get_pull_request_comments", "Pull Requests.get_pull_request_diff", 
                    "Pull Requests.get_pull_request_files", "Pull Requests.get_pull_request_reviews", 
                    "Pull Requests.get_pull_request_status", "Pull Requests.list_pull_requests", 
                    "Pull Requests.merge_pull_request", "Pull Requests.request_copilot_review", 
                    "Pull Requests.search_pull_requests", "Pull Requests.submit_pending_pull_request_review", 
                    "Pull Requests.update_pull_request", "Pull Requests.update_pull_request_branch",
                    "Repositories.create_branch", "Repositories.create_or_update_file", "Repositories.create_repository", 
                    "Repositories.delete_file", "Repositories.fork_repository", "Repositories.get_commit", "Repositories.get_file_contents", 
                    "Repositories.get_latest_release", "Repositories.get_release_by_tag", "Repositories.get_tag", 
                    "Repositories.list_branches", "Repositories.list_commits", "Repositories.list_releases", "Repositories.list_tags", 
                    "Repositories.push_files", "Repositories.search_code", "Repositories.search_repositories"
                ]
            
            AVAILABLE_TOOLS_CACHE = list(set(all_executable_tools)) 
            print(f"[AgentProxy] Tous les outils exécutables disponibles pour l'IA : {AVAILABLE_TOOLS_CACHE}")

        if not AVAILABLE_TOOLS_CACHE:
            raise RuntimeError("Aucun outil exécutable disponible pour le traitement.")

        # ÉTAPE 2: Sélection de l'outil
        prompt_for_selection = f"""
        À partir du prompt utilisateur, choisis le NOM EXACT (UN SEUL NOM) de l'outil exécutable le plus approprié dans la liste suivante.
        Les outils sont nommés avec la catégorie suivie d'un point et du nom de l'action (ex: 'Repositories.create_or_update_file').
        Réponds UNIQUEMENT par le NOM EXACT.

        Prompt Utilisateur: "{user_prompt}"
        Liste des Outils Exécutables: {', '.join(AVAILABLE_TOOLS_CACHE)}
        """
        
        selection_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        selection_response = selection_model.generate_content(prompt_for_selection)
        
        selected_tool = selection_response.text.strip().replace("'", "").replace('"', '')
        print(f"[AgentProxy] L'IA a sélectionné l'outil : '{selected_tool}'")

        if selected_tool not in AVAILABLE_TOOLS_CACHE:
            raise ValueError(f"L'IA a choisi un outil invalide : '{selected_tool}'")

        # ÉTAPE 3: Extraction des paramètres
        param_extraction_prompt = f"""
        À partir du prompt utilisateur: "{user_prompt}" et sachant que l'outil sélectionné est '{selected_tool}', 
        extrais les paramètres nécessaires pour cet outil.
        Retourne UNIQUEMENT un objet JSON pur.
        """
        
        params_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        params_response = params_model.generate_content(param_extraction_prompt)

        try:
            cleaned_json_string = params_response.text.strip()
            if cleaned_json_string.startswith("```json"):
                cleaned_json_string = cleaned_json_string[len("```json"):].strip()
            if cleaned_json_string.endswith("```"):
                cleaned_json_string = cleaned_json_string[:-len("```")].strip()
            
            extracted_params = json.loads(cleaned_json_string) if cleaned_json_string else {}
            print(f"[AgentProxy] Paramètres extraits par l'IA : {extracted_params}")
        except json.JSONDecodeError as e:
            raise ValueError(f"L'IA n'a pas renvoyé un JSON valide. Réponse brute: {params_response.text}")

        # --- DÉBUT DE LA SECTION CORRIGÉE ---
        # ÉTAPE 4: Appel direct de l'outil (sans activation explicite du toolset)
        print(f"[AgentProxy] Exécution de l'outil '{selected_tool}' avec les paramètres : {extracted_params}")

        # Le serveur MCP en mode DYNAMIC_TOOLSETS gère l'activation des toolsets implicitement.
        # Nous devons envoyer le nom de l'action SEULEMENT (ex: "create_or_update_file") au MCP
        # pour les outils qualifiés. Pour les outils de gestion, le nom est déjà l'action.

        method_to_call_mcp = selected_tool # Initialisation avec le nom complet
        toolset_name = None # Initialisation pour les logs

        if '.' in selected_tool:
            # Si l'outil est qualifié (ex: "Repositories.create_or_update_file"),
            # nous extrayons le nom du toolset et le nom de l'action.
            parts = selected_tool.split('.', 1)
            toolset_name = parts[0] # Ex: "Repositories" (pour les logs)
            method_to_call_mcp = parts[1] # Ex: "create_or_update_file" (Ceci est ce que le MCP attend)
            print(f"[AgentProxy] Outil qualifié détecté. Toolset: '{toolset_name}', Méthode pour MCP: '{method_to_call_mcp}' (original: '{selected_tool}')")
        else:
            # Pour les outils de gestion (non qualifiés), le nom sélectionné est déjà le nom de la méthode.
            print(f"[AgentProxy] Outil de gestion détecté. Méthode pour MCP: '{method_to_call_mcp}'")

        # La logique précédente d'appel à 'enable_toolset' est supprimée
        # car elle n'est pas nécessaire et n'est pas supportée par le MCP en mode dynamique.

        final_response = mcp_handler.send_request(
            method=method_to_call_mcp, # Envoie le nom de l'action (ex: "create_or_update_file")
            params=extracted_params
        )
        # --- FIN DE LA SECTION CORRIGÉE ---

        # ÉTAPE 5: Retour
        return {
            "taskId": request.taskId,
            "state": "completed",
            "result": final_response 
        }

    except Exception as e:
        print(f"Erreur lors du traitement de la tâche (via MCP) : {e}")
        raise HTTPException(status_code=500, detail=str(e))