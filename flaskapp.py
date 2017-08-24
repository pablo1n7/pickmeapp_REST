# -*- coding: utf-8 -*-
import json
from models.models import Usuario, Lugar, Mensaje
from flask import Flask, request,\
     render_template
from flask_socketio import SocketIO, emit, disconnect

app = Flask(__name__, static_folder='statics')
app.config.from_pyfile('flaskapp.cfg',)
socketio = SocketIO(app, ping_timeout=120, async_mode='threading')
clients = {}

@app.route("/")
def index():
    ''' Retorna la pagina principal '''
    return render_template("index.html")


@app.route("/guardarusuario",methods=['POST'])
def guardar_usuario():
    '''
        Guardar usuario en la base de datos. Devuelve error

        El json que se envia por POST tiene la siguiente forma:
            {"nombre": "usuario1n7", "id_usuario": "33778434611"}

    '''
    try:
        usr = Usuario(request.get_json())
        usr.guardar()
    except Exception:
        return json.dumps({'codigo':500, 'descripcion':'ERROR:Usuario en uso'})
    return json.dumps({'codigo':'200'})

@socketio.on('getlugares')
def get_lugares(usuario_nombre=None):
    '''
        Retorna los lugares agregados por un usuario
            si usuario_nombre!=None regresa todos  los lugares
    '''
    lugares = Lugar.get_lugares(usuario_nombre)
    emit("getlugares", json.dumps(lugares), room=request.sid)

@socketio.on('getusuarios')
def get_usuarios():
    '''
        Retorna los usuarios    
    '''
    print("getusuarios")
    usuarios = Usuario.get_usuarios()
    emit("getusuarios", json.dumps(usuarios), room=request.sid)

#@app.route("/guardarlugar",methods=['POST'])
@socketio.on('guardarlugar')
def guardar_lugar(nombre, latlng, descripcion, usuario):
    '''
        Metodo que guarda un lugar. El json que se envia por POST tiene la siguiente forma:
            {"nombre": "CASA", "latlng": "2222/222", "descripcion": "es mi lugar",
            "usuario":"pablo1n7"}

    '''
    data = {"nombre": nombre, "latlng": latlng, "descripcion": descripcion, "usuario":usuario}
    lugar = Lugar(data)
    id_lugar = lugar.guardar()
    emit("guardarlugar", {'codigo':'200', 'id_lugar':str(id_lugar)}, room=request.sid)

@socketio.on('mensaje')
def enviar_mensaje(destinatorio, texto_mensaje,id_lugar=None):
    '''
        Mensajeria por socketIO. Evento "mensaje".
    '''
    usuario_destino = Usuario.get_usuario(destinatorio)
    mensaje = Mensaje(usuario_destino.id_usuario, texto_mensaje, id_lugar)
    try:
        socket_destino = clients[usuario_destino.id_usuario]
        for key in list(clients.keys()):
            if clients[key] == request.sid:
                origen = key
        emit("mensaje", {"origen":origen, "mensaje":texto_mensaje, "id_lugar":id_lugar}, 
             room=socket_destino)
        mensaje.estado = "enviado"
        mensaje.guardar()
    except KeyError:
        mensaje.guardar()




@socketio.on('conectar')
def conectar(user_id):
    '''
        Metodo de conexion, que ademas registra las conexiones activas.
    '''
    print("Alguien se quiere conectar")
    #user_id = request.args.get('user_id', '')
    try:
        print("Alguien se quiere conectar {}".format(user_id))
        usuario = Usuario.get_usuario_por_id(user_id)
        emit("conectar", {'status':'OK','usuario':usuario.nombre}, room=request.sid)
        clients[user_id] = request.sid
        mensajes_sin_enviar = Mensaje.get_mensajes(usuario.id_usuario)
        for msg in mensajes_sin_enviar:
            emit("mensaje", {"origen":Usuario.get_usuario_por_id(msg.id_origen).nombre,
                            "mensaje":msg.mensaje,"id_lugar":msg.id_lugar}, room=request.sid)
            msg.registrar_envio()
        print('Client Connect {}'.format(usuario.nombre))
    
    except Exception:
        emit("no_registrado", {'codigo':404, 'descripcion':'ERROR: usuario no encontrado'}, room=request.sid)
        print("no_registrado")
        #disconnect()
    

@socketio.on('disconnect')
def desconectar():
    '''
        Metodo de desconeccion, elimina la conexion de la lista de conexiones activas.
    '''
    for key in list(clients.keys()):
        if clients[key] == request.sid:
            print('Client disconnected')
            del clients[key]

def main():
    '''Metodo principal'''
    #socketio.run(app,host="192.168.0.9",port=80)
    socketio.run(app,host="0.0.0.0")

if __name__ == "__main__":
    main()
