import json
import joblib
import random
import nltk
import string
import numpy as np
import tensorflow as tf
from tensorflow import keras
from keras.preprocessing.sequence import pad_sequences

# Inisialisasi variabel
input_shape = 10
tags = []  # data tag
inputs = []  # data input atau pola
responses = {}  # data respons
words = []  # data kata
documents = []  # data kalimat dokumen
classes = []  # data kelas atau tag
ignore_words = ['?', '!']

# Memuat intent dan respons dari file JSON
def load_response():
    global responses
    responses = {}
    with open('dataset/CHATBOT.json') as content:
        data = json.load(content)
    for intent in data['intents']:
        responses[intent['tag']] = intent['responses']
        for lines in intent['patterns']:
            inputs.append(lines)
            tags.append(intent['tag'])
        for pattern in intent['patterns']:
            w = nltk.word_tokenize(pattern)
            words.extend(w)
            documents.append((w, intent['tag']))
            if intent['tag'] not in classes:
                classes.append(intent['tag'])

load_response()

# Memuat model dan encoder
le = joblib.load("model/labelencoder.joblib")
tokenizer = joblib.load("model/tokenizer.joblib")
model = keras.models.load_model('model/chatbot_model.h5')

# Fungsi untuk menghasilkan respons
def generate_response(prediction_input):
    texts_p = []
    prediction_input = [letters.lower() for letters in prediction_input if letters not in string.punctuation]
    prediction_input = ''.join(prediction_input)
    texts_p.append(prediction_input)

    prediction_input = tokenizer.texts_to_sequences(texts_p)
    prediction_input = np.array(prediction_input).reshape(-1)
    prediction_input = pad_sequences([prediction_input], input_shape)

    output = model.predict(prediction_input)
    output = output.argmax()

    response_tag = le.inverse_transform([output])[0]
    return random.choice(responses[response_tag])

# Fungsi untuk persiapan, seperti mengunduh data NLTK yang diperlukan
def preparation():
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

preparation()
