import streamlit as st, requests, time, os, base64, json, schedule
from gtts import gTTS
from datetime import datetime
import threading

st.set_page_config(page_title="Usine 30 Jours", layout="wide")
st.title("🏭 USINE 30 JOURS - PROJETS LOURDS AUTO")
if not os.path.exists("projets"): os.mkdir("projets")

KEYS = {"BACKEND":[os.getenv("DS1"),os.getenv("DS2"),os.getenv("GR1"),os.getenv("GR2")],"FRONTEND":[os.getenv("DS3"),os.getenv("DS4"),os.getenv("GR3"),os.getenv("GR4")],"QA":[os.getenv("DS1"),os.getenv("DS3"),os.getenv("GR1"),os.getenv("GR3")],"BOSS":[os.getenv("DS2"),os.getenv("DS4"),os.getenv("GR2"),os.getenv("GR4")]}
C=0
RUNNING=False

def call(agent, tache, img=None):
    global C;i=C%4;C+=1;cle=KEYS[agent][i]
    u="https://api.deepseek.com/v1/chat/completions"if"sk-"in cle else"https://api.groq.com/openai/v1/chat/completions"
    m="deepseek-chat"if"sk-"in cle else"llama3-70b-8192"
    content=[{"type":"text","text":tache},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}"}}] if img else tache
    r=requests.post(u,headers={"Authorization":f"Bearer {cle}"},json={"model":m,"messages":[{"role":"system","content":agent},{"role":"user","content":content}]},timeout=180)
    time.sleep(10)
    return r.json()['choices'][0]['message']['content']

def save_project(nom, etape, data):
    with open(f"projets/{nom}.json","w") as f: json.dump({"nom":nom,"etape":etape,"data":data,"date":str(datetime.now())},f)

def load_project(nom):
    with open(f"projets/{nom}.json") as f: return json.load(f)

# FONCTION QUI TOURNE 1 FOIS PAR JOUR
def travailler_module():
    global RUNNING
    if not RUNNING: return

    for p in os.listdir("projets"):
        data = load_project(p.replace(".json",""))
        if data["etape"] == "TERMINÉ": continue

        modules = data.get("plan",[])
        module_actuel = int(data["etape"].split("/")[0].split(" ")[1]) - 1

        if module_actuel >= len(modules):
            data["etape"] = "TERMINÉ"
            save_project(data["nom"], "TERMINÉ", data["data"])
            continue

        module = modules[module_actuel]
        st.write(f"[{datetime.now()}] Travail sur: {module}")

        b=call("BACKEND",f"Code backend Python Flask pour module {module} de {data['nom']}")
        f=call("FRONTEND",f"Code frontend Android Kotlin pour module {module} de {data['nom']}")
        q=call("QA",f"Teste et intègre le module {module}. Code: {b}+{f}")
        bo=call("BOSS",f"Documente le module {module} pour {data['nom']}")

        code_total = data["data"] + f"\n\n=== {module} ===\n{b}\n{f}\n{q}\n{bo}"
        save_project(data["nom"], f"Module {module_actuel+2}/{len(modules)}", code_total)
        time.sleep(3600) # 1h de pause entre modules pour économiser

def run_scheduler():
    schedule.every().day.at("02:00").do(travailler_module) # Travaille à 2h du matin
    while RUNNING:
        schedule.run_pending()
        time.sleep(60)

tab1, tab2, tab3, tab4 = st.tabs(["🏭 USINE 30J", "🎤 ASSISTANT", "📁 GÉNÉRATEUR", "📦 MES PROJETS"])

with tab1:
    st.header("Lancer un projet pour 30 jours")
    type_projet = st.selectbox("Type", ["Réseau Social Facebook", "Jeu Battle Royale Free Fire", "App E-commerce Jumia"])
    nom_projet = st.text_input("Nom", "Face237")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("DÉMARRER L'USINE 30J", type="primary"):
            global RUNNING
            RUNNING=True
            modules = {"Réseau Social Facebook": ["Auth", "Fil Actu", "Like/Com", "Profil/Amis", "Chat", "Admin", "Stories", "Reels", "Notifs", "Paiement"],"Jeu Battle Royale Free Fire": ["Moteur 2D", "Tir/PV", "Map1", "Boutique", "Multi", "Sauvegarde", "Armes", "Véhicules", "Event", "Classement"]}
            save_project(nom_projet, "Module 1/10", "")
            threading.Thread(target=run_scheduler, daemon=True).start()
            st.success(f"✅ {nom_projet} lancé. Les agents bossent 1 module/jour à 2h du matin")

    with col2:
        if st.button("ARRÊTER L'USINE"):
            RUNNING=False
            st.warning("Usine en pause")

with tab2: # Assistant identique
    st.header("Assistant Photo + Search + Vocal")
    question = st.text_input("Ta question")
    if st.button("RÉPONDRE"):
        s=call("FRONTEND",f"Cherche: {question}")
        vo=call("QA",f"Résume en 3 phrases: {s}")
        tts = gTTS(vo, lang='fr'); tts.save("reponse.mp3")
        st.write(s); st.audio("reponse.mp3")

with tab3: # Générateur identique
    st.header("Générer fichier")
    type_f = st.selectbox("Type", ["TXT","CODE.py","CODE.kt","PDF"])
    contenu = st.text_area("Contenu")
    if st.button("GÉNÉRER"):
        fichier=call("BOSS",f"Génère {type_f}: {contenu}")
        st.download_button("Télécharger", fichier, f"fichier.{type_f.split('.')[-1]}")

with tab4:
    st.header("Avancement 30 Jours")
    for p in os.listdir("projets"):
        data = load_project(p.replace(".json",""))
        st.progress(int(data["etape"].split("/")[0].split(" ")[1]) / 10)
        st.write(f"**{data['nom']}** - {data['etape']} - {data['date']}")
        st.download_button("Télécharger", data['data'], p.replace(".json",".txt"))
