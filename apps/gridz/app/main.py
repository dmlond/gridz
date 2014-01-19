### TODO
###  - create a historical view of each grid to accompany the definitive grid
###  - updates should be expected to receive ONLY dirty fields
###  - inserts and updates will insert a record with the userid and timestamp and all current values to the historical view of the grid
###  - grids should have a published? boolean status in their meta data.
###  - users can get_publication_status
###  - inserts, updates to a published grid should fail with an error
###  - write background jobs to regularly consolidate the most recent values for each record in an unpublished grid, using the historical view

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
    if row is None:
        return row
    return dict(id=row[0],name=row[1],description=row[2])

def find_grid(db,id):
    cur = db.execute("select id, schema_id, name, description from grids where id = ?", (id,))
    row = cur.fetchone()
    if row is None:
        return row
    return dict(id=row[0], schema_id=row[1], name=row[2], description=row[3])

def find_grid_fields(db,id):
    cur = db.execute('select name, is_attribute, is_filter from grid_fields where grid_id = ?', (id,))
    fields = {}
    for grid_field in cur.fetchall():
        fields[grid_field[0]] = { 'is_attribute': bool(grid_field[1]), 'is_filter': bool(grid_field[2]) }
    return fields

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
def query_grid(schema_id,id):
    # render form to query based on grid attributes and filters with action url_for('view_data')
    return render_template('query_grid.html')

@app.route('/gridz/<schema_id>/<id>/data/edit')
def edit_data(schema_id,id):
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

# REST AJAX UI

@app.route('/grid/<schema_id>/<id>/_entry', methods=['POST'])
def get_entry(schema_id,id):
    schema = find_schema(g.db,schema_id)
    if schema is None:
        error = "schema %s does not exist!" % schema_id
        return jsonify({'error': error}), 500

    grid = find_grid(g.db,id)
    if grid is None:
        error = "grid %s does not exist!" % id
        return jsonify({'error': error}), 500

    #TODO, throw error if query includes non-filters, or fields includes non-attributes
    grid_fields = find_grid_fields(g.db, grid['id'])
    request_json =  json.loads(request.data)
    query = None
    if '_id' in request_json.keys():
        query = {'_id': ObjectId(request_json['_id'])}
    elif 'query' in request_json.keys():
        for key in request_json['query'].keys():
            if key not in grid_fields.keys():
                message = "%s is not a supported filter of this grid" % key
                return jsonify({'error': message})
            if not grid_fields[key]['is_filter']:
                message = "%s is not a supported filter of this grid" % key
                return jsonify({'error': message})
        query = request_json['query']
    else:
        return jsonify({'error': 'please supply either a document ID with the _id key, or a query!'})

    ret_doc = None
    if 'fields' in request_json.keys():
        requested_attributes = {}
        for key in request_json['fields']:
            if key != '_id':
                if key not in grid_fields.keys():
                    message = "%s is not a supported attribute of this grid" % key
                    return jsonify({'error': message})
                if not grid_fields[key]['is_attribute']:
                    message = "%s is not a supported attribute of this grid" % key
                    return jsonify({'error': message})
            requested_attributes[key] = True

        if '_id' in request_json['fields']:
            requested_attributes['_id'] = True
        else:
            requested_attributes['_id'] = False
        ret_doc = g.client[schema['name']][grid['name']].find_one(query, fields=requested_attributes)
    else:
        ret_doc = g.client[schema['name']][grid['name']].find_one(query)

    if ret_doc is None:
        return jsonify({})

    if '_id' in ret_doc.keys():
        ret_doc['_id'] = str(ret_doc['_id'])
    return jsonify(ret_doc)

@app.route('/grid/<schema_id>/<id>/_entry/create', methods=['POST'])
def create_entry(schema_id,id):
    schema = find_schema(g.db,schema_id)
    if schema is None:
        error = "schema %s does not exist!" % schema_id
        return jsonify({'error': error}), 500

    grid = find_grid(g.db,id)
    if grid is None:
        error = "grid %s does not exist!" % id
        return jsonify({'error': error}), 500

    request_json =  json.loads(request.data)
    if 'document' in request_json.keys():
        document = request_json['document']
        new_insert = g.client[schema['name']][grid['name']].insert(document)
        return jsonify({'_id': str(new_insert)})
    else:
        return jsonify({'error': 'please supply a document to insert!'})
    
@app.route('/grid/<schema_id>/<id>/_entry/update', methods=['POST'])
def update_entry(schema_id,id):
    schema = find_schema(g.db,schema_id)
    if schema is None:
        error = "schema %s does not exist!" % schema_id
        return jsonify({'error': error}), 500

    grid = find_grid(g.db,id)
    if grid is None:
        error = "grid %s does not exist!" % id
        return jsonify({'error': error}), 500

    document = request.arg.get('document', None)
    g.client[schema['name']][grid['name']].update(document['query'],document['update'])
    return jsonify(document)

@app.route('/grid/<schema_id>/<id>/_entry/remove', methods=['POST'])
def remove_entry(schema_id,id):
    schema = find_schema(g.db,schema_id)
    if schema is None:
        error = "schema %s does not exist!" % schema_id
        return jsonify({'error': error}), 500

    grid = find_grid(g.db,id)
    if grid is None:
        error = "grid %s does not exist!" % id
        return jsonify({'error': error}), 500

    document = request.arg.get('document', None)
    g.client[schema['name']][grid['name']].remove(document['query'])
    return jsonify({'message': 'removed'})
