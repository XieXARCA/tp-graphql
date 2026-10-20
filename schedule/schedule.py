import os 
import json
from werkzeug.exceptions import NotFound
from bson.json_util import dumps

from pymongo import MongoClient
from flask_jwt_extended import create_access_token, get_jwt_identity, get_jwt, jwt_required, JWTManager
from flask import Flask, request, jsonify
from env import SCHEDULE_PORT as PORT, DB_PORT, SECRET, ADMIN_PASSWORD



app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = SECRET
jwt = JWTManager(app)


client = MongoClient(f"mongodb://root:example@mongo:{DB_PORT}/?authSource=admin")

db = client["schedule"]
collection = db["schedule"]


with open("/app/data/times.json", "r") as jsf:
   schedule = json.load(jsf)["schedule"]

if not collection.find_one():
   collection.insert_many(schedule)



# /schedule?[from][to]
@app.route("/schedule", methods=["GET"])
def get_schedule():
   from_ = None
   to = None
   if req := request.args:
      if "from" in req:
         from_ = int(req["from"])
      if "to" in req:
         to = int(req["to"])

   if from_ is None and to is None:
      dumps(collection.find()), 200

   res = []
   for entry in collection.find():
      date = int(entry["date"])
      if (from_ is None or date >= from_) and (to is None or date <= to):
         res.append(entry)
   return dumps(res), 200

@app.route("/schedule/<date>", methods=["GET"])
def get_date(date):
   if entry := collection.find_one({ "date": date }):
      return dumps(entry), 200
   return jsonify({ "error": "date not found" }), 404

@app.route("/schedule/<date>", methods=["POST"])
@jwt_required()
def add_movies(date):
   movies = request.get_json()["movies"]

   if not get_jwt()["admin"]:
      return jsonify({ "error": "not authorized" }), 401

   query = { "date": date }
   if entry := collection.find_one(query):
      movies.extend(entry["movies"])
      collection.update_one(query, { "$set": { "movies": movies }})
   else:
      collection.insert_one({
         "date": date,
         "movies": movies
      })

   return dumps(collection.find_one(query)), 200

@app.route("/schedule/<date>", methods=["DELETE"])
@jwt_required()
def remove_date(date):
   if not get_jwt()["admin"]:
      return jsonify({ "error": "not authorized" }), 401

   if entry := collection.find_one_and_delete({ "date": date }):
      return dumps(entry), 200
   return jsonify({ "error": "date not found" }), 404

   

if __name__ == "__main__":
   print(f"Server running in port {PORT}")
   app.run(host="0.0.0.0", port=PORT)
