from ariadne import graphql_sync, make_executable_schema, load_schema_from_path, ObjectType, QueryType, MutationType
from flask import Flask, request, jsonify
from bson.json_util import dumps
import json, requests

from pymongo import MongoClient 

from env import BOOKING_PORT as PORT, DB_PORT, MOVIE_PORT



app = Flask(__name__)

client = MongoClient(f"mongodb://mongo:{DB_PORT}")
db = client["booking"]
bookings = db["bookings"]

if not bookings.find_one():
    with open("./data/bookings.json", "r") as f:
        tmp = json.load(f)["bookings"]
    bookings.insert_many(tmp)



type_defs = load_schema_from_path("./booking.graphql")
query = QueryType()
mutation = MutationType()
booking = ObjectType("Booking")

def booking_from_user_id(_, info, user_id):
    return bookings.find_one({ "userid": user_id })

def book_date(_, info, user_id, date, movie_id):
    query = f"{{                        \
      movie_by_id(id: \"{movie_id}\") {{\
        title                           \
      }}                                \
    }}"
    res = requests.post(f"http://localhost:{MOVIE_PORT}/graphql", json={ "query": query })

    if not res.ok or not res.json()["data"]["movie_by_id"]:
        return

    if booking := bookings.find_one({ "userid": user_id }):
        found = False
        for entry in booking["dates"]:
            if date == entry["date"]:
                entry["movies"].append(movie_id)
                found = True
                break
        if not found:
            booking["dates"].append({
                "date": date,
                "movies": [movie_id]
            })
    else:
        booking = {
            "userid": user_id,
            "dates": [{
                "date": date,
                "movies": [movie_id]
            }]
        }

    bookings.replace_one({ "userid": user_id }, booking, upsert=True)
    return booking
        
query.set_field("booking_from_user_id", booking_from_user_id)
mutation.set_field("book_date", book_date)
schema = make_executable_schema(type_defs, query, mutation)



@app.route("/graphql", methods=['POST'])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(schema, data, context_value=None, debug=app.debug)

    return jsonify(result), 200 if success else 400



if __name__ == "__main__":
    print(f"Server running in port {PORT}")
    app.run(host="0.0.0.0", port=PORT)
