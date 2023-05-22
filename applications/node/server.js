const express = require('express');
const app = express();
const bodyParser = require('body-parser');

app.use(bodyParser.json());

const authorization = async (req, res, next) => {
    const { user } = req.headers;
    const { method, originalUrl } = req;
    const response = await fetch('http://host.docker.internal:8180/v1/is_authorized', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        body: JSON.stringify({
            "principal": `User::\"${user}\"`,
            "action": `Action::\"${method.toLowerCase()}\"`,
            "resource": `ResourceType::\"${originalUrl.split('/')[1]}\"`
        })
    });
    const { decision } = await response.json();
    if (decision === 'Deny') {
        res.status(403).send('Access Denied');
        return;
    }
    next();
};

app.get('/article', authorization, async (req, res) => {
    const articles = ['article1', 'article2', 'article3'];
    res.send(articles);
});

app.post('/article/:id', authorization, async (req, res) => {
    res.send('Article created');
});

app.put('/article/:id', authorization, async (req, res) => {
    res.send('Article updated');
});

app.delete('/article/:id', authorization, async (req, res) => {
    res.send('Article deleted');
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
