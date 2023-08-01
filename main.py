import requests
from bs4 import BeautifulSoup
from googlesearch import search
import nltk
import pickle
import os.path

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


nltk.download('punkt')
nltk.download('stopwords')


class ContentAggregator:
    def __init__(self):
        self.content = []

    def aggregate_content(self, query):
        for url in search(query, num_results=10):
            try:
                response = requests.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                text = soup.get_text()
                self.content.append(text)
            except requests.exceptions.RequestException as e:
                continue

    def save_content(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self.content, file)

    def load_content(self, filename):
        if os.path.exists(filename):
            with open(filename, 'rb') as file:
                self.content = pickle.load(file)


class Recommender:
    def __init__(self, content):
        self.content = content
        self.stopwords = set(stopwords.words('english'))

    def preprocess_text(self, text):
        tokens = word_tokenize(text.lower())
        filtered_tokens = [token for token in tokens if token.isalnum() and token not in self.stopwords]
        return ' '.join(filtered_tokens)

    def calculate_similarity(self, query):
        query = self.preprocess_text(query)
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform([query] + self.content)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
        return similarities[0]


class UserProfile:
    def __init__(self, username):
        self.username = username
        self.preferences = {}

    def add_preference(self, preference, rating):
        self.preferences[preference] = rating

    def get_preferences(self):
        return self.preferences

    def clear_preferences(self):
        self.preferences = {}

    def save_profile(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self, file)

    @staticmethod
    def load_profile(filename):
        if os.path.exists(filename):
            with open(filename, 'rb') as file:
                return pickle.load(file)


class ContentRecommendationSystem:
    def __init__(self, content_filename, user_profiles_filename):
        self.content_filename = content_filename
        self.user_profiles_filename = user_profiles_filename
        self.content_aggregator = ContentAggregator()
        self.recommender = None
        self.user_profiles = {}

    def initialize_system(self):
        self.content_aggregator.load_content(self.content_filename)

        if not self.content_aggregator.content:
            query = input('Enter query for content aggregation: ')
            self.content_aggregator.aggregate_content(query)
            self.content_aggregator.save_content(self.content_filename)

        self.recommender = Recommender(self.content_aggregator.content)

        self.user_profiles = UserProfile.load_profile(self.user_profiles_filename)

    def recommend_content(self, username, query):
        if username not in self.user_profiles:
            self.user_profiles[username] = UserProfile(username)

        similarities = self.recommender.calculate_similarity(query)
        content_indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)
        recommended_content = [self.content_aggregator.content[idx] for idx in content_indices]

        return recommended_content

    def rate_content(self, username, preference, rating):
        if username in self.user_profiles:
            self.user_profiles[username].add_preference(preference, rating)
            self.user_profiles[username].save_profile(self.user_profiles_filename)

    def clear_user_preferences(self, username):
        if username in self.user_profiles:
            self.user_profiles[username].clear_preferences()
            self.user_profiles[username].save_profile(self.user_profiles_filename)

    def get_user_preferences(self, username):
        if username in self.user_profiles:
            return self.user_profiles[username].get_preferences()
        else:
            return {}

    def recommendation_interface(self):
        username = input('Enter username: ')

        while True:
            print('\nChoose an option:')
            print('1. Recommend content')
            print('2. Rate content')
            print('3. Clear user preferences')
            print('4. Exit')

            option = input('Enter option number: ')

            if option == '1':
                query = input('Enter query for content recommendation: ')
                recommended_content = self.recommend_content(username, query)
                print('\nRecommended content:')
                for idx, content in enumerate(recommended_content, start=1):
                    print(f'{idx}. {content}')

            elif option == '2':
                preference = input('Enter content preference: ')
                rating = float(input('Enter rating (0-1): '))
                self.rate_content(username, preference, rating)
                print('Content rating saved.')

            elif option == '3':
                self.clear_user_preferences(username)
                print('User preferences cleared.')

            elif option == '4':
                break


def main():
    content_filename = 'content.pickle'
    user_profiles_filename = 'user_profiles.pickle'

    system = ContentRecommendationSystem(content_filename, user_profiles_filename)
    system.initialize_system()
    system.recommendation_interface()


if __name__ == '__main__':
    main()