# Gestion des Incidents Basse Tension 🚧⚡
Une application web permettant de gérer les incidents basse tension, d'améliorer l'entretien du réseau électrique, et de générer des rapports d'incidents à partir d'images.

## 📌 Fonctionnalités principales
Suivi des incidents : Surveillance en temps réel des incidents déclarés.

Déclaration des incidents : Ajout de nouveaux incidents avec génération automatique de rapports.

Historique : Accès aux rapports des incidents passés.

Statistiques : Vue d'ensemble des incidents pour une meilleure analyse.

## 📸 Aperçu de l'application

Voici quelques captures d'écran de l'application :

### 📝 Génération des rapports d'incidents
![Génération des rapports d'incidents](static/images/generation%20des%20rapports%20d'incidents.png)

### 🔍 Suivi des incidents et état de réparation
![Suivi des incidents](static/images/suivi%20d'incident.png)

## 🏗️ Technologies utilisées

Backend : Flask, Flask-Login, SQLAlchemy

Frontend : HTML, CSS

Base de données : SQLite 

Modèles IA : CLIP (classification d'images), CNN (détection d'incidents)

Déploiement API : Flask + ngrok

## 🤖 Intelligence Artificielle

🔹 Classification avec CLIP
Le modèle CLIP d'OpenAI est utilisé pour classer les images d'incidents en différentes catégories :

Compteur brûlé

Poteau tombé

Câble endommagé

Oiseau sur les lignes

Isolateur cassé

Arbre sur les lignes

Le script analyse les images et stocke les résultats dans un fichier CSV, permettant d'associer chaque image à une classe prédite.

🔹 Détection avec un modèle CNN
Un réseau de neurones convolutionnel (CNN) a été entraîné sur 9481 images d'incidents pour améliorer la détection automatique et donne un precision de 93.30%.
Il utilise Keras avec un Early Stopping pour éviter le sur-ajustement,Le modèle est sauvegardé sous le nom mode_onee_final.ipynb et déployé via une API Flask exposée avec ngrok.
 Installation et exécution
1️⃣ Cloner le projet

git clone https://github.com/ihssane2002/Projet_onee.git
cd Projet_onee
2️⃣ Installer les dépendances

pip install -r requirements.txt

3️⃣ Lancer l'application

python main.py

L'application sera accessible à http://127.0.0.1:5000.
# 📝 Auteurs
Ihssane Bammad - Développeur principal
