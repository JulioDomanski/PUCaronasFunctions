import azure.functions as func
import json
from bson.objectid import ObjectId
from pymongo import MongoClient
from azure.servicebus import ServiceBusClient, ServiceBusMessage

SERVICE_BUS_CONNECTION_STRING = "Endpoint=sb://pucarona.servicebus.windows.net/;SharedAccessKeyName=Publisher;SharedAccessKey=MLFWPuR0PCyh9ZngTQU3iAnbL+GM32RVK+ASbIlyG8k=;EntityPath=pucaronaqueue"
SERVICE_BUS_QUEUE_NAME = "pucaronaqueue"


app = func.FunctionApp()

client = MongoClient("mongodb+srv://juliodomanski:porra123@pjbl-pucarona.whh8x.mongodb.net/?retryWrites=true&w=majority&appName=PJBL-PUCARONA")
db = client.get_database("PUCaronas")
collection = db.get_collection("usuarios")


@app.function_name('POSTusuario')
@app.route(route="CriarUsuario", methods=['POST'])
def post_usuario(req: func.HttpRequest) -> func.HttpResponse:
    req_body = req.get_json()

    
    required_fields = ['nome', 'email', 'telefone', 'cpf', 'tipo_usuario']
    for fields in required_fields:
        if fields not in req_body:
            return func.HttpResponse(
                json.dumps({"error": f"O campo {fields} está faltando."}),
                status_code=400,
                mimetype="application/json"
            )
        
    if req_body['tipo_usuario'] == 'motorista':
        if "numero_cnh" not in req_body:
            return func.HttpResponse(
                json.dumps({"error": "o campo numero da cnh esta faltando!"}),
                status_code=400,
                mimetype="application/json"
            )

    
    user_data = {
        "nome": req_body['nome'],
        "email": req_body['email'],
        "telefone": req_body['telefone'],
        "cpf": req_body['cpf'],
        "numero_cnh": req_body['numero_cnh'],
        "tipo_usuario": req_body['tipo_usuario'],
    }
    
    
    result = collection.insert_one(user_data)
    new_user_id = str(result.inserted_id)

    return func.HttpResponse(
            json.dumps({"message": "Usuário criado com sucesso!", "_id": new_user_id}),
            status_code=201,
            mimetype="application/json"
        )

@app.function_name('GETusuario')
@app.route(route="consultarUsuario/{user_id}", methods=['GET'])
def get_usuario(req: func.HttpRequest) -> func.HttpResponse:
    user_id = req.route_params.get('user_id')

    user = collection.find_one({"_id": ObjectId(user_id)})
    
    if user:
        user['_id'] = str(user['_id'])  
        return func.HttpResponse(
            json.dumps(user),
            status_code=200,
            mimetype="application/json"
        )
    else:
        return func.HttpResponse(
            json.dumps({"error": "Usuário não encontrado"}),
            status_code=404,
            mimetype="application/json"
        )

@app.function_name('VERusuario')
@app.route(route="verificaUsuario", methods=['POST'])
def verifica_tipo_usuario(req: func.HttpRequest) -> func.HttpResponse:

    body = req.get_json()
    id_usuario = body["id_usuario"]
    user = collection.find_one({"_id": ObjectId(id_usuario)})

    if user:
        user['_id'] = str(user['_id']) 
        tipo_usuario = user.get("tipo_usuario", "").lower()
        if tipo_usuario == "aluno":

            servicebus_client = ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION_STRING)
            body["http_code"] = "200"
            message_content = json.dumps(body)

            with servicebus_client.get_queue_sender(SERVICE_BUS_QUEUE_NAME) as sender:
                message = ServiceBusMessage(message_content)
                sender.send_messages(message)

            return func.HttpResponse(
                json.dumps(body),
                status_code=200,
                mimetype="application/json"
            )
        else:
            error_message = {
                "http_code": "401",
                "message": f"O usuario nao eh Aluno."
            }
            servicebus_client = ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION_STRING)
            message_content = json.dumps(error_message)

            with servicebus_client.get_queue_sender(SERVICE_BUS_QUEUE_NAME) as sender:
                message = ServiceBusMessage(message_content)
                sender.send_messages(message)

            return func.HttpResponse(
                json.dumps(error_message),
                status_code=401,
                mimetype="application/json"
            )
    else:
        error_message = {
            "http_code": "404",
            "message": "Usuario nao encontrado."
        }
        servicebus_client = ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION_STRING)
        message_content = json.dumps(error_message)

        with servicebus_client.get_queue_sender(SERVICE_BUS_QUEUE_NAME) as sender:
            message = ServiceBusMessage(message_content)
            sender.send_messages(message)
        return func.HttpResponse(
                json.dumps(error_message),
                status_code=400,
                mimetype="application/json"
            )

@app.function_name('PUTusuario')
@app.route(route="atualizarUsuario", methods=['PUT'])
def update_usuario(req: func.HttpRequest) -> func.HttpResponse:
    req_body = req.get_json()
    user_id = req_body.get('id')  

    if not user_id:
        return func.HttpResponse(
            json.dumps({"error": "ID do usuário não fornecido"}),
            status_code=400,
            mimetype="application/json"
        )

    
    user = collection.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        return func.HttpResponse(
            json.dumps({"error": "Usuário não encontrado"}),
            status_code=404,
            mimetype="application/json"
        )
    
    updated_data = {
        "nome": req_body.get("nome", user["nome"]),
        "email": req_body.get("email", user["email"]),
        "telefone": req_body.get("telefone", user["telefone"]),
        "numero_cnh": req_body.get("numero_cnh", user["numero_cnh"]),
        "tipo_usuario": req_body.get("tipo_usuario", user["tipo_usuario"]),
    }

    collection.update_one({"_id": ObjectId(user_id)}, {"$set": updated_data})

    return func.HttpResponse(
        json.dumps({"message": "Usuário atualizado com sucesso"}),
        status_code=200,
        mimetype="application/json"
    )

@app.function_name('DELETEusuario')
@app.route(route="deletarUsuario/{user_id}", methods=['DELETE'])
def delete_usuario(req: func.HttpRequest) -> func.HttpResponse:

    user_id = req.route_params.get('user_id')
    result = collection.delete_one({"_id": ObjectId(user_id)})

    if result.deleted_count != 1:
        return func.HttpResponse(
                json.dumps({"message": "Usuário não encontrado"}),
                status_code=404,
                mimetype="application/json"
            )
    return func.HttpResponse(
        json.dumps({"message": "Usuário excluido com sucesso"}),
        status_code=200,
        mimetype="application/json"
    )
