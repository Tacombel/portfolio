from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from werkzeug.urls import url_parse
from app.email import send_password_reset_email
import sqlite3
import finantial


@app.route('/')
@app.route('/index')
@login_required
def index():
    response = []
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute('SELECT * FROM activo WHERE descargar=? ORDER BY nombre', (1,))
    query = c.fetchall()

    for q in query:
        c.execute('SELECT * FROM cotizacion WHERE activo_id=? ORDER BY fecha DESC LIMIT 2', (q[0],))
        data = c.fetchall()
        fechaultima = (data[0][1],)
        VLultimo = data[0][2]
        VLanterior = data[1][2]
        variation = (VLultimo - VLanterior) / VLanterior * 100
        VLultimo = ("{0:.4f}".format(VLultimo),)
        VLanterior = ("{0:.4f}".format(VLanterior),)
        fechaanterior = (data[1][1],)
        variation = ("{0:.2f}".format(variation),)
        line = q + fechaultima + VLultimo + fechaanterior + VLanterior + variation
        response.append(line)

    return render_template('index.html', title='Home', query=response)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/assets')
@login_required
def assets():
    return render_template('assets.html', title='Assets')


@app.route('/npv')
@login_required
def npv():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute('SELECT * FROM movimiento_activo ORDER BY fecha DESC')
    query = c.fetchall()
    units = {}
    NPV = 0
    for q in query:
        if q[4] in units:
            units[q[4]] = units[q[4]] + q[2]
        else:
            units[q[4]] = q[2]
    delete = []
    for key, value in units.items():
        if value < 0.000001:
            delete.append(key)
    for e in delete:
        del units[e]
    response = []
    for key in units:
        c.execute('SELECT * FROM activo WHERE id=?', (key,))
        query = c.fetchone()
        name = query[2]
        number = units[key]
        currency = query[5]
        c.execute('SELECT * FROM cotizacion WHERE activo_id=? ORDER BY fecha DESC LIMIT 1', (key,))
        query = c.fetchone()
        date = query[1]
        VL = query[2]
        if currency == 'EUR':
            value = units[key] * VL
        elif currency == 'GBP':
            c.execute('SELECT * FROM cotizacion WHERE activo_id=? AND fecha<=? ORDER BY fecha DESC LIMIT 1', (11, date,))
            query = c.fetchone()
            value_currency = query[2]
            value = units[key] * VL / value_currency
        elif currency == 'USD':
            c.execute('SELECT * FROM cotizacion WHERE activo_id=? AND fecha<=? ORDER BY fecha DESC LIMIT 1', (10, date,))
            query = c.fetchone()
            value_currency = query[2]
            value = number * VL / value_currency
        NPV = NPV + value
        number = "{0:.2f}".format(number)
        VL = "{0:.2f}".format(VL)
        if number == "1.00":
            number = "-"
            VL = "-"
        value = "{0:.2f}".format(value) + "€"
        line = []
        line.append(name)
        line.append(number)
        line.append(date)
        line.append(VL)
        line.append(currency)
        line.append(value)
        response.append(line)
    response = sorted(response, key=lambda asset: asset[0])
    NPV = "{0:.2f}".format(NPV) + "€"
    return render_template('npv.html', title='NPV', query=response, NPV=NPV)
