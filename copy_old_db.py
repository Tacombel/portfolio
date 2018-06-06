from pymongo import MongoClient
import sqlite3
import datetime


# Conexion a MongoDB

client = MongoClient('192.168.1.55')
db = client.meteor


# Tablas MongoDB
activos = db.activos
cotizaciones = db.cotizaciones
movimiento_activos = db.movimientosactivos

# Conexion a SQLite

conn = sqlite3.connect('app.db')
c = conn.cursor()

# Limpio las tablas

c.execute("DELETE FROM cotizacion")
c.execute("DELETE FROM activo")
c.execute("DELETE FROM movimiento_activo")
conn.commit()

conn.commit()
# Transferencia

cursor = activos.find()
relacion = {}
i = 1
n = 1
for data in cursor:
    relacion[data['_id']] = i
    i = i + 1
    if data['ticker'] == 'xxx':
        data['ticker'] = n
        n = n + 1
    c.execute("INSERT INTO activo (ticker, nombre, tipo, url, moneda, descargar, clase) VALUES (?, ?, ?, ?, ?, ?, ?)", (data['ticker'], data['nombre'], data['tipo'], data['url'], data['moneda'], data['descargar'], data['clase'],))

cursor = cotizaciones.find()
for data in cursor:
    data['Id_Activo'] = relacion[data['Id_Activo']]
    data['fecha'] = data['fecha'] + datetime.timedelta(hours=5)
    t = datetime.date(int(data['fecha'].strftime("%Y")), int(data['fecha'].strftime("%m")), int(data['fecha'].strftime("%d")))
    data['fecha'] = t
    c.execute("INSERT OR REPLACE INTO cotizacion (fecha, VL, activo_id) VALUES (?, ?, ?)", (data['fecha'], data['VL'], data['Id_Activo'],))

cursor = movimiento_activos.find()
for data in cursor:
    data['Id_Activo'] = relacion[data['Id_Activo']]
    data['fecha'] = data['fecha'] + datetime.timedelta(hours=5)
    t = datetime.date(int(data['fecha'].strftime("%Y")), int(data['fecha'].strftime("%m")), int(data['fecha'].strftime("%d")))
    data['fecha'] = t
    c.execute("INSERT INTO movimiento_activo (fecha, unidades, precio, activo_id, user_id) VALUES (?, ?, ?, ?, ?)", (data['fecha'], data['unidades'], data['precio'], data['Id_Activo'], 1,))

conn.commit()
