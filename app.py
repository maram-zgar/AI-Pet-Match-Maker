from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import time
from matching import AnimalMatcher # Importe la classe du fichier matching.py

# --- Configuration et Initialisation ---
app = Flask(__name__)
# Une clé secrète est OBLIGATOIRE pour utiliser les sessions Flask
app.secret_key = os.environ.get('SECRET_KEY', 'votre_cle_secrete_ultra_sure_ici') 

# Initialisation du Matcher
MATCHER = None
try:
    # Initialisation de la classe AnimalMatcher et entraînement du modèle KNN
    MATCHER = AnimalMatcher(csv_path="data/animals.csv", n_neighbors=5)
    print("Préparation des embeddings et entraînement du KNN en cours...")
    MATCHER.train_knn()
    print("Système AnimalMatcher prêt.")
except FileNotFoundError:
    print("ERREUR: Le fichier 'data/animals.csv' est introuvable. Veuillez le créer et vérifier le chemin.")
except Exception as e:
    print(f"Erreur lors de l'initialisation de AnimalMatcher: {e}")


# --- Définition des Questions du Chatbot ---
# Note: L'ordre des questions est important pour la séquence de dialogue
CHAT_QUESTIONS = [
    {
        'key': 'species_preference',
        'ai_message': "Bonjour ! Je suis l'assistant Pet Match. Ensemble, nous allons trouver ton ami parfait ! Pour commencer, quel type d'animal souhaites-tu adopter ?",
        'options': [
            {'label': "Un Chien 🐕", 'value': 'Dog'},
            {'label': "Un Chat 🐈", 'value': 'Cat'},
            {'label': "Pas de préférence", 'value': 'no preference'}
        ]
    },
    {
        'key': 'energy_preference',
        'ai_message': "Super ! Maintenant, quelle est l'énergie que tu recherches chez ton compagnon ?",
        'options': [
            {'label': "Haute (très actif, joueur)", 'value': 'high'},
            {'label': "Moyenne (équilibré, balades régulières)", 'value': 'medium'},
            {'label': "Basse (calme, relax, siestes)", 'value': 'low'}
        ]
    },
    {
        'key': 'friendliness_preference',
        'ai_message': "Et quel niveau d'affection cherches-tu ? Préfères-tu un animal très proche ou plus indépendant ?",
        'options': [
            {'label': "Très affectueux (pot de colle)", 'value': 'high'},
            {'label': "Amical (indépendant mais gentil)", 'value': 'medium'},
            {'label': "Indépendant (réservé, solitaire)", 'value': 'low'}
        ]
    },
    {
        'key': 'age_preference',
        'ai_message': "Quel âge préfères-tu pour ton futur ami ? (L'âge influence souvent le niveau d'activité)",
        'options': [
            {'label': "Jeune (plus de travail mais très joueur)", 'value': 'young'},
            {'label': "Adulte (personnalité stable)", 'value': 'adult'},
            {'label': "Senior (tranquille et posé)", 'value': 'senior'}
        ]
    },
    {
        'key': 'home_type',
        'ai_message': "Quel est ton environnement de vie ? (Pour évaluer les besoins en espace)",
        'options': [
            {'label': "Appartement (milieu urbain)", 'value': 'apartment'},
            {'label': "Maison avec jardin", 'value': 'house_yard'},
            {'label': "Foyer très actif (beaucoup de visiteurs/mouvement)", 'value': 'active'},
            {'label': "Foyer très calme et paisible", 'value': 'quiet'}
        ]
    },
    {
        'key': 'experience',
        'ai_message': "Enfin, as-tu déjà eu des animaux de compagnie ?",
        'options': [
            {'label': "Oui, je suis expérimenté", 'value': 'experienced'},
            {'label': "Non, ce sera mon premier animal", 'value': 'first_time'}
        ]
    },
    {
        'key': 'children',
        'ai_message': "Y a-t-il des enfants (moins de 12 ans) dans ton foyer ?",
        'options': [
            {'label': "Oui", 'value': True},
            {'label': "Non", 'value': False}
        ]
    },
]


