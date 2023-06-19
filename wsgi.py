from app_web_server import app

#wsgi server for Guinicorn
if __name__ == "__main__":
    app.run()