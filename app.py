
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "food.db")


# Connect to the SQLite database
def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


# Create database tables
def init_db():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS foods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                food_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                status TEXT DEFAULT 'Pending'
            )
        """)


# Display food menu and customer orders
@app.route("/")
def home():
    with connect() as db:
        foods = db.execute(
            "SELECT * FROM foods ORDER BY id DESC"
        ).fetchall()

        orders = db.execute("""
            SELECT orders.*, foods.name AS food_name
            FROM orders
            LEFT JOIN foods ON orders.food_id = foods.id
            ORDER BY orders.id DESC
        """).fetchall()

    return render_template("index.html", foods=foods, orders=orders)


# CREATE: Add a new food item
@app.route("/add", methods=["POST"])
def add_food():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    try:
        price = float(request.form.get("price", ""))
        if not name or price < 0:
            raise ValueError
    except ValueError:
        return "Enter a valid dish name and non-negative price.", 400

    with connect() as db:
        db.execute(
            "INSERT INTO foods (name, description, price) VALUES (?, ?, ?)",
            (name, description, price)
        )

    return redirect(url_for("home"))


# UPDATE: Edit food item details
@app.route("/update/<int:food_id>", methods=["POST"])
def update_food(food_id):
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    try:
        price = float(request.form.get("price", ""))
        if not name or price < 0:
            raise ValueError
    except ValueError:
        return "Enter valid dish details.", 400

    with connect() as db:
        db.execute(
            """UPDATE foods
               SET name = ?, description = ?, price = ?
               WHERE id = ?""",
            (name, description, price, food_id)
        )

    return redirect(url_for("home"))


# DELETE: Remove a food item
@app.route("/delete/<int:food_id>", methods=["POST"])
def delete_food(food_id):
    with connect() as db:
        db.execute("DELETE FROM foods WHERE id = ?", (food_id,))

    return redirect(url_for("home"))


# CREATE: Place a customer order
@app.route("/order", methods=["POST"])
def place_order():
    customer = request.form.get("customer", "").strip()

    try:
        food_id = int(request.form.get("food_id", ""))
        quantity = int(request.form.get("quantity", ""))
        if not customer or quantity < 1:
            raise ValueError
    except ValueError:
        return "Enter a valid customer name and quantity.", 400

    with connect() as db:
        food = db.execute(
            "SELECT id FROM foods WHERE id = ?", (food_id,)
        ).fetchone()

        if food is None:
            return "Please select an available dish.", 400

        db.execute(
            """INSERT INTO orders (customer, food_id, quantity)
               VALUES (?, ?, ?)""",
            (customer, food_id, quantity)
        )

    return redirect(url_for("home"))


# UPDATE: Change customer order status
@app.route("/order-status/<int:order_id>", methods=["POST"])
def update_order_status(order_id):
    status = request.form.get("status", "")
    allowed_statuses = {
        "Pending", "Preparing", "Delivered", "Cancelled"
    }

    if status not in allowed_statuses:
        return "Invalid order status.", 400

    with connect() as db:
        db.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id)
        )

    return redirect(url_for("home"))


# Initialize the database
init_db()


if __name__ == "__main__":
    app.run(debug=True)
