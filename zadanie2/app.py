from flask import Flask, jsonify, request
from neo4j import GraphDatabase

user="neo4j"
password="test1234"
uri="bolt://localhost:7687"

app = Flask(__name__)

driver = GraphDatabase.driver(uri, auth=(user, password),database="neo4j")

def get_employees(tx, sort_category, filter_info):
    order_by = f'ORDER BY e.{sort_category}' if sort_category != "" else ""
    
    contains = f'WHERE e.{filter_info["kategoria"]} CONTAINS "{filter_info["klucz"]}"' if filter_info != "" else ""
    
    query = f"MATCH (e:Employee) {contains} RETURN e, elementId(e) {order_by}"
    results = tx.run(query).data()

    employees = [{'id': result['elementId(e)'],'imie': result['e']['imie'], 'nazwisko': result['e']['nazwisko'], 'stanowisko': result['e']['stanowisko']} for result in results]

    return employees

@app.route('/employees', methods=['GET'])
def get_employees_route():
    sort_category = request.json['sort'] if 'sort' in request.json else ""
    filter_info = request.json['filter'] if 'filter' in request.json else ""

    with driver.session() as session:
        employees = session.read_transaction(get_employees, sort_category, filter_info)

    response = {'employees': employees}
    return jsonify(response)


def add_employee(tx, imie, nazwisko, stanowisko, departament):
    query = "MERGE (e:Employee {imie: $imie, nazwisko: $nazwisko, stanowisko: $stanowisko})-[r:WORKS_IN]->(d:Department {nazwa: $departament}) RETURN e,r,d"

    tx.run(query, imie=imie, nazwisko=nazwisko, stanowisko=stanowisko, departament=departament)


@app.route('/employees', methods=['POST'])
def add_employee_route():
    imie = request.json['imie']
    nazwisko = request.json['nazwisko']
    stanowisko = request.json['stanowisko']
    departament = request.json['departament']

    with driver.session() as session:
        session.write_transaction(add_employee, imie, nazwisko, stanowisko, departament)

    response = {'status': 'success'}
    return jsonify(response)


def update_employee(tx, id, nowe_imie, nowe_nazwisko, nowe_stanowisko, nowy_departament):
    query = "MATCH (e:Employee) WHERE elementId(e)=$id RETURN e"
    result = tx.run(query, id=id).data()

    if not result:
        return None
    else:
        query = "MATCH (e:Employee)-[r:WORKS_IN]->(:Department) WHERE elementId(e)=$id MERGE (d:Department {nazwa: $nowy_departament}) DELETE r CREATE (e)-[:WORKS_IN]->(d) SET e.imie=$nowe_imie, e.nazwisko=$nowe_nazwisko, e.stanowisko=$nowe_stanowisko"
        tx.run(query, id=id, nowe_imie=nowe_imie, nowe_nazwisko=nowe_nazwisko, nowe_stanowisko=nowe_stanowisko, nowy_departament=nowy_departament)
        return {'imie': nowe_imie, 'nazwisko': nowe_nazwisko, 'stanowisko': nowe_stanowisko, 'departament': nowy_departament}


@app.route('/employees/<string:id>', methods=['PUT'])
def update_employee_route(id):
    nowe_imie = request.json['imie']
    nowe_nazwisko = request.json['nazwisko']
    nowe_stanowisko = request.json['stanowisko']
    nowy_departament = request.json['departament']

    with driver.session() as session:
        employee = session.write_transaction(update_employee, id, nowe_imie, nowe_nazwisko, nowe_stanowisko, nowy_departament)

    if not employee:
        response = {'message': 'Employee not found'}
        return jsonify(response), 404
    else:
        response = {'status': 'success'}
        return jsonify(response)


def delete_employee(tx, id):
    query = "MATCH (e:Employee) WHERE elementId(e)=$id RETURN e"
    result = tx.run(query, id=id).data()

    if not result:
        return None
    else:
        query = "MATCH (e:Employee) WHERE elementId(e)=$id DETACH DELETE e"
        tx.run(query, id=id)
        return {'id': id}

@app.route('/employees/<string:id>', methods=['DELETE'])
def delete_employee_route(id):
    with driver.session() as session:
        employee = session.write_transaction(delete_employee, id)

    if not employee:
        response = {'message': 'employee not found'}
        return jsonify(response), 404
    else:
        response = {'status': 'success'}
        return jsonify(response)

def get_subordinates_of_employee(tx, id):
    query = "MATCH (e:Employee)-[:MANAGES]->(s:Employee) WHERE elementId(e)=$id RETURN s"
    results = tx.run(query, id=id).data()

    subordinates = [{'imie': result['s']['imie'], 'nazwisko': result['s']['nazwisko'], 'stanowisko': result['s']['stanowisko']} for result in results]

    return subordinates

@app.route('/employees/<string:id>/subordinates', methods=['GET'])
def get_subordinates_of_employee_route(id):
    with driver.session() as session:
        subordinates = session.write_transaction(get_subordinates_of_employee, id)

    if not subordinates:
        response = {'message': 'employee not found'}
        return jsonify(response), 404
    else:
        response = subordinates
        return jsonify(response)


def get_department_of_employee(tx, id):
    query = "MATCH (e:Employee)-[:WORKS_IN]->(d:Department) WHERE elementId(e)=$id RETURN d"
    department = tx.run(query, id=id).data()

    query = "MATCH (m:Employee)-[:MANAGES]->(d:Department) WHERE d.nazwa=$nazwa RETURN m"
    manager = tx.run(query, nazwa = department[0]["d"]["nazwa"]).data()

    query = "MATCH (e:Employee)-[:WORKS_IN]->(d:Department) WHERE d.nazwa=$nazwa RETURN e"
    workers = tx.run(query, nazwa = department[0]["d"]["nazwa"]).data()

    departmentInfo = {
        'nazwa': department[0]["d"]["nazwa"],
        'manager': manager[0]["m"]["imie"] + " " + manager[0]["m"]["nazwisko"],
        'liczba pracownikow': len(workers)
    }

    return departmentInfo

@app.route('/employees/<string:id>/department', methods=['GET'])
def get_department_of_employee_route(id):
    with driver.session() as session:
        department = session.write_transaction(get_department_of_employee, id)

    if not department:
        response = {'message': 'employee not found'}
        return jsonify(response), 404
    else:
        response = department
        return jsonify(response)


def get_departments(tx):
    query = "MATCH (e:Employee)-[:WORKS_IN]->(d:Department) RETURN elementId(d) AS ID, d.nazwa AS nazwa, count(e) AS liczba_pracownikow"
    departments = tx.run(query).data()

    return departments

@app.route('/employees/departments', methods=['GET'])
def get_departments_route():
    with driver.session() as session:
        departments = session.write_transaction(get_departments)

        response = departments
        return jsonify(response)


def get_workers_of_department(tx, id):
    query = "MATCH (e:Employee)-[:WORKS_IN]->(d:Department) WHERE elementId(d)=$id RETURN e"
    results = tx.run(query, id=id).data()

    subordinates = [{'imie': result['e']['imie'], 'nazwisko': result['e']['nazwisko'], 'stanowisko': result['e']['stanowisko']} for result in results]

    return subordinates

@app.route('/departments/<string:id>/employees', methods=['GET'])
def get_workers_of_department_route(id):
    with driver.session() as session:
        subordinates = session.write_transaction(get_workers_of_department, id)

    if not subordinates:
        response = {'message': 'department not found'}
        return jsonify(response), 404
    else:
        response = subordinates
        return jsonify(response)


if __name__ == '__main__':
    app.run()
