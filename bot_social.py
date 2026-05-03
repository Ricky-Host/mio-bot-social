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
    
# 1. PLANNER (DIRETTORE STRATEGICO) - Ora focalizzato su Industria 4.0/5.0
    planner = Agent(
        role='Direttore Strategico di Automazione Industriale', 
        goal='''Individuare innovazioni concrete in tre settori chiave: 
                1. Food Processing (lavorazione carne, zuppe, efficienza energetica, incentivi Italia).
                2. Logistica Interna (AGV, muletti autonomi, rulliere, integrazione software).
                3. Biogas (automazione elettrica, SCADA intelligenti, processi autonomi).''',
        backstory='''Sei un esperto di consulenza industriale. Il tuo obiettivo è trovare tecnologie che 
                portino vantaggi reali ai produttori: aumento del margine, riduzione dei costi, 
                diminuzione dei tempi di fermo macchina e facilità di ripartenza post-guasto.
                Guardi alle novità dei grandi player (Siemens, Rockwell, ecc.) e cerchi soluzioni che 
                uniscano meccanica avanzata, elettronica e software (sistemi di visione, AI integrata negli SCADA, 
                bot di supporto per operatori nel settaggio impianti).''', 
        llm=llm
    )
    
    # 2. SCOUTER (RICERCATORE TECNICO) - Aggiornato per cercare hardware e software
    scouter = Agent(
        role='Ingegnere Ricercatore Senior',
        goal='Trovare schede tecniche, casi studio e novità hardware/software sui temi scelti dal Planner.',
        backstory='''Sei un ingegnere che non si ferma alla superficie. Cerchi dettagli tecnici su 
                nuovi sensori di visione, algoritmi di manutenzione predittiva per il Biogas, 
                nuovi motori ad alta efficienza per il Food o novità software da leader come Siemens e Rockwell. 
                Ti interessi di come il software semplifica la gestione meccanica.''',
        tools=[ricerca_web],
        llm=llm
    )
    
# 2. WRITER (IL COPYWRITER TECNICO B2B)
        writer = Agent(
        role='Senior Engineering Manager & Copywriter',
        goal='Scrivere post tecnici che posizionino l autore come un leader di pensiero (Top Voice) nell Automazione Industriale.',
        backstory='''Sei un ingegnere con 15 anni di esperienza in stabilimento. Non fai il giornalista, fai l'analista. 
        Quando parli di una nuova tecnologia, non ti limiti a descriverla, ma spieghi il "Perché è importante oggi" e il "Cosa cambia per le aziende".
        Usi un tono pragmatico, diretto e basato sui numeri (es. efficienza, ROI, riduzione guasti).
        Condividi le informazioni come se fossero "Lezioni imparate sul campo" o "Insight strategici".
        ... (mantieni le regole di formattazione di prima) ...''',
        llm=llm
    )



    task_1 = Task(description='Decidi l argomento di oggi.', expected_output='1 frase.', agent=planner)
    
    # Task aggiornato con focus sulla formattazione
    task_2 = Task(
        description='''Scrivi 1 post LinkedIn e 1 post X. 
        Formatta il post LinkedIn seguendo rigorosamente le regole del Writer (paragrafi corti, righe vuote, elenchi puntati).
        Dividili ESATTAMENTE inserendo la stringa "||SEPARATORE||" tra l uno e l altro. Non usare JSON.''', 
        expected_output='Post LinkedIn (ben spaziato) ||SEPARATORE|| Post X', 
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

    # Scriviamo sul foglio (Data, Argomento, LinkedIn, X, Stato)
    scrivi_post_su_sheet("Ricerca Automatica", post_ln, post_x)

if __name__ == "__main__":
    esecuzione_autonoma()
