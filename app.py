import os
from os.path import join, dirname
from dotenv import load_dotenv
from flask import Flask, request, url_for, render_template, jsonify, redirect
from pymongo import MongoClient
import requests
from datetime import datetime
from bson import ObjectId

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")

app = Flask(__name__)

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]


@app.route('/')
def main():
    words_saved = db.words.find({}, {'_id': False})
    words = []
    for word in words_saved:
        definition = word['definitions'][0]['shortDef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition
        })
    word = request.args.get('word')
    temp_suggestions = request.args.get('suggestions')
    suggestions = None
    if temp_suggestions:
        suggestions = temp_suggestions.split(',')
    return render_template('index.html', data=words, word=word, suggestions=suggestions)


@app.route('/detail/<keyword>')
def detail(keyword):
    apiKey = '2a2f3d4e-e5ae-4170-a70d-52a147b1c185'
    url = f'https: //www.dictionaryapi.com/api/v3/references/collegiate/json/{
        keyword}?key={apiKey}'
    response = requests.get(url)
    definitions = response.json()

    if not definitions:
        return redirect(url_for(
            'main',
            word=keyword
        ))

    if type(definitions[0]) is str:
        suggestions = ','.join(definitions)
        return redirect(url_for(
            'main',
            word=keyword,
            suggestions=suggestions
        ))

    status = request.args.get('status', 'new')
    return render_template('detail.html', word=keyword, defs=definitions, status=status)


@app.route('/api/save', methods=['POST'])
def saveWord():
    json_data = request.get_json()
    word = json_data.get('wordGive')
    definitions = json_data.get('definitions')
    time = datetime.now()
    time = time.strftime('%d-%m-%Y')

    data = {
        'word': word,
        'definitions': definitions,
        'time': time
    }
    db.words.insert_one(data)

    return jsonify({
        'result': 'success',
        'msg': f'The Word, {word}, Has Been Saved'
    })


@app.route('/api/delete_word', methods=['POST'])
def deleteWord():
    word = request.form.get('wordGive')
    db.words.delete_one({'word': word})
    db.examples.delete_many({'word': word})
    return jsonify({
        'result': 'success',
        'msg': f'The Word, {word}, Has Been Deleted'
    })


@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word_give')
    example_data = db.examples.find({'word': word})
    examples = []
    for example in example_data:
        examples.append({
            'id': str(example.get('_id')),
            'example': example.get('example')
        })
    return ({
        'result': 'success',
        'examples': examples
    })


@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    example = request.form.get('example')
    word = request.form.get('word')
    doc = {
        'example': example,
        'word': word
    }
    db.examples.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'Your Examples, {example}, for word {word}, was saved!'
    })


@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    db.examples.delete_one({'_id': ObjectId(id)})
    return jsonify({
        'result': 'success',
        'msg': f'Your Example from word {word}, was deleted'
    })


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

# apiKey = '2a2f3d4e-e5ae-4170-a70d-52a147b1c185'
# word = 'plane'
# url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={apiKey}'
# res = requests.get(url)
# result = req.json()
# print(responses)
