from functools import wraps

import requests
import os
from flask import Flask, request

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

def authorization(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = request.headers.get('user')
        method = request.method
        original_url = request.path

        response = requests.post('http://host.docker.internal:8180/v1/is_authorized', json={
            "principal": f"User::\"{user}\"",
            "action": f"Action::\"{method.lower()}\"",
            "resource": f"ResourceType::\"{original_url.split('/')[1]}\"",
            "context": request.json
        }, headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        decision = response.json().get('decision')

        if decision != 'Allow':
            return 'Access Denied', 403
        
        return f(*args, **kwargs)
    
    return decorated

@app.route('/article')
@authorization
def get_articles():
    articles = ['article1', 'article2', 'article3']
    return {'articles': articles}

@app.route('/article/<id>', methods=['POST'])
@authorization
def create_article(id):
    return 'Article created'

@app.route('/article/<id>', methods=['PUT'])
@authorization
def update_article(id):
    return 'Article updated'

@app.route('/article/<id>', methods=['DELETE'])
@authorization
def delete_article(id):
    return 'Article deleted'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3001))
    app.run(port=port, debug=True, host='0.0.0.0')
