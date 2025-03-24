from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os
import requests
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle

app = Flask(__name__)
app.secret_key = "votre_clé_secrète"

# Configuration de la base de données
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['DOCUMENT_FOLDER'] = 'statics/documents/'

# Création du dossier de documents s'il n'existe pas
os.makedirs(app.config['DOCUMENT_FOLDER'], exist_ok=True)

app.config['SQLALCHEMY_BINDS'] = {
    'incidents': 'sqlite:///incidents.db'
}

db = SQLAlchemy(app)

# Configuration de Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Modèle utilisateur
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    role = db.Column(db.String(50), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

    # Dictionnaire des recommandations par type d'incident


recommendations = {
    "Compteur brûlé": [
        "Nouveau compteur - Type: Monophasé / Triphasé, conforme aux normes de distribution électrique",
        "Câbles électriques - Section: 6mm², 10mm², résistants à la chaleur et aux surtensions",
        "Tournevis isolé - Norme IEC 60900, avec poignée ergonomique",
        "Gants isolants haute tension - Classe 2 (jusqu'à 17 000V)",
        "Multimètre numérique - Pour vérifier la tension et le courant avant l'installation"
    ],
    "Poteau tombé": [
        "Poteau en béton - Hauteur: 9m ou 12m, avec traitement hydrofuge",
        "Grue hydraulique - Capacité 10T, adaptée au levage en zone difficile",
        "Câbles de soutien - Résistance à la traction 5000N, avec attaches en acier inoxydable",
        "Écarteurs de câbles - Pour maintenir les lignes en sécurité pendant l’intervention",
        "Kit de scellement rapide - Pour assurer la fixation du poteau dans le sol"
    ],
    "Câble endommagé": [
        "Câble de remplacement - Section adaptée aux charges électriques du réseau",
        "Pinces coupantes - Résistance jusqu'à 1000V, avec isolant en caoutchouc",
        "Isolants thermorétractables - Norme NF EN 50321, pour protéger les connexions",
        "Connecteurs de câbles - À compression, pour une meilleure conductivité",
        "Ruban isolant haute tension - Protection contre les courts-circuits"
    ],
    "Oiseau sur les lignes": [
        "Éloigneur d'oiseaux - Effaroucheur acoustique programmable",
        "Gants isolés - Testés jusqu'à 1000V pour manipulation sécurisée",
        "Perche isolée télescopique - Pour dégager les oiseaux sans contact direct",
        "Système de protection anti-perchoir - Pour éviter les installations futures"
    ],
    "Isolateur cassé": [
        "Isolateur de remplacement - Porcelaine ou polymère haute résistance",
        "Tournevis isolé - Manche antidérapant, norme CEI 60900",
        "Clef dynamométrique - Pour assurer un serrage optimal des fixations",
        "Graisse diélectrique - Pour éviter l’oxydation des connexions"
    ],
    "Arbre sur les lignes": [
        "Tronçonneuse thermique - Puissance 2200W, avec guide-chaîne de sécurité",
        "Gants anti-coupure - Protection classe 3, pour éviter les blessures",
        "Équipement de sécurité - Casque avec visière, harnais et chaussures renforcées",
        "Sangles de retenue - Pour contrôler la chute des branches coupées",
        "Véhicule nacelle - Pour accéder aux branches en hauteur"
    ]
}


# Exemple de liste d'actions correctives par type d'incident
corrective_actions = {
    "Compteur brûlé": [
        "Remplacer le compteur endommagé avec un modèle homologué",
        "Vérifier l’intégrité des câbles pour détecter toute coupure ou surchauffe",
        "Assurer un serrage correct des bornes pour éviter les faux contacts",
        "Tester l’installation après remplacement pour confirmer le bon fonctionnement"
    ],
    "Poteau tombé": [
        "Sécuriser la zone avec un périmètre de sécurité",
        "Déposer les câbles avant le relevage du poteau",
        "Remplacer le poteau endommagé et stabiliser la base avec du béton renforcé",
        "Reconnecter les câbles en respectant les normes de tension"
    ],
    "Câble endommagé": [
        "Remplacer le câble endommagé avec un câble de même section et isolation",
        "Effectuer des soudures ou des connexions étanches si nécessaire",
        "Inspecter l’ensemble du tronçon pour repérer d’autres faiblesses",
        "Tester la tension après l’intervention pour garantir la continuité du réseau"
    ],
    "Oiseau sur les lignes": [
        "Dégager l’oiseau avec une perche isolée pour éviter tout risque de choc électrique",
        "Installer des effaroucheurs ou des dispositifs anti-perchoir",
        "Informer les autorités environnementales en cas d’espèce protégée"
    ],
    "Isolateur cassé": [
        "Remplacer l’isolateur avec un modèle neuf adapté au type de ligne",
        "Vérifier l’absence de fissures sur les autres isolateurs du même support",
        "Serrer les fixations et appliquer une graisse isolante"
    ],
    "Arbre sur les lignes": [
        "Évaluer les risques avant toute intervention",
        "Couper les branches menaçantes tout en assurant la stabilité des câbles",
        "Vérifier l’intégrité des conducteurs après dégagement",
        "Programmer un entretien régulier des arbres proches des lignes"
    ]
}

# Exemple de mesures de sécurité par type d'incident
safety_measures = {
    "Compteur brûlé": [
        "Porter des gants isolants de classe 2",
        "S'assurer que la ligne est hors tension avant toute manipulation",
        "Utiliser des outils isolés pour toute connexion électrique",
        "Mettre en place des panneaux de signalisation pour éviter les intrusions"
    ],
    "Poteau tombé": [
        "Porter des gants de protection et un harnais de sécurité",
        "Délimiter un périmètre de sécurité autour du poteau",
        "Éviter tout contact direct avec les câbles sous tension",
        "Utiliser une nacelle pour les travaux en hauteur"
    ],
    "Câble endommagé": [
        "Déconnecter l’alimentation avant toute intervention",
        "Utiliser des outils isolés et des équipements de protection individuelle (EPI)",
        "Ne pas travailler sous conditions météorologiques dangereuses",
        "Effectuer une vérification visuelle des autres câbles avant de quitter les lieux"
    ],
    "Oiseau sur les lignes": [
        "Éviter tout contact direct avec la ligne électrique",
        "Utiliser une perche isolée pour retirer l’animal en toute sécurité",
        "Ne pas tenter d’intervenir sans équipements adéquats",
        "Informer les services environnementaux si nécessaire"
    ],
    "Isolateur cassé": [
        "Vérifier que la ligne est hors tension avant toute manipulation",
        "Utiliser des gants isolants et des outils adaptés",
        "S’assurer que l’isolateur est correctement fixé après remplacement",
        "Effectuer un contrôle visuel des autres isolateurs du même support"
    ],
    "Arbre sur les lignes": [
        "Porter des équipements de sécurité complets (casque, gants, lunettes de protection)",
        "Ne pas couper d’arbres ou de branches sans analyse préalable des risques",
        "Travailler avec un binôme pour plus de sécurité",
        "Assurer un suivi après intervention pour éviter d'autres incidents"
    ]
}


from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
import os


def generate_pdf(incident_id, lieu, nom_client, date, description, conditions, incident_type, recommendations,
                 corrective_actions, safety_measures):
    pdf_path = os.path.join(app.config['DOCUMENT_FOLDER'], f"incident_{incident_id}.pdf")

    # Création du document PDF
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    elements = []

    # Définition des styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    bold_style = styles['Heading2']
    normal_style = styles['Normal']

    # Ajout du logo de l'ONEE
    logo_path = os.path.join(app.static_folder, 'images', 'onee logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=120, height=60)
        elements.append(logo)

    # Titre du rapport
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Rapport d'Incident - ID: {incident_id}", title_style))
    elements.append(Spacer(1, 20))

    # Informations générales bien espacées
    elements.append(Paragraph("<b>Informations Générales</b>", bold_style))
    elements.append(Spacer(1, 10))

    general_info = [
        ["Lieu :", lieu],
        ["Nom du Client :", nom_client],
        ["Date :", date],
        ["Description :", description],
        ["Conditions :", conditions],
        ["Type d'Incident :", incident_type]
    ]

    table_general = Table(general_info, colWidths=[140, 350])
    table_general.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.white)
    ]))
    elements.append(table_general)
    elements.append(Spacer(1, 20))

    # Fonction pour créer des tableaux clairs et lisibles
    def create_styled_table(data, title, bg_color):
        elements.append(Paragraph(f"<b>{title}</b>", bold_style))
        elements.append(Spacer(1, 5))

        table_data = [[title]] + [[item] for item in data]

        table = Table(table_data, colWidths=[450])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), bg_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica')
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

    # Ajout des tableaux
    create_styled_table(recommendations, "Matériel Recommandé", colors.gray)
    create_styled_table(corrective_actions, "Actions Correctives", colors.gray)
    create_styled_table(safety_measures, "Mesures de Sécurité", colors.gray)

    # Génération du PDF
    doc.build(elements)
    incident = Incident(
        id=incident_id,
        lieu=lieu,
        nom_client=nom_client,
        date=datetime.strptime(date, '%Y-%m-%d'),
        description=description,
        incident_type=incident_type,
        pdf_report=f"incident_{incident_id}.pdf",
        status="Non réparé"  # Statut par défaut
    )

    db.session.add(incident)
    db.session.commit()
    return pdf_path


