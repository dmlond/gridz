import sys
import json
from app import app
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, jsonify, Response

from pymongo import MongoClient
import sqlite3
from bson.objectid import ObjectId
from contextlib import closing
from flask_wtf import Form
import wtforms
from wtforms import widgets, TextField, TextAreaField, BooleanField, SelectMultipleField, FieldList, FormField, SubmitField

class SchemaForm(Form):
    name = TextField("Name")
    description = TextAreaField("Description")
    submit = SubmitField("Create")

class GridFormFields(wtforms.Form):
    name = TextField("name")
    is_queryable_by = SelectMultipleField('is Queryable By',
                                          choices=[('filter', 'Filter'), ('attribute', 'Attribute')]
        )
        
class GridForm(Form):
    name = TextField("Name")
    description = TextAreaField("Description")
    grid_form_fields = FieldList(FormField(GridFormFields))
    submit = SubmitField("Create")

def find_schema(db,id):
    cur = db.execute('select id, name, description from schemas where id = ?', (id,))
    row = cur.fetchone()
    return dict(id=row[0],name=row[1],description=row[2])

def find_grid(db,id):
    cur = db.execute("select id, schema_id, name, description from grids where id = ?", (id,))
    row = cur.fetchone()
    return dict(id=row[0], schema_id=row[1], name=row[2], description=row[3])

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

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

#SCHEMAS
@app.route('/')
@app.route('/schemas')
@app.route('/schemas/<type>')
def schemas(type=None):
    cur = g.db.execute('select id, name, description from schemas order by id desc')
    schemas = [ dict(id=row[0], name=row[1], description=row[2]) for row in cur.fetchall() ]
    if type is None:
        return render_template('schemas.html', schemas=schemas)
    else:
        return Response(json.dumps(schemas),  mimetype='application/json')

@app.route('/schema/<id>')
def schema(id):
    schema = find_schema(g.db,id)
    return render_template('schema.html', schema=schema)

@app.route('/schema/<id>/destroy')
def destroy_schema(id):
    g.db.execute("delete from schemas where id = ?", (id,))
    g.db.commit()
    return redirect(url_for('schemas'))

@app.route('/schema/new')
def new_schema():
    form = SchemaForm()
    return render_template('new_schema.html',form=form)

@app.route('/schema/create', methods=['POST'])
def create_schema():
    form = SchemaForm(request.form)
    cur = g.db.execute('insert into schemas(name, description) values(?, ?)',
                 [form.name.data, form.description.data])
    new_id = cur.lastrowid
    g.db.commit()
    flash('New schema was successfully posted')
    return redirect(url_for('schema', id=new_id))

# GRID MANAGEMENT
@app.route('/gridz/<schema_id>')
@app.route('/gridz/<schema_id>/<type>')
def gridz(schema_id,type=None):
    cur = None
    schema = find_schema(g.db, schema_id)
    cur = g.db.execute('select id, name, description from grids order by id desc')
    grids = [dict(id=row[0], name=row[1], description=row[2]) for row in cur.fetchall()]
    if type is None:
        return render_template('gridz.html', schema=schema,grids=grids)
    else:
        return jsonify({schema['name']: grids})

@app.route('/grid/<schema_id>/<id>')
def grid(schema_id,id):
    schema = find_schema(g.db,schema_id)
    grid = find_grid(g.db,id)
    cur = g.db.execute('select name, is_attribute, is_filter from grid_fields where grid_id = ?', (id,))
    grid_attributes = []
    grid_filters = []
    for grid_field in cur.fetchall():
        if grid_field[1]:
            grid_attributes.append(grid_field[0])
        if grid_field[2]:
            grid_filters.append(grid_field[0])
    return render_template('grid.html', schema=schema,grid=grid,grid_attributes=grid_attributes,grid_filters=grid_filters)

@app.route('/grid/<schema_id>/new')
def new_grid(schema_id):
    schema = find_schema(g.db,schema_id)
    form = GridForm()
    form.grid_form_fields.append_entry()
    return render_template('new_grid.html', schema=schema,form=form)

@app.route('/grid/<schema_id>/create', methods=['POST'])
def create_grid(schema_id):
    try:
        form = GridForm(request.form)
        cur = g.db.execute('insert into grids(name, schema_id, description) values(?, ?, ?)',
        [form.name.data, schema_id, form.description.data])
        new_id = cur.lastrowid

        grid_fields = []
        for grid_form_field in form.grid_form_fields.data:
            grid_field = [ new_id, grid_form_field['name'] ]
            is_attribute = 0
            if 'attribute' in grid_form_field['is_queryable_by']:
                is_attribute = 1
            grid_field.append(is_attribute)

            is_filter = 0
            if 'filter' in grid_form_field['is_queryable_by']:
                is_filter = 1
            grid_field.append(is_filter)
            grid_fields.append(grid_field)

        g.db.executemany('insert into grid_fields(grid_id, name, is_attribute, is_filter) values(?,?,?,?)', grid_fields)
        g.db.commit()
        flash("New grid was successfully created")
        return redirect(url_for('grid',schema_id=schema_id,id=new_id))
    except Exception as e:
        g.db.rollback()
        sys.stderr.write("GOT AN ERROR\n")
        return 500

