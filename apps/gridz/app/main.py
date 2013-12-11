from app import app
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from pymongo import MongoClient
import sqlite3
from bson.objectid import ObjectId

@app.before_request
def before_request():
    g.db = connect_db()
    g.client = MongoClient()
    
@app.teardown_request
def teardown_request(exception):
    client = getattr(g, 'client', None)
    if client is not None:
        client.close()
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def find_schema(db, id):
    cur = db.execute("select id, name, description from schemas where id = ?", (id,))
    row = curr.fetchone()
    return dict(id=row[0], name=row[1], description=row[2])

def find_grid(db, schema_id, id):
    cur = db.execute("select id, name, description from grids where schema_id = ? and id = ?", (schema_id, id))
    row = curr.fetchone()
    return dict(id=row[0], name=row[1], description=row[2])

#SCHEMAS
@app.route('/')
@app.route('/schemas')
@app.route('/schemas/<type>')
def schemas():
    cur = g.db.execute('select id, name, description from schemas order by id desc')
    schemas = [dict(id=row[0], name=row[1], description=row[2]) for row in cur.fetchall()]
    if type is None:
        render_template('schemas.html', schemas=schemas)
    else
        return jsonify(schemas)

@app.route('/schema/<id>')
def schema():
    schema = find_schema(g.db, id)
    return render_template('schema.html', schema=schema)

@app.route('/schema/<id>/destroy')
def destroy_schema():
    curr = g.db.execute("delete from schemas where id = ?", (id,))
    db.commit()
    return redirect(url_for('schemas'))

@app.route('/schema/new')
def new_schema():
    return render_template('new_schema.html')

@app.route('/schema/create', methods=['POST'])
def create_schema():
    cur = g.db.execute('insert into schemas(name, description) values(?, ?)',
                 [request.form['name'], request.form['description']])
    new_id = cur.lastrowid
    g.db.commit()
    flash('New schema was successfully posted')
    return redirect(url_for('schema', id=new_id))

# GRID MANAGEMENT
@app.route('/gridz/<schema_id>')
@app.route('/gridz/<schema_id>/<type>')
def gridz():
    cur = None
    schema = get_schema(g.db, schema_id)
    cur = g.db.execute('select id, name, description from grids order by id desc')
    grids = [dict(id=row[0], name=row[1], description=row[2]) for row in cur.fetchall()]
    if type is None:
        return render_template('gridz.html', schema=schema,grids=grids)
    else
        return jsonify(dict("{ schema.name }"=grids))

@app.route('/gridz/<schema_id>/<id>')
def grid():
    schema = find_schema(g.db, schema_id)
    grid = find_grid(g.db, schema_id, id)
    cur = g.db.execute('select name, is_attribute, is_filter from grid_fields where grid_id = ?', (grid.id,))
    grid_attributes = []
    grid_filters = []
    for grid_field in cur.fetchall():
        if grid_field[1]:
            grid_attributes.append(grid_field[0])
        if grid_field[2]:
            grid_filters.append(grid_field[0])
    return render_template('grid.html', schema=schema,grid=grid,grid_attributes,grid_filters)

@app.route('/gridz/<schema_id>/new')
def new_grid():
    schema = find_schema(g.db, schema_id)
    return render_template('new_grid.html', schema=schema)

@app.route('/gridz/<schema_id>/create', methods=['POST'])
def create_grid():
    cur = g.db.execute('insert into grids(name, schema_id, description) values(?, ?, ?)',
    [request.form['name'], schema_id, request.form['description']])
    new_id = cur.lastrowid
    grid_fields = [ [ new_id, field['name'], field['is_attribute'], field['is_filter'] ] for field in request.form['grid_fields'] ]
    g.db.executemany('insert into grid_fields(grid_id, name, is_attribute, is_filter) values(?,?,?,?)', grid_fields)
    g.db.commit()
    flash("New { schema.name } grid was successfully created")
    return redirect(url_for('grid',schema_id=schema_id,id=new_id))

@app.route('/gridz/<schema_id>/<id>/destroy')
def destroy_grid():
    g.db.execute('delete from grid_fields where grid_id = ?',(id,))
    g.db.execute('delete from grid where schema_id = ? and id = ?', (schema_id, id))
    flash("Grid deleted")
    return redirect(url_for('gridz',schema_id=schema_id))

