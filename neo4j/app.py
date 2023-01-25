from flask import Flask, jsonify, request
from neo4j import GraphDatabase
import os

app = Flask(__name__)

# Set up connection to Neo4j
uri = os.environ.get("NEO_URI")
user = os.environ.get("NEO_USERNAME")
password = os.environ.get("NEO_PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, password), database="neo4j")


# Helper function to build query
def build_query(name=None, surname=None, position=None, sort=None, order=None):
    query = "MATCH (e:Employee)"
    filters = []
    if name:
        filters.append(f"e.name = '{name}'")
    if surname:
        filters.append(f"e.surname = '{surname}'")
    if position:
        filters.append(f"e.position = '{position}'")
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " RETURN e, elementId(e)"
    if sort:
        sort = sort.split(",")
        query += f" ORDER BY {', '.join([f'e.{attr}' for attr in sort])} {order}"
    return query


# GET endpoint to retrieve all employees
@app.route("/employees", methods=["GET"])
def get_employees():
    name = request.args.get("name")
    surname = request.args.get("surname")
    position = request.args.get("position")
    sort = request.args.get("sort")
    order = request.args.get("order", "")
    query = build_query(name, surname, position, sort, order)

    with driver.session() as session:
        result = session.run(query)
        employees = [
            {
                "id": employee["elementId(e)"],
                "name": employee["e"]["name"],
                "surname": employee["e"]["surname"],
                "position": employee["e"]["position"],
                "department": employee["e"]["department"]
            }
            for employee in result
        ]

        return jsonify(employees)


# POST endpoint to add a new employee
@app.route("/employees", methods=["POST"])
def add_employee():
    name = request.json.get("name")
    surname = request.json.get("surname")
    position = request.json.get("position")
    department = request.json.get("department")
    if not all(val for val in [name, surname, position, department]):
        return jsonify({"message": "Missing required fields"})
    with driver.session() as session:
        check = session.run(f"MATCH (e:Employee) WHERE e.name = '{name}' AND e.surname = '{surname}' RETURN e.name")
        if check.single():
            return jsonify({"message": "employee already exists"})
        else:
            session.run(
                f"CREATE (e:Employee {{name: '{name}', surname: '{surname}', position: '{position}', department: '{department}'}})"
            )
            return jsonify({"message": "employee added"})


# PUT endpoint to update an employee
@app.route("/employees/<employee_id>", methods=["PUT"])
def update_employee(employee_id):
    name = request.json.get("name")
    surname = request.json.get("surname")
    position = request.json.get("position")
    department = request.json.get("department")

    with driver.session() as session:
        session.run(
            f"MATCH (e:Employee) WHERE id(e) = {employee_id}"
            f"SET e.name = '{name}', e.surname = '{surname}', e.position = '{position}', e.department = '{department}'"
        )
        return jsonify({"message": "employee updated"})


# DELETE endpoint to delete an employee
@app.route("/employees/<employee_id>", methods=["DELETE"])
def delete_employee(employee_id):
    with driver.session() as session:
        session.run(f"MATCH (e:Employee) WHERE id(e) = {employee_id} DETACH DELETE e")
        return jsonify({"message": "employee deleted"})


# GET endpoint to retrieve an employee's subordinates
@app.route("/employees/<employee_id>/subordinates", methods=["GET"])
def get_subordinates(employee_id):
    with driver.session() as session:
        result = session.run(
            f"MATCH (e:Employee)-[:REPORTS_TO]->(s:Employee) WHERE id(e) = {employee_id}"
            f"RETURN s, elementId(s)"
        )
        subordinates = [
            {
                "id": subordinate["elementId(s)"],
                "name": subordinate["s"]["name"],
                "surname": subordinate["s"]["surname"],
                "position": subordinate["s"]["position"],
                "department": subordinate["s"]["department"],
            }
            for subordinate in result
        ]
        return jsonify(subordinates)


# GET endpoint to retrieve an employee's department
@app.route("/employees/<employee_id>/department", methods=["GET"])
def get_employee_department(employee_id):
    with driver.session() as session:
        result = session.run(
            f"MATCH (e:Employee)-[:BELONGS_TO]->(d:Department) WHERE id(e) = {employee_id} RETURN d.name"
        )
        return jsonify({"department": result.single()[0]})


# GET endpoint to retrieve all departments
@app.route("/departments", methods=["GET"])
def get_departments():
    with driver.session() as session:
        result = session.run("MATCH (d:Department) RETURN d.name")
        departments = [department[0] for department in result]
        return jsonify({"departments": departments})


# GET endpoint to retrieve all employees in a department
@app.route("/departments/<department_name>/employees", methods=["GET"])
def get_department_employees(department_name):
    with driver.session() as session:
        result = session.run(
            f"MATCH (e:Employee)-[:BELONGS_TO]->(d:Department) WHERE d.name = '{department_name}' RETURN e, elementId(e)"
        )
        employees = [
            {
                "id": employee["elementId(e)"],
                "name": employee["e"]["name"],
                "surname": employee["e"]["surname"],
                "position": employee["e"]["position"],
                "department": employee["e"]["department"],
            }
            for employee in result
        ]
        return jsonify(employees)