# Fonction pour appeler l'API de prédiction
def predict_incident_with_api(image_path):
    api_url = 'https://61a2-35-185-121-112.ngrok-free.app/predict'
    with open(image_path, 'rb') as file:
        files = {'file': (os.path.basename(image_path), file, 'image/jpeg')}
        response = requests.post(api_url, files=files)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Erreur API : {response.status_code} - {response.text}")

@app.route('/add-incident', methods=['GET', 'POST'])
@login_required
def add_incident():
    if request.method == 'POST':
        incident_id = request.form.get('incident_id')
        lieu = request.form.get('lieu')
        nom_client = request.form.get('nom_client')
        date = request.form.get('date')
        description = request.form.get('description')
        conditions = request.form.get('conditions')
        photos = request.files.getlist('photos')

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        incident_type = None
        confidence = None
        for photo in photos:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)

            try:
                api_response = predict_incident_with_api(photo_path)
                incident_type = api_response['prediction']
                confidence = api_response['confidence']
            except Exception as e:
                flash(f"Erreur de prédiction : {e}", "error")
                return redirect(url_for('add_incident'))

        recommendations_list = recommendations.get(incident_type, [])
        corrective_list = corrective_actions.get(incident_type, [])
        safety_list = safety_measures.get(incident_type, [])

        document_path = generate_pdf(incident_id, lieu, nom_client, date, description, conditions, incident_type, recommendations_list, corrective_list, safety_list)

        return render_template('incident.html', incident_id=incident_id, lieu=lieu, nom_client=nom_client, date=date, description=description, conditions=conditions, prediction=incident_type, confidence=confidence, recommendations=recommendations_list)

    return render_template('incident.html')

