# Getting Started with Flask

Flask is a lightweight WSGI web application framework written in Python. It's designed to make getting started quick and easy, with the ability to scale up to complex applications.

## Installation

First, install Flask using pip:

```bash
pip install flask
```

## Creating Your First Application

Here's a simple "Hello World" application:

```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)
```

## Routing

Flask uses decorators to bind functions to URLs:

```python
@app.route('/user/<username>')
def show_user_profile(username):
    return f'User: {username}'

@app.route('/post/<int:post_id>')
def show_post(post_id):
    return f'Post: {post_id}'
```

## HTTP Methods

By default, routes only respond to GET requests. You can specify other methods:

```python
from flask import request

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return do_login()
    else:
        return show_login_form()
```

## Templates

Flask uses Jinja2 for templating:

```python
from flask import render_template

@app.route('/hello/<name>')
def hello(name):
    return render_template('hello.html', name=name)
```

## Static Files

Place static files (CSS, JavaScript, images) in a `static` folder in your package.

## Next Steps

- Learn about blueprints for larger applications
- Explore Flask extensions for common features
- Implement database integration with Flask-SQLAlchemy
- Add user authentication with Flask-Login
