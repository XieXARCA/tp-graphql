from ariadne import graphql_sync, make_executable_schema, load_schema_from_path, ObjectType, QueryType, MutationType
from flask import Flask, request, jsonify
import json

from pymongo import MongoClient 

from env import MOVIE_PORT as PORT, DB_PORT



app = Flask(__name__)

client = MongoClient(f"mongodb://mongo:{DB_PORT}")
db = client["movie"]
movies = db["movies"]
actors = db["actors"]

if not movies.find_one():
    with open("./data/movies.json", "r") as f:
        tmp = json.load(f)["movies"]
    movies.insert_many(tmp)

if not actors.find_one():
    with open("./data/actors.json", "r") as f:
        tmp = json.load(f)["actors"]
    actors.insert_many(tmp)



type_defs = load_schema_from_path("./movie.graphql")
query = QueryType()
movie = ObjectType("Movie")
actor = ObjectType("Actor")

def movie_by_id(id):
    return movies.find_one({ "id": id })

def movie_actors(movie):
    return [actor for actor in actors.find() if movie["id"] in actor["films"]]

def actor_by_name(name):
    return actors.find_one({ "lastname": name })

def actor_movies(actor):
    return [movie_by_id(id) for id in actor["films"]]
        

query.set_field("movie_by_id",   lambda _, info, id: movie_by_id(id))
movie.set_field("actors",        lambda movie, info: movie_actors(movie))
query.set_field("actor_by_name", lambda _, info, name: actor_by_name(name))
actor.set_field("films",         lambda actor, info: actor_movies(actor))
schema = make_executable_schema(type_defs, movie, actor, query)



@app.route("/graphql", methods=['POST'])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(schema, data, context_value=None, debug=app.debug)

    return jsonify(result), 200 if success else 400



if __name__ == "__main__":
    print(f"Server running in port {PORT}")
    app.run(host="0.0.0.0", port=PORT)
