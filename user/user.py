
import json
import time
import requests
#import booking_pb2
#import booking_pb2_grpc
#import movie_pb2
#import movie_pb2_grpc
# CALLING gRPC requests

from concurrent import futures
from pymongo import MongoClient
from bson.json_util import dumps
from werkzeug.exceptions import NotFound
from flask import Flask, render_template, request, jsonify, make_response
from flask_jwt_extended import (
   JWTManager,
   create_access_token,
   get_jwt_identity,
   jwt_required,
   set_access_cookies,
   get_jwt
)

app = Flask(__name__)

client = MongoClient("mongodb://root:example@mongo:27017/?authSource=admin")

db = client["users"]
collection = db["users"]

app.config["JWT_SECRET_KEY"] = "7oiz2wPmzQFaKxw7GwNC__5inY7i1bSKwW2MnlkgnC0"
app.config["JWT_TOKEN_LOCATION"]= ["headers","cookies"]
app.config["JWT_COOKIE_SECURE"] = False

jwt = JWTManager(app)

PORT = 3004
HOST = '0.0.0.0'

with open('{}/data/users.json'.format("."), "r") as jsf:
   users = json.load(jsf)["users"]

collection.insert_many(users)
# Authentication route
@app.route("/login", methods= ["POST"])
def login():

   name = request.args.get("username")
   query = {"name": str(name)}
   user = collection.find_one(query)

   if user :
      additional_claims = {"admin": user.get("admin", False), "dev": user.get("dev", False)}
      token = create_access_token(identity = user["id"], additional_claims = additional_claims)
      
      last_active = int(time.time())
      user["last_active"] = last_active
      collection.replace_one(query , user)
      response = make_response(jsonify(token), 200)
      set_access_cookies(response, token)
      return response
   return make_response(jsonify({"Error":"User not in database"}), 400)


# Get user infos 
@app.route("/user/<userid>", methods= ['GET'])
@jwt_required()
def infos(userid):

   claims = get_jwt()
   is_admin = claims.get("admin", False)

   if get_jwt_identity() != userid and not is_admin:
      return make_response(jsonify({"Error": "Access denied"}), 403)

   query = {"id": str(userid)}
   user = collection.find_one(query)

   if user :
      return make_response(dumps(user), 200)

   return make_response(jsonify({"Error":"User in not in database"}), 404)


# CALLING GraphQL requests 
# todo to complete

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