@app.route('/download-report/<incident_id>')
@login_required
def download_report(incident_id):
    file_path = os.path.join(app.config['DOCUMENT_FOLDER'], f"incident_{incident_id}.pdf")

    if not os.path.exists(file_path):
        return "Le rapport n'existe pas!", 404

    return send_file(file_path, as_attachment=True)
from flask import Flask, render_template, request, url_for, send_from_directory
from flask_login import login_required
import os




# Route pour afficher l'historique des incidents
@app.route('/incident-history', methods=['GET', 'POST'])
@login_required
def incident_history():
    pdf_path = None
    error = None

    if request.method == 'POST':
        incident_id = request.form.get('incident_id')

        if incident_id:
            # Chemin du PDF
            pdf_filename = f"{incident_id}.pdf"
            pdf_folder = os.path.join('statics', 'documents')  # Dossier statics/documents
            full_path = os.path.join(pdf_folder, pdf_filename)

            if os.path.exists(full_path):
                # Créer le chemin pour afficher le PDF
                pdf_path = f"/statics/documents/{pdf_filename}"
            else:
                error = "Aucun rapport trouvé avec cet ID."

    return render_template('historique.html', pdf_path=pdf_path, error=error)

# Route pour accéder aux fichiers PDF dans statics/documents
@app.route('/statics/documents/<path:filename>')
def get_pdf(filename):
    return send_from_directory('statics/documents', filename)
import PyPDF2
from flask import Flask, render_template, session
from flask_login import login_required
import matplotlib.pyplot as plt
import io
import base64


# Route pour afficher les statistiques
@app.route('/stats', methods=['GET'])
@login_required
def stats():
    # Le chemin vers le dossier où sont stockés les fichiers PDF
    folder_path = 'statics/documents'

    # Types d'incidents attendus
    types_incidents = {
        'Oiseau sur les lignes': 0,
        'Poteau tombé': 0,
        'Arbre sur les lignes': 0,
        'Compteur brûlé': 0,
        'Isolateur cassé': 0,
        'Câble endommagé': 0
    }

    # Parcourir les fichiers PDF dans le dossier
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(folder_path, filename)

            # Lire le fichier PDF et extraire le texte
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""

            # Extraire le type d'incident
            incident_type = extract_incident_type(text)
            if incident_type in types_incidents:
                types_incidents[incident_type] += 1

    # Générer un graphique des incidents par type
    labels = list(types_incidents.keys())
    counts = list(types_incidents.values())

    # Créer un graphique avec Matplotlib
    fig, ax = plt.subplots()
    ax.bar(labels, counts, color='blue')
    ax.set_title('Répartition des incidents par type')
    ax.set_xlabel('Type d\'incident')
    ax.set_ylabel('Nombre d\'incidents')
    plt.xticks(rotation=45)

    # Sauvegarder le graphique dans un format image pour l'affichage dans le template
    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')

    # Rendre la page avec le graphique
    return render_template('stats.html', img_base64=img_base64, types_incidents=types_incidents)


