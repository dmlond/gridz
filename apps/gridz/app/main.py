from app import app
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from pymongo import MongoClient
from bson.objectid import ObjectId

@app.before_request
def before_request():
    g.client = MongoClient()
    
@app.teardown_request
def teardown_request(exception):
    client = getattr(g, 'client', None)
    if client is not None:
        client.close()

@app.route('/')
def show_grid():
    columns = [{"id": "title", "name": "Titlate", "field": "title" },
               {"id":  "duration", "name" :  "Duration", "field":  "duration" },
               {"id":  "%", "name":  "% Complete", "field":  "percentComplete" },
               {"id":  "start", "name":  "Start", "field":  "start" },
               {"id":  "finish", "name":  "Finish", "field":  "finish" },
               {"id":  "effort-driven", "name":  "Effort Driven", "field":  "effortDriven" } ]
    return render_template('grid.html',columns=columns)

@app.route('/create')
def create_grid():
    return render_template('create_grid.html')

# AJAX UI
@app.route('_database_names')
def get_database_names():
    client = getattr(g, 'client', None)
    return jsonify([db for db in client.database_names() if db != 'local'])

@app.route('/_entries')
def get_entries():
    client = getattr(g, 'client', None)

    db_name = request.arg.get('database_name', None, type=str)
    collection_name = request.arg.get('collection_name', None, type=str)
    document = request.arg.get('document', None)
    if db_name is None || collection_name is None || document is None:
        return jsonify({'error': 'You must supply a db_name, collection_name, and document query'})
    else
        return jsonify(client[db_name][collection_name].find(document['query'], fields=document['fields'], exhaust=bool(1)))

@app.route('/_entry')
def get_entry():
    # process request.args to return the requested entry as json
    client = getattr(g, 'client', None)

    db_name = request.arg.get('database_name', None, type=str)    
    collection_name = request.arg.get('collection_name', None, type=str)
    document = request.arg.get('document', None)
    id = request.arg.get('_id', None, type=str)
    
    if db_name is None || collection_name is None
        return jsonify({'error': 'You must supply a db_name, collection_name, and document query or _id ObjectId'})
        if document is None
            if id is None
                return jsonify({'error': 'You must supply a db_name, collection_name, and document query or _id ObjectId'})
            else
                return jsonify(client[db_name][collection_name].find_one({'_id': ObjectId(id)}, fields=document['fields']))
        else
            return jsonify(client[db_name][collection_name].find_one(document['query'], fields=document['fields']))

@app.route('/_create_entry')
def create_entry():
    client = getattr(g, 'client', None

    db_name = request.arg.get('database_name', None, type=str)
    collection_name = request.arg.get('collection_name', None, type=str)
    document = request.arg.get('document', None)
    if document is None:
        return jasonify({'error': 'please supply a document to insert', 'document': document })
    else
        if collection_name is not None && document is not None:
            client[db_name][collection_name].insert(document)
            return jsonify(document)
    
@app.route('/_update_entry')
def update_entry():
    client = getattr(g, 'client', None)

    db_name = request.arg.get('database_name', None, type=str)
    collection_name = request.arg.get('collection_name', None, type=str)
    document = request.arg.get('document', None)

    if document['id'] is None:
        return jasonify({'error': 'please suplly an id in the document to update', 'document': document })
    else
        if collection_name is not None && document is not None:
            client[db_name][collection_name].update(document['query'],document['update'])
            return jsonify(document)

@app.route('/_remove_entry')
def remove_entry():
    # process request.args to remove an 
    client = getattr(g, 'client', None)

    db_name = request.arg.get('database_name', None, type=str)
    collection_name = request.arg.get('collection_name', None, type=str)
    document = request.arg.get('document', None)
    if collection_name is not None && document is not None:
        client[db_name][collection_name].remove(document['query'])
        return jsonify({'message': 'removed'})