#DATA
@app.route('/gridz/<schema_id>/<id>/data', methods=['GET','POST'])
@app.route('/gridz/<schema_id>/<id>/data/<type>', methods=['GET','POST'])
def view_data():
    schema = find_schema(g.db, schema_id)
    grid = find_grid(g.db, schema_id, id)
    cur = g.db.execute('select name from grid_fields where grid_id = ?', (grid.id,))
    grid_fields = [ row[0] for row in cur.fetchall() ]

    entries = None
    if request.method == 'POST':
        requested_attributes = request.arg.get('attributes')
        attributes = dict( attribute=(attribute in requested_attributes) for attribute in grid_fields )
        entries = g.client[schema.name][grid.name].find(request.arg.get('query'),fields=attributes, exhaust=True)
    else
        entries = g.client[schema.name][grid.name].find(None,exhaust=True)
    
    if type is None:
        columns = [ dict(id=row[0], name=row[0], field=row[0]) for row in grid_fields ]
        return render_template('grid_data.html', schema=schema, grid=grid, columns=columns, entries=entries)
    else
        if type == 'csv':
            columns = grid_fields
            return render_template('grid_data.csv', columns=columns, entries=entries)
        else
            return jsonify(entries)

@app.route('/gridz/<id>/data/query')
def query_grid():
    # render form to query based on grid attributes and filters with action url_for('view_data')
    return render_template('query_grid.html')

@app.route('/gridz/<id>/data/edit')
def edit_data():
    schema = find_schema(g.db, schema_id)
    grid = find_grid(g.db, schema_id, id)
    grid_fields = [ row[0] for row in cur.fetchall() ]

    entries = None
    if request.method == 'POST':
        requested_attributes = request.arg.get('attributes')
        attributes = dict( attribute=(attribute in requested_attributes) for attribute in grid_fields )
        entries = g.client[schema.name][grid.name].find(request.arg.get('query'),fields=attributes, exhaust=True)
        entries = g.client[schema.name][grid.name].find(request.arg.get('document'),exhaust=True)
    else
        entries = g.client[schema.name][grid.name].find(None,exhaust=True)
    
    cur = g.db.execute('select name from grid_fields where grid_id = ?', (grid.id,))
    columns = [ dict(id=row[0], name=row[0], field=row[0]) for row in grid_fields ]
    return render_template('edit_data.html', schema=schema, grid=grid, columns=columns, entries=entries)

# AJAX UI

@app.route('/gridz/_entry', methods=['POST'])
def get_entry():
    # process request.args to return the requested entry as json
    db_name = request.arg.get('database_name', None, type=str)    
    collection_name = request.arg.get('collection_name', None, type=str)
    document = request.arg.get('document', None)
    id = request.arg.get('_id', None, type=str)
    
    if db_name is None || collection_name is None:
        return jsonify({'error': 'You must supply a db_name, collection_name, and document query or _id ObjectId'})

    if document is None:
        if id is None:
            return jsonify({'error': 'You must supply a db_name, collection_name, and document query or _id ObjectId'})
        else
            return jsonify(g.client[db_name][collection_name].find_one({'_id': ObjectId(id)}, fields=document['fields']))
    else
        return jsonify(g.client[db_name][collection_name].find_one(document['query'], fields=document['fields']))

@app.route('/gridz/_entry/create', methods=['POST'])
def create_entry():
    db_name = request.arg.get('database_name', None, type=str)
    collection_name = request.arg.get('collection_name', None, type=str)
    document = request.arg.get('document', None)
    if document is None:
        return jasonify({'error': 'please supply a document to insert', 'document': document })
    else
        if collection_name is not None && document is not None:
            g.client[db_name][collection_name].insert(document)
            return jsonify(document)
    
@app.route('/gridz/_entry/update', methods=['POST'])
def update_entry():
    db_name = request.arg.get('database_name', None, type=str)
    collection_name = request.arg.get('collection_name', None, type=str)
    document = request.arg.get('document', None)

    if document['id'] is None:
        return jasonify({'error': 'please suplly an id in the document to update', 'document': document })
    else
        if collection_name is not None && document is not None:
            g.client[db_name][collection_name].update(document['query'],document['update'])
            return jsonify(document)

@app.route('/gridz/_entry/remove', methods=['POST'])
def remove_entry():
    db_name = request.arg.get('database_name', None, type=str)
    collection_name = request.arg.get('collection_name', None, type=str)
    document = request.arg.get('document', None)
    if collection_name is not None && document is not None:
        g.client[db_name][collection_name].remove(document['query'])
        return jsonify({'message': 'removed'})
