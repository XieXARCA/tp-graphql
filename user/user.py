
import json, hashlib, base64
import time
import requests
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

from env import SCHEDULE_PORT as PORT, DB_PORT, SECRET, ADMIN_PASSWORD

app = Flask(__name__)

client = MongoClient(f"mongodb://mongo:{DB_PORT}")

db = client["users"]
collection = db["users"]

app.config["JWT_SECRET_KEY"] = SECRET
app.config["JWT_TOKEN_LOCATION"]= ["headers","cookies"]
app.config["JWT_COOKIE_SECURE"] = False

jwt = JWTManager(app)

HOST = '0.0.0.0'

with open('/app/data/users.json', "r") as jsf:
   users = json.load(jsf)["users"]

collection.insert_many(users)

def hexhash(text):
   return hashlib.sha256(text.encode("utf-8")).hexdigest()


@app.route("/signup", methods=["POST"])
def signup():
   body = request.get_json()
   id       = body["id"]
   password = body["password"]
   name = body["name"]

   if collection.find_one({ "id": id }):
      return jsonify({ "Error": "id taken" }), 403

   collection.insert_one({
      "id": id,
      "password": hexhash(password),
      "name" : name
   })
   
   return jsonify({ "success": "signed up" }), 200


# Authentication route
@app.route("/login", methods= ["POST"])
def login():

   name = request.args.get("username")
   password = request.args.get("password")

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
