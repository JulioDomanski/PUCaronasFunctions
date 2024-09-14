import azure.functions as func
import json
from bson.objectid import ObjectId
from pymongo import MongoClient

app = func.FunctionApp()

client = MongoClient("mongodb+srv://juliodomanski:<PASSWORD>@pjbl-pucarona.whh8x.mongodb.net/?retryWrites=true&w=majority&appName=PJBL-PUCARONA")
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
