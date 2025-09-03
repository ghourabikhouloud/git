import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# Importe le bon handler, celui qui exécute les commandes Git
from git_handler import GitCommandHandler

# --- Configuration ---
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Initialisation de l'application ---
app = FastAPI()
handler = GitCommandHandler()

# --- Modèle de requête A2A ---
class TaskRequest(BaseModel):
    taskId: str
    message: dict

# --- Endpoint A2A principal ---
@app.post("/v1/tasks/send")
async def send_task(request: TaskRequest):
    user_prompt = request.message["parts"][0]["text"]
    
    # --- LE REPO_PATH EST ICI ! ---
    # C'est la variable CRUCIALE pour cet agent, car il travaille en local.
    # Assurez-vous de changer ce chemin pour qu'il pointe vers un projet Git sur votre PC.
    repo_path = "C:/Users/ghour/OneDrive/Bureau/Djangooo/Eco_Style_project"
    
    # Outils que le modèle GenAI peut utiliser pour les opérations Git locales
    tools = {
        "git_commit": lambda message: handler.git_commit(message=message, repo_path=repo_path),
        "git_push": lambda remote, branch: handler.git_push(remote=remote, branch=branch, repo_path=repo_path),
        "git_pull": lambda remote, branch: handler.git_pull(remote=remote, branch=branch, repo_path=repo_path),
        "git_status": lambda: handler.git_status(repo_path=repo_path),
    }

    try:
        # L'IA de l'agent interprète le prompt et choisit l'outil local
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", tools=tools.values())
        response = model.generate_content(user_prompt)
        
        function_call = response.candidates[0].content.parts[0].function_call
        function_name = function_call.name
        function_args = dict(function_call.args)
        
        print(f"[GitAgent Server] L'IA a choisi l'outil : {function_name} avec les arguments : {function_args}")
        
        # Exécution de la fonction choisie
        tool_function = tools.get(function_name)
        if tool_function:
            result = tool_function(**function_args)
        else:
            result = f"Erreur : Outil inconnu '{function_name}'"

        # Formatage de la réponse au standard A2A
        return {
            "task": {
                "taskId": request.taskId,
                "state": "completed",
                "messages": [{"role": "agent", "parts": [{"text": result}]}]
            }
        }
    except Exception as e:
        print(f"Erreur lors du traitement de la tâche git : {e}")
        raise HTTPException(status_code=500, detail=str(e))