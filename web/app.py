from flask import Flask


#initialize flask app
app = Flask(__name__)
app.secret_key = 'gobrr'


@app.route('/')
def home():
    return "Hello World"

if __name__ == "__main__":
    app.run(debug=True, port=5000)
