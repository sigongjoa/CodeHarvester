from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html', title='대시보드')

@main.route('/about')
def about():
    return render_template('about.html', title='시스템 소개')
