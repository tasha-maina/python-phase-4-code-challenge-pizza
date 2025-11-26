#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

# initialize db
db.init_app(app)

# migrations
migrate = Migrate(app, db)

# RESTful API (not used, but required by project)
api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"


# ------------------------------
# GET /restaurants
# ------------------------------
@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants = Restaurant.query.all()
    response = [
        {
            "id": r.id,
            "name": r.name,
            "address": r.address
        }
        for r in restaurants
    ]
    return response, 200


# ------------------------------
# GET /restaurants/<id>
# ------------------------------
@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)

    if not restaurant:
        return {"error": "Restaurant not found"}, 404

    # Build nested restaurant_pizzas list
    rps = []
    for rp in restaurant.restaurant_pizzas:
        rps.append({
            "id": rp.id,
            "price": rp.price,
            "pizza_id": rp.pizza_id,
            "restaurant_id": rp.restaurant_id,
            "pizza": {
                "id": rp.pizza.id,
                "name": rp.pizza.name,
                "ingredients": rp.pizza.ingredients
            }
        })

    response = {
        "id": restaurant.id,
        "name": restaurant.name,
        "address": restaurant.address,
        "restaurant_pizzas": rps
    }

    return response, 200


# ------------------------------
# DELETE /restaurants/<id>
# ------------------------------
@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)

    if not restaurant:
        return {"error": "Restaurant not found"}, 404

    db.session.delete(restaurant)
    db.session.commit()

    return "", 204


# ------------------------------
# GET /pizzas
# ------------------------------
@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas = Pizza.query.all()
    response = [
        {
            "id": p.id,
            "name": p.name,
            "ingredients": p.ingredients
        }
        for p in pizzas
    ]
    return response, 200


# ------------------------------
# POST /restaurant_pizzas
# ------------------------------
@app.route("/restaurant_pizzas", methods=["POST"])
def create_restaurant_pizza():
    data = request.get_json()

    price = data.get("price")
    pizza_id = data.get("pizza_id")
    restaurant_id = data.get("restaurant_id")

    # Required field validation
    if price is None or pizza_id is None or restaurant_id is None:
        return {"errors": ["validation errors"]}, 400

    # Price range validation
    if price < 1 or price > 30:
        return {"errors": ["validation errors"]}, 400

    try:
        new_rp = RestaurantPizza(
            price=price,
            pizza_id=pizza_id,
            restaurant_id=restaurant_id
        )
        db.session.add(new_rp)
        db.session.commit()

    except Exception:
        db.session.rollback()
        return {"errors": ["validation errors"]}, 400

    # Success response with pizza + restaurant nested
    response = {
        "id": new_rp.id,
        "price": new_rp.price,
        "pizza_id": new_rp.pizza_id,
        "restaurant_id": new_rp.restaurant_id,
        "pizza": {
            "id": new_rp.pizza.id,
            "name": new_rp.pizza.name,
            "ingredients": new_rp.pizza.ingredients
        },
        "restaurant": {
            "id": new_rp.restaurant.id,
            "name": new_rp.restaurant.name,
            "address": new_rp.restaurant.address
        }
    }

    return response, 201


if __name__ == "__main__":
    app.run(port=5555, debug=True)