def extract_incident_type(text):
    """
    Fonction pour extraire le type d'incident à partir du texte extrait du fichier PDF.
    """
    known_types = [
        'Oiseau sur les lignes', 'Poteau tombé', 'Arbre sur les lignes',
        'Compteur brûlé', 'Isolateur cassé', 'Câble endommagé'
    ]
    for incident_type in known_types:
        if incident_type in text:
            return incident_type
    return 'Inconnu'
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user  # L'utilisateur actuel est récupéré via Flask-Login

    if request.method == 'POST':
        # Traitement de l'upload de l'image de profil
        file = request.files['profile_image']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Mise à jour de l'image de profil de l'utilisateur dans la base de données
            user.profile_image = url_for('static', filename=f'uploads/{filename}')
            # Sauvegardez les modifications dans la base de données
            # db.session.commit() # Si vous utilisez SQLAlchemy par exemple

    # Rendu de la page avec l'utilisateur actuel
    return render_template("profile.html", user=user)
# Routes existantes (login, register, dashboard, etc.)
@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            flash("Connexion réussie !", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        phone = request.form.get("phone")
        role = request.form.get("role")

        if User.query.filter_by(email=email).first():
            flash("Cet email est déjà utilisé.", "error")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur est déjà utilisé.", "error")
            return redirect(url_for("register"))

        user = User(
            username=username,
            email=email,
            password=password,
            phone=phone,
            role=role
        )
        db.session.add(user)
        db.session.commit()

        flash("Inscription réussie ! Vous pouvez maintenant vous connecter.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


from datetime import datetime


class Incident(db.Model):
    __bind_key__ = 'incidents'
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    lieu = db.Column(db.String(100), nullable=False)
    nom_client = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.String(500), nullable=False)
    incident_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='Non réparé')
    repaired_by = db.Column(db.String(100), nullable=True)
    repaired_date = db.Column(db.DateTime, nullable=True)
    pdf_report = db.Column(db.String(255), nullable=True)


# Route pour le dashboard - Version corrigée
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    # Récupère tous les incidents triés par date
    incidents = Incident.query.order_by(Incident.date.desc()).all()

    # Debug: Affiche les incidents et leurs rapports
    print("Incidents dans la base:")
    for inc in incidents:
        pdf_exists = os.path.exists(os.path.join(app.config['DOCUMENT_FOLDER'], inc.pdf_report)) if inc.pdf_report else 'N/A'
        print(f"ID: {inc.id}, PDF: {inc.pdf_report}, Existe: {pdf_exists}")

    pdf_path = None
    error = None

    if request.method == 'POST':
        incident_id = request.form.get('incident_id')
        if incident_id:
            incident = Incident.query.get(incident_id)
            if incident:
                if incident.pdf_report:
                    # Construction du chemin correct
                    pdf_path = f"/statics/documents/{incident.pdf_report}"

                    # Vérification que le fichier existe
                    if not os.path.exists(os.path.join(app.config['DOCUMENT_FOLDER'], incident.pdf_report)):
                        error = "Le fichier PDF existe dans la base mais pas sur le disque"
                else:
                    error = "Cet incident n'a pas de rapport PDF associé"
            else:
                error = "Aucun incident trouvé avec cet ID"

    return render_template('dashboard.html',
                         incidents=incidents,
                         pdf_path=pdf_path,
                         error=error)


# Route pour marquer comme réparé - Version corrigée
@app.route('/mark-repaired/<int:incident_id>', methods=['POST'])
@login_required
def mark_repaired(incident_id):
    incident = Incident.query.get_or_404(incident_id)

    # Mise à jour de l'incident
    incident.status = "Réparé"
    incident.repaired_by = current_user.username
    incident.repaired_date = datetime.utcnow()

    try:
        db.session.commit()
        flash("Incident marqué comme réparé avec succès!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la mise à jour: {str(e)}", "error")

    return redirect(url_for('dashboard'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# Point d'entrée de l'application
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Créer les tables de la base de données
    app.run(debug=True)