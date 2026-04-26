import os
import json
import random
import gspread
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from duckduckgo_search import DDGS
from datetime import datetime

# ==========================================
# 1. RECUPERO CHIAVI (DA AMBIENTE)
# ==========================================
# In GitHub Actions useremo i "Secrets" per non mostrare le chiavi nel codice
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ==========================================
# 2. CONNESSIONE A GOOGLE SHEETS
# ==========================================
def connetti_google_sheets():
    try:
        # Carica le credenziali dal Secret di GitHub (che salveremo come file temporaneo)
        with open('credentials.json', 'w') as f:
            f.write(os.getenv("GOOGLE_CREDENTIALS_JSON"))
        
        gc = gspread.service_account(filename='credentials.json')
        return gc.open("Automazione_AI_Database").sheet1
    except Exception as e:
        print(f"Errore: {e}")
        return None

def scrivi_post_su_sheet(argomento, post_ln, post_x):
    sheet = connetti_google_sheets()
    if sheet:
        data_oggi = datetime.now().strftime("%Y-%m-%d %H:%M")
        # Scriviamo in colonne separate: Data | Argomento | LinkedIn | X | Stato
        sheet.append_row([data_oggi, argomento, post_ln, post_x, "DA PUBBLICARE"])

# ==========================================
# 3. MOTORE AI E AGENTI (MECE INVISIBILE)
# ==========================================
@tool("Ricerca_Tecnica_Avanzata")
def ricerca_web(query: str, **kwargs) -> str:
    """Cerca casi studio tecnici. Inserisci solo testo."""
    try:
        with DDGS() as ddgs:
            risultati = list(ddgs.text(f"{query} case study", max_results=3))
            return str(risultati)
    except: return "Nessun dato."

def esecuzione_autonoma():
    llm = LLM(model="groq/llama-3.3-70b-versatile", api_key=GROQ_API_KEY)

    # 1. PLANNER
    planner = Agent(
        role='Direttore Strategico', 
        goal='Trovare nicchie tecnologiche avanzate.',
        backstory='Sei un analista. Scegli temi complessi ma affascinanti.', 
        llm=llm
    )
    
    # 2. WRITER (IL TOCCO UMANO + MECE INVISIBILE)
    writer = Agent(
        role='Analista Industriale',
        goal='Scrivere analisi tecniche che sembrino post di un umano esperto.',
        backstory='''Applichi una logica ferrea (MECE), ma la nascondi totalmente.
        REGOLE:
        - Vietato citare il metodo MECE o altri framework.
        - Scrittura discorsiva, terza persona, tono freddo ma autorevole.
        - Alterna frasi lunghe e brevi per rompere il ritmo dell'IA.
        - Inizia subito con il dato tecnico, senza saluti.''',
        llm=llm
    )

    task_1 = Task(description='Decidi l argomento di oggi.', expected_output='1 frase.', agent=planner)
    task_2 = Task(
        description='Scrivi 1 post LinkedIn e 1 post X. Dividili ESATTAMENTE inserendo la stringa "||SEPARATORE||" tra l uno e l altro. Non usare JSON, scrivi solo testo normale.', 
        expected_output='Testo post LinkedIn ||SEPARATORE|| Testo post X', 
        agent=writer
    )
    crew = Crew(agents=[planner, writer], tasks=[task_1, task_2])
    risultato = crew.kickoff()
    
risultato_testo = str(risultato)
    
    # Dividiamo il testo usando la nostra parola d'ordine
    if "||SEPARATORE||" in risultato_testo:
        parti = risultato_testo.split("||SEPARATORE||")
        post_ln = parti[0].strip()
        post_x = parti[1].strip()
    else:
        # Se l'AI si dimentica il separatore, mettiamo tutto su LinkedIn
        post_ln = risultato_testo.strip()
        post_x = "Post X non generato correttamente."

    # Scriviamo sul foglio (assicurati che la colonna E sia per lo STATO, o modificala su Fogli)
    scrivi_post_su_sheet(argomento, post_ln, post_x)

if __name__ == "__main__":
    esecuzione_autonoma()
