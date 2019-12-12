import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    FLASK_DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTS_PER_PAGE = 10
    UPLOAD_FOLDER = r'C:\Users\golov\OneDrive\Documents\microblog\app\upload_files'

