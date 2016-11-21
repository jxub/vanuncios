# -*- coding: utf-8 -*-
import os
import sqlite3
from flask import (
    Flask, request, session, g, redirect, url_for,
    abort, render_template, flash
    )

app = Flask(__name__)

app.config.update(dict(
    DATABASE = os.path.join(app.root_path, 'vanuncios.db'),
    SECRET_KEY = 'my dev key',
    USERNAME = 'admin',
    PASSWORD = 'admin',
))

app.config.from_envvar('VANUNCIOS_SETTINGS', silent=True)

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    
@app.cli.command('initdb')
def initdb_command():
    init_db()
    print 'Initialized the database for Vanuncios'

def get_db():
    #creates a new db connection for this app context g
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    #closes the db connection if there is any in the context
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()
    
@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select title, text from entries order by id desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (title, text) values (?, ?)',
                 [request.form['title'], request.form['text']])
    db.commit()
    flash('Has publicado un nuevo anuncio')
    return redirect(url_for('show_entries'))

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        if (request.form['password'] != app.config['PASSWORD'] and
        request.form['username'] != app.config['USERNAME']):
            error = 'Contraseña y usuario inválidos'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Contraseña inválida'
        elif request.form['username'] != app.config['USERNAME']:
            error = 'El usuario no existe'
        else:
            session['logged_in'] = True
            flash('Has iniciado la sesion')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Has cerrado la sesion')
    return redirect(url_for('show_entries'))

host = os.getenv('IP', '0.0.0.0')
port = int(os.getenv('PORT', 8080))

if __name__ == "__main__":
    app.run(host=host, port=port, debug=True)
