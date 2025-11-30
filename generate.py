from faker import Faker
import random
import pandas as pd

fake = Faker()

def generate_animals(n=50):
    dog_breeds = ["Labrador", "Beagle", "Bulldog", "Poodle", "Shepherd", "Golden Retriever", "Husky", "Chihuahua"]
    cat_breeds = ["Persian", "Siamese", "Maine Coon", "Sphynx", "Bengal", "Ragdoll", "British Shorthair", "Tabby"]
    colors = ["black", "white", "brown", "grey", "gold", "mixed", "cream", "orange"]

    def rand_species(): 
        return random.choice(["Dog", "Cat"])
    
    def rand_age(): 
        return round(random.uniform(0.2, 15.0), 1)
    
    def rand_sex(): 
        return random.choice(["M", "F"])
    
    def rand_color(): 
        return random.choice(colors)
    
    def rand_date(): 
        return fake.date_between(start_date="-2y", end_date="today").isoformat()

    def rand_weight(species):
        if species == "Dog":
            return round(random.uniform(3.0, 45.0), 2)
        else:  # Cat
            return round(random.uniform(2.0, 8.0), 2)

    def generate_personality_profile(species, breed, age, sex):
        """Generate rich, detailed personality description for NLP embeddings"""
        
        # Energy descriptors
        energy_descriptors = {
            "high": ["very energetic", "loves to run and play", "always on the move", "needs lots of exercise", 
                    "bounces with excitement", "thrives on activity"],
            "medium": ["moderately active", "enjoys regular playtime", "balanced energy", "playful but not hyperactive",
                      "likes both play and rest"],
            "low": ["calm and relaxed", "prefers lounging", "gentle and peaceful", "enjoys quiet time",
                   "mellowed with age", "sedentary lifestyle"]
        }
        
        # Friendliness descriptors
        friendliness_descriptors = {
            "high": ["extremely affectionate", "loves everyone they meet", "craves human attention", 
                    "tail wags constantly", "seeks out cuddles", "very sociable", "great with families"],
            "medium": ["friendly but selective", "warms up after introduction", "moderately social",
                      "affectionate with trusted people", "balanced temperament"],
            "low": ["independent spirit", "prefers solitude", "takes time to trust", "reserved personality",
                   "selective with affection", "needs patient owner"]
        }
        
        # Special traits based on species
        dog_traits = [
            "loves fetch and outdoor games", "excellent walking companion", "enjoys car rides",
            "responds well to training", "protective of family", "good with children",
            "needs mental stimulation", "loves treats and food puzzles", "barks to communicate",
            "enjoys dog parks and socializing", "loyal companion", "needs daily exercise"
        ]
        
        cat_traits = [
            "enjoys climbing and perching high", "loves to chase toys", "purrs when content",
            "independent but loving", "enjoys window watching", "playful with laser pointers",
            "uses scratching post regularly", "curious about everything", "loves cozy spots",
            "gentle with children", "enjoys quiet environments", "grooms meticulously"
        ]
        
        # Age-based traits
        if age < 2:
            age_traits = ["young and still learning", "puppy/kitten energy", "needs training and guidance",
                         "very playful", "teething phase", "exploring the world"]
        elif age < 7:
            age_traits = ["in their prime", "fully grown", "established personality", "mature behavior",
                         "settled into routines"]
        else:
            age_traits = ["senior with wisdom", "calmer with age", "set in their ways", "mature companion",
                         "gentle soul", "experienced pet"]
        
        # Generate random characteristics
        energy_level = random.choice(["high", "medium", "low"])
        friendliness_level = random.choice(["high", "medium", "low"])
        
        energy_desc = random.choice(energy_descriptors[energy_level])
        friend_desc = random.choice(friendliness_descriptors[friendliness_level])
        species_traits = random.sample(dog_traits if species == "Dog" else cat_traits, k=3)
        age_desc = random.choice(age_traits)
        
        # Additional personality elements
        likes = random.choice([
            "loves belly rubs", "enjoys being brushed", "loves mealtime", "enjoys napping in sunbeams",
            "loves interactive play", "enjoys gentle petting", "loves outdoor adventures", "enjoys quiet companionship"
        ])
        
        ideal_home = random.choice([
            "Would thrive in an active household", "Perfect for a quiet home", 
            "Great for families with kids", "Ideal for single owner", 
            "Best with experienced pet owners", "Wonderful for first-time owners",
            "Suited for apartment living", "Needs a home with a yard"
        ])
        
        # Construct rich personality description
        description = (
            f"This {age}-year-old {breed} {species.lower()} is {energy_desc} and {friend_desc}. "
            f"{age_desc.capitalize()}. {' '.join(species_traits)}. {likes}. "
            f"{ideal_home}. {'He' if sex == 'M' else 'She'} would make a wonderful addition to the right home."
        )
        
        # Calculate numerical levels for reference (1-10 scale)
        energy_numeric = {"high": random.uniform(7, 10), "medium": random.uniform(4, 7), "low": random.uniform(1, 4)}
        friendliness_numeric = {"high": random.uniform(7, 10), "medium": random.uniform(4, 7), "low": random.uniform(1, 4)}
        
        return {
            "description": description,
            "energy_level": round(energy_numeric[energy_level], 1),
            "friendliness_level": round(friendliness_numeric[friendliness_level], 1)
        }

    rows = []
    for i in range(n):
        species = rand_species()
        breed = random.choice(dog_breeds if species == "Dog" else cat_breeds)
        name = random.choice(["Bella", "Max", "Luna", "Charlie", "Milo", "Coco", "Lucy", "Rocky", 
                            "Oliver", "Daisy", "Leo", "Sophie", "Shadow", "Whiskers", "Duke", "Princess",
                            "Buddy", "Molly", "Zeus", "Nala", "Oscar", "Lily", "Simba", "Chloe"])
        age = rand_age()
        sex = rand_sex()
        color = rand_color()
        
        # Generate rich personality profile
        profile = generate_personality_profile(species, breed, age, sex)
        
        # Generate image URL
        image_url = f"https://placeCats.com/{200+i}/{200+i}" if species == "Cat" \
                    else f"https://placedog.net/{200+i}"

        row = {
            "id": i + 1,
            "name": name,
            "species": species,
            "breed": breed,
            "age_years": age,
            "sex": sex,
            "color": color,
            "weight_kg": rand_weight(species),
            "arrival_date": rand_date(),
            "vaccinated": random.choice([True, False]),
            "microchipped": random.choice([True, False]),
            "energy_level": profile["energy_level"],
            "friendliness_level": profile["friendliness_level"],
            "personality_description": profile["description"],
            "image_url": image_url
        }
        rows.append(row)

    return pd.DataFrame(rows)

# Generate and save
if __name__ == "__main__":
    df = generate_animals(50)
    df.to_csv("animals.csv", index=False)
    print("✓ Generated 50 animals and saved to animals.csv")
    print("\nSample of first 3 animals:")
    print(df[["id", "name", "species", "breed", "energy_level", "friendliness_level"]].head(3).to_string(index=False))
    print(f"\n✓ Total: {len(df)} animals with rich personality descriptions")
    print("\nExample personality description:")
    print(f"\n{df.iloc[0]['name']}: {df.iloc[0]['personality_description']}")