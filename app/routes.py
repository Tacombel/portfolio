from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from werkzeug.urls import url_parse
from app.email import send_password_reset_email
import sqlite3
import XIRR
import datetime


def add_asset_units():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute('SELECT * FROM movimiento_activo ORDER BY fecha DESC')
    query = c.fetchall()
    units = {}
    for q in query:
        if q[4] in units:
            units[q[4]] = units[q[4]] + q[2]
        else:
            units[q[4]] = q[2]
    for key, value in units.items():
        if value < 0.000001:
            units[key] = 0
    return units


def assets_with_units():
    units = add_asset_units()
    delete = []
    for key, value in units.items():
        if value == 0:
            delete.append(key)
    for e in delete:
        del units[e]
    return units


def date_to_eu_format(fecha):
    fecha = datetime.date(int(fecha[0:4]), int(fecha[5:7]), int(fecha[8:]))
    return fecha.strftime("%-d-%-m-%Y")


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
        ticker = q[1]
        nombre = q[2]
        fechaultima = date_to_eu_format(data[0][1])
        VLultimo = data[0][2]
        VLanterior = data[1][2]
        variation = (VLultimo - VLanterior) / VLanterior * 100
        VLultimo = "{0:.4f}".format(VLultimo)
        VLanterior = "{0:.4f}".format(VLanterior)
        fechaanterior = date_to_eu_format(data[1][1])
        variation = "{0:.2f}".format(variation)
        line = []
        line.append(ticker)
        line.append(nombre)
        line.append(fechaultima)
        line.append(VLultimo)
        line.append(fechaanterior)
        line.append(VLanterior)
        line.append(variation)
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
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    response = []
    c.execute('SELECT * FROM activo')
    query = c.fetchall()
    for q in query:
        lista = []
        lista.append(q[0])
        lista.append(q[2])
        response.append(lista)
    response = sorted(response, key=lambda asset: asset[1])
    return render_template('assets.html', title='Assets', query=response)


@app.route('/asset/<id>')
@login_required
def asset(id):
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute('SELECT * FROM activo WHERE id=?', (id,))
    query = c.fetchone()
    # response
    response = []
    for q in query:
        response.append(q)
    units = add_asset_units()
    try:
        units[int(id)]
    except KeyError:
        units[int(id)] = 0
    response.append(units[int(id)])
    # data_1
    c.execute('SELECT * FROM cotizacion WHERE activo_id=? ORDER BY fecha DESC LIMIT 5', (id,))
    data_1 = c.fetchall()
    # data_2
    c.execute('SELECT * FROM movimiento_activo WHERE activo_id=? ORDER BY fecha DESC LIMIT 5', (id,))
    data_2 = c.fetchall()
    return render_template('asset.html', title='Assets', query=response, data_1=data_1, data_2=data_2)


@app.route('/asset/VL/<id>', methods=['POST'])
@login_required
def asset_vl(id):
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    fecha = request.form.get('fecha')
    VL = request.form.get('VL')
    c.execute("INSERT OR REPLACE INTO cotizacion (fecha, VL, activo_id) VALUES (?, ?, ?)", (fecha, VL, id,))
    conn.commit()
    return redirect(url_for('asset', id=id))


@app.route('/asset/movement/<id>', methods=['POST'])
@login_required
def asset_movement(id):
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    fecha = request.form.get('fecha')
    unidades = request.form.get('unidades')
    precio = request.form.get('precio')
    c.execute("INSERT OR REPLACE INTO movimiento_activo (fecha, unidades, precio, activo_id, user_id) VALUES (?, ?, ?, ?, ?)", (fecha, unidades, precio, id, 1,))
    conn.commit()
    return redirect(url_for('asset', id=id))


@app.route('/npv')
@login_required
def npv():
    units = assets_with_units()
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    NPV = 0
    response = []
    for key in units:
        c.execute('SELECT * FROM activo WHERE id=?', (key,))
        query = c.fetchone()
        activo_id = query[0]
        name = query[2]
        number = units[key]
        currency = query[5]
        c.execute('SELECT * FROM cotizacion WHERE activo_id=? ORDER BY fecha DESC LIMIT 1', (key,))
        query = c.fetchone()
        date = query[1]
        VL = query[2]
        # XIRR
        if number == 1:
            rate = "-"
        else:
            c.execute('SELECT * FROM movimiento_activo WHERE activo_id=?', (key,))
            query = c.fetchall()
            values = []
            dates = []
            for q in query:
                number_2 = q[2] * (-1)
                price = q[3]
                date_2 = q[1]
                values.append(number_2 * price)
                dates.append(datetime.date(int(date_2[0:4]), int(date_2[5:7]), int(date_2[8:])))
            values.append(number * VL)
            dates.append(datetime.date(int(date[0:4]), int(date[5:7]), int(date[8:])))
            try:
                rate = "{0:.2f}".format(XIRR.xirr(values, dates) * 100) + "%"
            except: # noqa
                rate = "Error"
        # END XIRR
        if currency == 'EUR':
            value = units[key] * VL
        elif currency == 'GBP':
            c.execute('SELECT * FROM cotizacion WHERE activo_id=? ORDER BY fecha DESC LIMIT 1', (11,))
            query = c.fetchone()
            value_currency = query[2]
            value = units[key] * VL / value_currency
        elif currency == 'USD':
            c.execute('SELECT * FROM cotizacion WHERE activo_id=? ORDER BY fecha DESC LIMIT 1', (10,))
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
        date = date_to_eu_format(date)
        line = []
        line.append(name)
        line.append(number)
        line.append(date)
        line.append(VL)
        line.append(currency)
        line.append(value)
        line.append(rate)
        line.append(activo_id)
        response.append(line)
    response = sorted(response, key=lambda asset: asset[0])
    NPV = "{0:.2f}".format(NPV) + "€"
    return render_template('npv.html', title='NPV', query=response, NPV=NPV)
