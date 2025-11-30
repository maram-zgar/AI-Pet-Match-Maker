import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sentence_transformers import SentenceTransformer
import warnings

# Supprimer l'avertissement de FutureWarning de scikit-learn
warnings.filterwarnings("ignore", category=FutureWarning)

# --- Configuration du Modèle NLP ---
# Charger le modèle NLP une seule fois au démarrage
try:
    print("Chargement du modèle SentenceTransformer (all-MiniLM-L6-v2)...")
    # Utiliser un modèle léger et rapide pour l'encodage
    NLP_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    VECTOR_DIMENSION = 384
    print("Modèle NLP chargé.")
except Exception as e:
    print(f"Erreur lors du chargement de SentenceTransformer : {e}")
    NLP_MODEL = None
    VECTOR_DIMENSION = 384 # Dimension par défaut si le modèle échoue

def get_vector(text):
    """Convertit un texte en un vecteur d'embedding."""
    if NLP_MODEL:
        # Encoder le texte en utilisant le modèle chargé
        return NLP_MODEL.encode(text)
    else:
        # Retourne un vecteur aléatoire si le modèle n'a pas pu charger (pour les tests uniquement)
        print("ATTENTION: Utilisation d'un vecteur aléatoire (NLP non chargé).")
        return np.random.rand(VECTOR_DIMENSION)

