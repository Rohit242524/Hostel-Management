from flask import Flask

from routes.routes import setup_routes

app = Flask(__name__)
app.secret_key = "secret"
app.permanent_session_lifetime = 3600

setup_routes(app)

if __name__ == "__main__":
    app.run(debug=True)