@app.route('/grid/<schema_id>/<id>/destroy')
def destroy_grid(schema_id,id):
    g.db.execute('delete from grid_fields where grid_id = ?',(id,))
    g.db.execute('delete from grids where schema_id = ? and id = ?', (schema_id, id))
    g.db.commit()
    flash("Grid deleted")
    return redirect(url_for('gridz',schema_id=schema_id))

#DATA
@app.route('/gridz/<schema_id>/<id>/data', methods=['GET','POST'])
@app.route('/gridz/<schema_id>/<id>/data/<type>', methods=['GET','POST'])
def view_data(schema_id,id,type=None):
    schema = find_schema(g.db,schema_id)
    grid = find_grid(g.db,id)
    cur = g.db.execute('select name from grid_fields where grid_id = ?', (id,))
    grid_fields = [ row[0] for row in cur.fetchall() ]

    entries = None
    if request.method == 'POST':
        requested_attributes = request.arg.get('attributes')
        attributes = {}
        for attribute in grid_fields:
            attributes[attribute] = attribute in requested_attributes
        entries = g.client[schema.name][grid.name].find(request.arg.get('query'),fields=attributes, exhaust=True)
    else:
        entries = g.client[schema.name][grid.name].find(None,exhaust=True)
    
    if type is None:
        columns = [ dict(id=row[0], name=row[0], field=row[0]) for row in grid_fields ]
        return render_template('grid_data.html', schema=schema, grid=grid, columns=columns, entries=entries)
    else:
        if type == 'csv':
            columns = grid_fields
            return render_template('grid_data.csv', columns=columns, entries=entries)
        else:
            return jsonify(entries)

@app.route('/gridz/<schema_id>/<id>/data/query')
def query_grid(id):
    # render form to query based on grid attributes and filters with action url_for('view_data')
    return render_template('query_grid.html')

@app.route('/gridz/<schema_id>/<id>/data/edit')
def edit_data(id):
    schema = find_schema(g.db,schema_id)
    grid = find_grid(g.db,id)
    grid_fields = [ row[0] for row in cur.fetchall() ]

    entries = None
    if request.method == 'POST':
        requested_attributes = request.arg.get('attributes')
        attributes = {}
        for attribute in grid_fields:
            attributes[attribute] = attribute in requested_attributes            
        entries = g.client[schema.name][grid.name].find(request.arg.get('query'),fields=attributes, exhaust=True)
        entries = g.client[schema.name][grid.name].find(request.arg.get('document'),exhaust=True)
    else:
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
    
    if db_name is None or collection_name is None:
        return jsonify({'error': 'You must supply a db_name, collection_name, and document query or _id ObjectId'})

    if document is None:
        if id is None:
            return jsonify({'error': 'You must supply a db_name, collection_name, and document query or _id ObjectId'})
        else:
            return jsonify(g.client[db_name][collection_name].find_one({'_id': ObjectId(id)}, fields=document['fields']))
    else:
        return jsonify(g.client[db_name][collection_name].find_one(document['query'], fields=document['fields']))

@app.route('/gridz/_entry/create', methods=['POST'])
def create_entry():
    db_name = request.arg.get('database_name', None, type=str)
    collection_name = request.arg.get('collection_name', None, type=str)
    document = request.arg.get('document', None)
    if document is None:
        return jsonify({'error': 'please supply a document to insert', 'document': document })
    else:
        if collection_name is not None and document is not None:
            g.client[db_name][collection_name].insert(document)
            return jsonify(document)
    
@app.route('/gridz/_entry/update', methods=['POST'])
def update_entry():
    db_name = request.arg.get('database_name', None, type=str)
    collection_name = request.arg.get('collection_name', None, type=str)
    document = request.arg.get('document', None)

    if document['id'] is None:
        return jsonify({'error': 'please suplly an id in the document to update', 'document': document })
    else:
        if collection_name is not None and document is not None:
            g.client[db_name][collection_name].update(document['query'],document['update'])
            return jsonify(document)

@app.route('/gridz/_entry/remove', methods=['POST'])
def remove_entry():
    db_name = request.arg.get('database_name', None, type=str)
    collection_name = request.arg.get('collection_name', None, type=str)
    document = request.arg.get('document', None)
    if collection_name is not None and document is not None:
        g.client[db_name][collection_name].remove(document['query'])
        return jsonify({'message': 'removed'})