class AnimalMatcher:
    def __init__(self, csv_path="data/animals.csv", n_neighbors=5):
        """Initialise le matcher d'animaux avec KNN."""
        self.df = pd.read_csv(csv_path)
        self.df.columns = self.df.columns.str.lower()
        self.n_neighbors = n_neighbors
        self.knn_model = None
        self.animal_vectors = None

        NOM_COLONNE_IMAGE_DANS_CSV = 'image_url' # <--- MODIFIEZ CECI !
        NOM_COLONNE_DESCRIPTION_DANS_CSV = 'personality_description' # Déjà utilisé

        if NOM_COLONNE_IMAGE_DANS_CSV in self.df.columns:
            # Renomme la colonne de l'image en 'img_url' pour correspondre au HTML
            self.df = self.df.rename(columns={NOM_COLONNE_IMAGE_DANS_CSV: 'img_url'})
            print(f"La colonne '{NOM_COLONNE_IMAGE_DANS_CSV}' a été renommée en 'img_url'.")
        else:
             print(f"⚠️ AVERTISSEMENT : La colonne '{NOM_COLONNE_IMAGE_DANS_CSV}' est introuvable. Les images ne s'afficheront pas.")
        
        # Vérification de la colonne de description avant l'utilisation
        if NOM_COLONNE_DESCRIPTION_DANS_CSV not in self.df.columns:
             raise ValueError(f"Colonne essentielle '{NOM_COLONNE_DESCRIPTION_DANS_CSV}' manquante pour le matching.")
        
        
    def prepare_embeddings(self):
        """Convertit toutes les descriptions de personnalité des animaux en vecteurs."""
        print("Conversion des descriptions en embeddings...")
        self.animal_vectors = np.array([
            get_vector(desc) for desc in self.df['personality_description']
        ])
        print(f"✓ Création des embeddings pour {len(self.animal_vectors)} animaux terminée.")
        
    def train_knn(self):
        """Entraîne le modèle KNN sur les embeddings d'animaux."""
        if self.animal_vectors is None:
            self.prepare_embeddings()
            
        print("Entraînement du modèle KNN...")
        self.knn_model = NearestNeighbors(
            n_neighbors=self.n_neighbors,
            metric='cosine',  # La métrique Cosine est excellente pour les embeddings de texte
            algorithm='brute'
        )
        self.knn_model.fit(self.animal_vectors)
        print("✓ Modèle KNN entraîné.")
        
    def create_user_profile(self, answers):
        """
        Crée une description en langage naturel des préférences de l'utilisateur
        à partir des réponses du chatbot.
        """
        profile_parts = []
        
        # Mappage pour l'énergie
        if 'energy_preference' in answers:
            energy_map = {
                'high': 'un animal très énergique et actif qui adore jouer et se dépenser',
                'medium': 'un animal modérément actif avec une énergie équilibrée',
                'low': 'un animal calme et relaxé qui apprécie les moments de tranquillité'
            }
            profile_parts.append(f"Je recherche {energy_map.get(answers['energy_preference'], 'un animal')}.")
        
        # Mappage pour l'amitié
        if 'friendliness_preference' in answers:
            friend_map = {
                'high': 'extrêmement affectueux et aime tout le monde',
                'medium': 'amical mais pas trop pot de colle',
                'low': 'indépendant et réservé, pas toujours à la recherche d\'attention'
            }
            profile_parts.append(f"Cet animal doit être {friend_map.get(answers['friendliness_preference'], 'amical')}.")
        
        # Mappage pour l'âge
        if 'age_preference' in answers:
            age_map = {
                'young': 'Je préfère un animal jeune et joueur',
                'adult': 'Je préfère un animal adulte avec une personnalité bien établie',
                'senior': 'Je préfère un animal senior au tempérament très calme'
            }
            profile_parts.append(age_map.get(answers['age_preference'], ''))
            
        # Mappage pour le type d'habitat
        if 'home_type' in answers:
            home_map = {
                'apartment': 'approprié pour la vie en appartement',
                'house_yard': 'qui aime avoir un jardin pour courir',
                'active': 'qui convient à un foyer très actif et mouvementé',
                'quiet': 'qui s\'adapte à un foyer calme et paisible'
            }
            profile_parts.append(f"L'animal devrait être {home_map.get(answers['home_type'], '')}.")
            
        # Mappage pour l'expérience
        if 'experience' in answers:
            exp_map = {
                'first_time': 'Je suis un primo-adoptant',
                'experienced': 'Je suis un adoptant expérimenté'
            }
            profile_parts.append(exp_map.get(answers['experience'], ''))
            
        # Préférence d'espèce (filtrage simple)
        if 'species_preference' in answers and answers['species_preference'] != 'no preference':
            profile_parts.append(f"Mon choix se porte sur l'espèce : {answers['species_preference'].lower()}.")

        # Enfants
        if 'children' in answers and answers['children']:
            profile_parts.append("L'animal doit être à l'aise avec les enfants.")
        
        # Joindre toutes les parties en une description cohérente
        user_profile = ' '.join(filter(None, profile_parts))
        return user_profile
    
    def find_matches(self, user_answers):
        """
        Trouve les animaux les plus compatibles basés sur les préférences de l'utilisateur.
        
        Args:
            user_answers: Dictionnaire des réponses de l'utilisateur.
            
        Returns:
            DataFrame avec les animaux les plus compatibles et leur score de matching.
        """
        if self.knn_model is None:
            # Re-entraînement si nécessaire, bien que nous le fassions au démarrage dans app.py
            self.train_knn()
        
        # 1. Créer le profil utilisateur
        user_profile = self.create_user_profile(user_answers)
        print(f"\nProfil Utilisateur Généré: {user_profile}\n")
        
        # 2. Filtrage simple (Espèce)
        filtered_df = self.df.copy()
        
        species_pref = user_answers.get('species_preference')
        if species_pref and species_pref != 'no preference':
            filtered_df = filtered_df[filtered_df['species'].str.lower() == species_pref.lower()]

        # Si le filtrage ne laisse plus d'animaux, retourner un DF vide
        if filtered_df.empty:
             # Si aucun match après le filtre strict, retourner les 5 meilleurs chiens/chats par défaut
             fallback_df = self.df[self.df['species'].isin(['Dog', 'Cat'])].head(self.n_neighbors).copy()
             fallback_df['match_score'] = 0
             return fallback_df 
        
        # 3. Trouver les embeddings correspondants dans le DF filtré
        filtered_indices = filtered_df.index.tolist()
        filtered_vectors = self.animal_vectors[filtered_indices]

        # 4. Entraîner un KNN temporaire sur le sous-ensemble filtré
        temp_knn = NearestNeighbors(n_neighbors=min(self.n_neighbors, len(filtered_vectors)), metric='cosine', algorithm='brute')
        temp_knn.fit(filtered_vectors)

        # 5. Convertir le profil utilisateur en vecteur
        user_vector = get_vector(user_profile).reshape(1, -1)
        
        # 6. Trouver les voisins les plus proches dans le sous-ensemble filtré
        distances, indices = temp_knn.kneighbors(user_vector)
        
        # 7. Mapper les indices retournés à l'index original du DataFrame
        original_indices = [filtered_indices[i] for i in indices[0]]
        
        # 8. Récupérer les animaux matchés
        matches = self.df.loc[original_indices].copy()
        
        # 9. Calculer le score de similarité
        matches['match_score'] = 1 - distances[0]
        matches['match_score'] = (matches['match_score'] * 100).round(3)
        
        # Optionnel: Classer par score (bien que KNN le fasse par défaut)
        matches = matches.sort_values(by='match_score', ascending=False)
        
        return matches
