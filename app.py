import streamlit as st 
import pandas as pd
import os 
from PIL import Image, ImageOps, ImageChops
from email.mime.text import MIMEText
import smtplib
import re


def crop_black_borders(img):
    bg = Image.new(img.mode, img.size, (0, 0, 0))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()

    if bbox:
        return img.crop(bbox)

    return img

def envoyer_email(
    nom,
    prenom,
    email_client,
    panier,
    total
):

    contenu = f"""
Nouvelle demande inventaire

Nom : {nom}
Prénom : {prenom}
Email : {email_client}

Objets demandés :
"""
    for item in panier:
        contenu += f"""
- {item['objet']} ({item['prix']} €)
"""
    contenu += f"""
TOTAL : {total:.2f} €
"""
    msg = MIMEText(contenu)
    msg["Subject"] = "Nouvelle demande inventaire"
    msg["From"] = "hernandez.thibaut31@gmail.com"
    msg["To"] = "hernandez.thibaut31@gmail.com"
    serveur = smtplib.SMTP(
        "smtp.gmail.com",
        587
    )
    serveur.starttls()
    serveur.login(
        st.secrets["EMAIL"],
        st.secrets["PASSWORD"]
    )
    serveur.send_message(msg)
    serveur.quit()




if "panier" not in st.session_state:
    st.session_state.panier = []

@st.dialog("🛒 Mon panier")
def show_cart():

    panier = st.session_state.panier

    if not panier:
        st.info("Panier vide")
        return
    total = 0
    for item in panier:
        if item["prix"] == '-':
            prix = 0
        else:
            prix = float(item["prix"])
        total += prix
        total += prix
        with st.container(border=True):

            col1, col2 = st.columns([1, 3])

            with col1:

                if item["image"]:
                    st.image(
                        item["image"],
                        use_container_width=True
                    )

            with col2:

                st.subheader(item["objet"])

                st.write(f"Prix : {item['prix']} €")
                st.write(f"Catégorie : {item['categorie']}")

                if st.button(
                    "❌ Retirer",
                    key=f"remove_{item['objet']}"
                ):
                    st.session_state.panier.remove(item)
                    st.rerun()
    
    st.subheader(f"💰 Total : {total:.2f} €")
    nom = st.text_input("Nom")

    prenom = st.text_input("Prénom")

    email = st.text_input("Email")

    if st.button("📧 Envoyer la demande"):
        if nom and prenom and email:
            envoyer_email(
                nom,
                prenom,
                email,
                panier,
                total
            )
            st.success(
                "Demande envoyée ✅"
            )
        else:
            st.warning(
                "Merci de remplir les champs"
            )
@st.cache_data
def load_image(path):

    img = Image.open(path)

    img.thumbnail((1200, 1200))

    return img

@st.dialog("Galerie photos")
def show_gallery(image_paths, objet):

    st.subheader(objet)

    for img in image_paths:
        im = load_image(img)
        im = ImageOps.exif_transpose(im)
        im = crop_black_borders(im)
        im.thumbnail((800, 800))
        st.image(
            im,
            use_container_width=True
        )

@st.cache_data
def get_all_photos():

    return os.listdir("Photos")

st.set_page_config(
    page_title="Inventaire Clara & Thib",
    layout="wide"
)

st.title("📦 Inventaire Clara et Thibaut")
top1, top2 = st.columns([10, 1])

with top2:

    if st.button(
        f"🛒 {len(st.session_state.panier)}",
        use_container_width=True
    ):
        show_cart()

SHEET_ID = "1KB6DaRcND6WbAwIRg45SF63uHtJRYt9f"
GID = "1016625712"

url = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=csv&gid={GID}"
)

@st.cache_data(ttl=300)
def load_data():

    return pd.read_csv(url)

df = load_data()
# df = pd.read_csv("Inventaire.csv")

st.sidebar.header("Filtres")
categories = ["Toutes"] + sorted(df["Catégorie"].dropna().unique().tolist())
categorie_selection = st.sidebar.selectbox(
    "Catégorie",categories
)

dispo_selection = st.sidebar.selectbox(
    "Disponibilité",["Toutes", "Réservé", "Dispo"]
)
recherche = st.sidebar.text_input(
    "Rechercher un objet"
)

df_filtre = df.copy()
df_filtre["Dispo"] = df_filtre["Dispo"].fillna("Dispo")


if categorie_selection != "Toutes":
    df_filtre = df_filtre[df_filtre["Catégorie"] == categorie_selection]
if dispo_selection != "Toutes":
    df_filtre = df_filtre[df_filtre["Dispo"] == dispo_selection]
if recherche:
    df_filtre = df_filtre[df_filtre["Objet"].str.contains(recherche, case=False, na=False)]

df_filtre = df_filtre[df_filtre["Dispo"] != 'Réservé']

df_filtre = df_filtre.fillna('-')
def has_photo(objet):
    objet = str(objet).strip().lower()

    for fichier in all_photos:
        nom = os.path.splitext(fichier)[0].lower()

        if nom.startswith(objet):
            return True

    return False

all_photos = get_all_photos()
df_filtre["has_photo"] = df_filtre["Objet"].apply(has_photo)
df_filtre = df_filtre.sort_values(
    by=["has_photo"],
    ascending=False
)

cards = st.columns(3)  # 2 objets par ligne
for index, (_, row) in enumerate(df_filtre.iterrows()):

    with cards[index % 3]:
        with st.container(border=True):

            col1, col2= st.columns([2,2])

            with col1:
                objet = str(row["Objet"]).strip().lower()

                image_paths = []

                for fichier in all_photos:

                    nom = os.path.splitext(fichier)[0].lower()

                    if nom.startswith(objet):

                        image_paths.append(
                            os.path.join("Photos", fichier)
                        )

                image_paths.sort()
                if image_paths:
                    img = load_image(image_paths[0])
                    img = ImageOps.exif_transpose(img)
                    img = crop_black_borders(img)
                    img.thumbnail((800, 800))
                    st.image(
                        img,
                        use_container_width=True
                    )
                    if st.button(
                        "Voir les photos",
                        key=f"btn_{index}"
                    ):
                        show_gallery(
                            image_paths,
                            row["Objet"]
                        )
                else:
                    st.warning("Photos introuvables")
            with col2:
                
                st.markdown(
                    f"""
                    <div style="height:450px; overflow:hidden;">
                    
                    <h4>{row['Objet']}</h4>

                    <p><b>Description :</b> {row['Description']}</p>

                    <p><b>Etat :</b> {row['Etat']}</p>

                    <p><b>Dimensions :</b> {row['Dimensions']}</p>

                    <p><b>Prix :</b> {row['Prix']} €</p>

                    <p><b>Catégorie :</b> {row['Catégorie']}</p>

                    <p><b>Disponible :</b> {row['Dispo']}</p>

                    </div>
                    """,
                    unsafe_allow_html=True
                )
           
            if st.button(
                "🛒",
                key=f"cart_{index}",
                help="Ajouter au panier"
            ):

                first_image = image_paths[0] if image_paths else None

                produit = {
                    "objet": row["Objet"],
                    "prix": row["Prix"],
                    "categorie": row["Catégorie"],
                    "image": first_image
                }

                # éviter doublons
                if produit not in st.session_state.panier:

                    st.session_state.panier.append(
                        produit
                    )

                    st.toast(
                        f"{row['Objet']} ajouté au panier"
                    )
        st.divider()