# --- Routes Flask ---

@app.route('/')
def home():
    """Route principale qui redirige vers le démarrage du chat."""
    session.clear()
    return render_template('index.html')

@app.route('/start-chat')
def start_chat():
    """Affiche la page du chatbot et initialise la session."""
    session['user_answers'] = {}
    session['current_step'] = 0
    return render_template('chatbot.html')


@app.route('/chat', methods=['POST'])
def chat():
    """Gère la logique de dialogue (question/réponse)."""
    
    if not MATCHER:
        # Erreur si le matcher n'a pas été initialisé (ex: fichier CSV manquant)
        return jsonify({'status': 'error', 'ai_message': "Le système de matching n'est pas prêt. Le fichier de données est peut-être manquant."}), 500

    data = request.get_json()
    user_answer = data.get('user_answer')
    q_key = data.get('current_question_key')
    
    # 1. Traiter la réponse précédente (sauf le premier appel d'initialisation)
    if q_key and user_answer is not None:
        # S'assurer que les réponses sont bien stockées comme le type attendu (booléen pour 'children')
        if q_key == 'children':
            session['user_answers'][q_key] = True if user_answer == 'True' else False
        elif q_key == 'energy_level':
             # Les niveaux sont des nombres, mais ici on utilise des chaînes ('high', 'medium', 'low')
             session['user_answers'][q_key] = user_answer
        else:
             session['user_answers'][q_key] = user_answer
             
        session['current_step'] += 1
        
    current_step = session.get('current_step', 0)
    
    # 2. Vérifier si toutes les questions ont été posées
    if current_step >= len(CHAT_QUESTIONS):
        # Toutes les réponses sont collectées -> Lancer le matching
        return jsonify({'status': 'match_found', 'redirect_url': '/waiting'})
        
    # 3. Poser la prochaine question
    else:
        next_question = CHAT_QUESTIONS[current_step]
        
        # Construire les données de réponse pour le JS
        response_data = {
            'status': 'continue',
            'ai_message': next_question['ai_message'],
            'next_question': {'key': next_question['key'], 'type': 'selection' if 'options' in next_question else 'text'},
            'options': next_question.get('options', [])
        }
        return jsonify(response_data)


@app.route('/waiting')
def waiting():
    """Affiche la page d'attente. La redirection vers /results est gérée par le JS de waiting.html."""
    return render_template('waiting.html')


@app.route('/results')
def results():
    """Affiche la page des résultats après le matching."""
    user_answers = session.get('user_answers')
    
    if not user_answers or not MATCHER:
        return redirect(url_for('home')) 
    
    try:
        # Lancer la fonction de matching
        matches_df = MATCHER.find_matches(user_answers)
        
        # Convertir les résultats en une liste de dictionnaires pour le template HTML
        matches = matches_df.to_dict('records')
        
        # Le premier match est le meilleur
        best_match = matches[0] if matches else None
        other_matches = matches[1:] if len(matches) > 1 else []
        
        # Stocker les résultats en session (utile pour pet-info)
        session['last_matches'] = matches
        
        return render_template('results.html', best_match=best_match, other_matches=other_matches)
        
    except Exception as e:
        app.logger.error(f"Erreur lors du matching: {e}")
        return render_template('error.html', message=f"Désolé, une erreur s'est produite lors de la recherche du match parfait : {e}"), 500



@app.route('/pet-info/<int:pet_id>')
def pet_info(pet_id):
    """Affiche les informations détaillées d'un animal spécifique."""
    if MATCHER and MATCHER.df is not None:
        try:
            # Récupérer la ligne correspondante à l'ID
            pet = MATCHER.df[MATCHER.df['id'] == pet_id].iloc[0].to_dict()
            return render_template('pet_info.html', pet=pet)
        except IndexError:
            return render_template('error.html', message="Animal non trouvé."), 404
    else:
        return redirect(url_for('home'))
        
# --- Démarrage de l'Application ---
if __name__ == '__main__':
    app.run(debug=True)
