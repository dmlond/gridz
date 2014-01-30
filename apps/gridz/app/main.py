### TODO
###  - create a historical view of each grid to accompany the definitive grid {entry_id: ObjectId(...), modification_date: date, field1: prev_field1_val, ..., fieldN: prev_fieldN_val}
###  - updates should be expected to receive ONLY dirty fields
###  - inserts and updates will insert a record with the userid and timestamp and all current values to the historical view of the grid
###  - grids should have a published? boolean status in their meta data.
###  - users can get_publication_status
###  - inserts, updates to a published grid should fail with an error
###  - write background jobs to regularly consolidate the most recent values for each record in an unpublished grid, using the historical view
###  - can we use a write_concern to find out how many entries are updated or removed from update/remove_entry
###  - create system to allow per-user access to attributes and filters, e.g. one user can see all fields as attributes or filters, but other
###    user can only see and use a subset because it is PHI


### GRID
###   fields:
###      is_attribute:
###         true: users can request documents with just this field:value in the return
###         false: field and its value are only seen in context of values for all fields
###      is_filter:
###         true: users can filter documents returned using this field:value
###         false: users cannot filter documents on this field

import sys
import json
from app import app
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, Response

from pymongo import MongoClient
from bson import Binary, Code
from bson.json_util import dumps, loads
from bson.objectid import ObjectId
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

def stringify_ids(docs):
    for doc in docs:
        if '_id' in doc.keys():
            doc['_id'] = str(doc['_id'])

def objectify_ids(docs):
    for doc in docs:
        if '_id' in doc.keys():
            doc['_id'] = ObjectId(doc['_id'])

@app.before_request
def before_request():
    g.client = MongoClient()
    if app.config['TESTING']:
        g.schema_db = 'testing_schemas'
    else:
        g.schema_db = 'schemas'

@app.teardown_request
def teardown_request(exception):
    client = getattr(g, 'client', None)
    if client is not None:
        client.close()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#SCHEMAS
@app.route('/')
@app.route('/schemas')
@app.route('/schemas/<type>')
def schemas(type=None):
    schemas = list(g.client[g.schema_db]['definitions'].find(None, exhaust=True))
    if type is None:
        stringify_ids(schemas)
        return render_template('schemas.html', schemas=schemas)
    else:
        return Response(dumps(schemas),  mimetype='application/json')

@app.route('/schema/<id>')
def schema(id):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(id)})
    stringify_ids([schema])
    return render_template('schema.html', schema=schema)

@app.route('/schema/<id>/destroy')
def destroy_schema(id):
    g.client[g.schema_db]['definitions'].remove({'_id': ObjectId(id)})
    flash("Schema deleted")
    return redirect(url_for('schemas'))

@app.route('/schema/new')
def new_schema():
    form = SchemaForm()
    return render_template('new_schema.html',form=form)

@app.route('/schema/create', methods=['POST'])
def create_schema():
    form = SchemaForm(request.form)
    new_id = g.client[g.schema_db]['definitions'].insert({'name': form.name.data, 'description': form.description.data})
    flash('New schema was successfully posted')
    return redirect(url_for('schema', id=str(new_id)))

# GRID MANAGEMENT
@app.route('/gridz/<schema_id>')
@app.route('/gridz/<schema_id>/<type>')
def gridz(schema_id,type=None):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(schema_id)})
    grids = list(g.client[schema['name']]['grids'].find(None, exhaust=True))
    if type is None:
        stringify_ids([schema] + grids)
        return render_template('gridz.html', schema=schema,grids=grids)
    else:
        return dumps({schema['name']: grids})

@app.route('/grid/<schema_id>/<id>')
def grid(schema_id,id):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(schema_id)})
    grid =  g.client[schema['name']]['grids'].find_one({'_id': ObjectId(id)})
    stringify_ids([schema,grid])
    return render_template('grid.html', schema=schema,grid=grid)

@app.route('/grid/<schema_id>/new')
def new_grid(schema_id):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(schema_id)})
    stringify_ids([schema])
    form = GridForm()
    form.grid_form_fields.append_entry()
    return render_template('new_grid.html', schema=schema,form=form)

@app.route('/grid/<schema_id>/create', methods=['POST'])
def create_grid(schema_id):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(schema_id)})
    form = GridForm(request.form)
    new_grid = {
        'name': form.name.data,
        'description': form.description.data,
        'fields': {}
    }

    for grid_form_field in form.grid_form_fields.data:
      new_grid['fields'][grid_form_field['name']] = {'is_attribute': False, 'is_filter': False}
      if 'attribute' in grid_form_field['is_queryable_by']:
        new_grid['fields'][grid_form_field['name']]['is_attribute'] = True

      if 'filter' in grid_form_field['is_queryable_by']:
        new_grid['fields'][grid_form_field['name']]['is_filter'] = True

    new_id = g.client[schema['name']]['grids'].insert(new_grid)
    flash("New grid was successfully created")
    return redirect(url_for('grid',schema_id=schema_id,id=str(new_id)))

@app.route('/grid/<schema_id>/<id>/destroy')
def destroy_grid(schema_id,id):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(schema_id)})
    g.client[schema['name']]['grids'].remove({'_id': ObjectId(id)})
    flash("Grid deleted")
    return redirect(url_for('gridz',schema_id=schema_id))

#DATA
@app.route('/gridz/<schema_id>/<id>/data', methods=['GET','POST'])
@app.route('/gridz/<schema_id>/<id>/data/<type>', methods=['GET','POST'])
def view_data(schema_id,id,type=None):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(schema_id)})
    grid =  g.client[schema['name']]['grids'].find_one({'_id': ObjectId(id)})
    stringify_ids([schema,grid])
    entries = None
    if request.method == 'POST':
        attributes = { attribute: True for attribute in request.arg.get('attributes') if grid['field'][attribute]['is_attribute'] }
        if request.arg.get('query') is not None:
            for filter in request.arg.get('query').keys():
                if filter not in grid['fields'].keys():
                    flash("%s is not a supported filter of this grid" % filter)
                    abort(500)
                if not grid['fields'][filter]['is_filter']:
                    flash("%s is not a supported filter of this grid" % filter)
                    abort(500)
                
        entries = list(g.client[schema['name']][grid['name']].find(request.arg.get('query'),fields=attributes, exhaust=True))
    else:
        entries = list(g.client[schema['name']][grid['name']].find(None,exhaust=True))

    stringify_ids([schema,grid] + entries)
    if type is None:
        columns = [ dict(id=field_name, name=field_name, field=field_name) for field_name in grid['fields'].keys() ]
        return render_template('grid_data.html', schema=schema, grid=grid, columns=columns, entries=entries)
    else:
        if type == 'csv':
            columns = grid['fields'].keys()
            return render_template('grid_data.csv', columns=columns, entries=entries)
        else:
            return dumps(entries)

@app.route('/gridz/<schema_id>/<id>/data/query')
def query_grid(schema_id,id):
    # render form to query based on grid attributes and filters with action url_for('view_data')
    return render_template('query_grid.html')

@app.route('/gridz/<schema_id>/<id>/data/edit')
def edit_data(schema_id,id):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(schema_id)})
    grid =  g.client[schema['name']]['grids'].find_one({'_id': ObjectId(id)})
    entries = None
    if request.method == 'POST':
        attributes = { attribute: True for attribute in request.arg.get('attributes') if grid['field'][attribute]['is_attribute'] }
        if request.arg.get('query') is not None:
            for filter in request.arg.get('query').keys():
                if filter not in grid['fields'].keys():
                    flash("%s is not a supported filter of this grid" % filter)
                    abort(500)
                if not grid['fields'][filter]['is_filter']:
                    flash("%s is not a supported filter of this grid" % filter)
                    abort(500)
        entries = g.client[schema['name']][grid['name']].find(request.arg.get('query'),fields=attributes, exhaust=True)
    else:
        entries = g.client[schema['name']][grid['name']].find(None,exhaust=True)
    
    columns = [ dict(id=field_name, name=field_name, field=field_name) for field_name in grid['fields'].keys() ]
    return render_template('edit_data.html', schema=schema, grid=grid, columns=columns, entries=entries)

# SINGLE ENTRY REST
@app.route('/grid/<schema_id>/<id>/_entry', methods=['POST'])
def get_entry(schema_id,id):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(schema_id)})
    if schema is None:
        error = "schema %s does not exist!" % schema_id
        return dumps({'error': error}), 500

    grid =  g.client[schema['name']]['grids'].find_one({'_id': ObjectId(id)})
    if grid is None:
        error = "grid %s does not exist!" % id
        return dumps({'error': error}), 500

    request_json = {}
    if request.data:
        request_json = loads(request.data)

    query = None
    if '_id' in request_json.keys():
        query = {'_id': ObjectId(request_json['_id']) }
    elif 'query' in request_json.keys():
        for filter in request_json['query'].keys():
            if filter not in grid['fields'].keys():
                message = "%s is not a supported filter of this grid" % filter
                return dumps({'error': message}), 500
            if not grid['fields'][filter]['is_filter']:
                message = "%s is not a supported filter of this grid" % filter
                return jsonify({'error': message}), 500
        query = request_json['query']
    else:
        return dumps({'error': 'please supply either a document ID with the _id key, or a query!'}), 500

    ret_doc = None
    if 'fields' in request_json.keys():
        requested_attributes = {}
        for attribute in request_json['fields']:
            if attribute != '_id':
                if attribute not in grid['fields'].keys():
                    message = "%s is not a supported attribute of this grid" % attribute
                    return dumps({'error': message}), 500
                if not grid['fields'][attribute]['is_attribute']:
                    message = "%s is not a supported attribute of this grid" % key
                    return dumps({'error': message}), 500
            requested_attributes[attribute] = True

        if '_id' in request_json['fields']:
            requested_attributes['_id'] = True
        else:
            requested_attributes['_id'] = False
        ret_doc = g.client[schema['name']][grid['name']].find_one(query, fields=requested_attributes)
    else:
        ret_doc = g.client[schema['name']][grid['name']].find_one(query)

    if ret_doc is None:
        return dumps({})

    stringify_ids([ret_doc])
    return dumps(ret_doc)

@app.route('/grid/<schema_id>/<id>/_entry/create', methods=['POST'])
def create_entry(schema_id,id):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(schema_id)})
    if schema is None:
        error = "schema %s does not exist!" % schema_id
        return dumps({'error': error}), 500

    grid =  g.client[schema['name']]['grids'].find_one({'_id': ObjectId(id)})
    if grid is None:
        error = "grid %s does not exist!" % id
        return dumps({'error': error}), 500

    request_json = {}
    if request.data:
        request_json = loads(request.data)

    if 'document' not in request_json.keys():
        return dumps({'error': 'please supply a document to insert!'})

    document = request_json['document']
    for field in document.keys():
        if field not in grid['fields'].keys():
            error = "schema %s grid %s does not support field %s" % (schema['name'], grid['name'], field)
            return dumps({'error': error}), 500

    new_insert = g.client[schema['name']][grid['name']].insert(document)
    return dumps({'_id': str(new_insert)})

@app.route('/grid/<schema_id>/<id>/_entry/update', methods=['POST'])
def update_entry(schema_id,id):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(schema_id)})
    if schema is None:
        error = "schema %s does not exist!" % schema_id
        return dumps({'error': error}), 500

    grid =  g.client[schema['name']]['grids'].find_one({'_id': ObjectId(id)})
    if grid is None:
        error = "grid %s does not exist!" % id
        return dumps({'error': error}), 500

    request_json = {}
    if request.data:
        request_json = loads(request.data)

    if 'document' not in request_json.keys():
        return dumps({'error': 'This method updates a single entry with a supplied document hash of update and query.  please supply a document to update!'})
    
    document = request_json['document']
    if 'update' not in document.keys():
        return dumps({'error': 'please supply a document[update] update hash of attributes and values to update'}), 500

    if 'query' not in document.keys():
        return dumps({'error': 'please supply a document[query] hash of key value pairs to find the document to update'}), 500
        
    for attribute in document['update'].keys():
        if attribute not in grid['fields'].keys():
            return dumps({'error': 'schema %s grid %s does not support field %s' % (schema['name'], grid['name'], attribute)})

    for filter in document['query'].keys():
        if filter == '_id':
            document['query']['_id'] = ObjectId(document['query']['_id'])
        else:
            if not grid['fields'][filter]['is_filter']:
                error = "schema %s grid %s does not support filter %s" % (schema['name'], grid['name'], filter)
                return dumps({'error': error}), 500

    return dumps(g.client[schema['name']][grid['name']].update(document['query'],{'$set': document['update']}))

@app.route('/grid/<schema_id>/<id>/_entry/remove', methods=['POST'])
def remove_entry(schema_id,id):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(schema_id)})
    if schema is None:
        error = "schema %s does not exist!" % schema_id
        return dumps({'error': error}), 500

    grid =  g.client[schema['name']]['grids'].find_one({'_id': ObjectId(id)})
    if grid is None:
        error = "grid %s does not exist!" % id
        return dumps({'error': error}), 500

    request_json = {}
    if request.data:
        request_json = loads(request.data)

    query = None
    if '_id' not in request_json.keys():
        return dumps({'error': 'This method removes a single entry based on its objectid.  please supply a hash with key _id of the entry to remove'}), 500

    query = {'_id': ObjectId(request_json['_id']) }
    return dumps(g.client[schema['name']][grid['name']].remove(query))

# MULTI ENTRY REST
@app.route('/grid/<schema_id>/<id>/_entries', methods=['POST'])
def get_entries(schema_id,id):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(schema_id)})
    if schema is None:
        error = "schema %s does not exist!" % schema_id
        return dumps({'error': error}), 500

    grid =  g.client[schema['name']]['grids'].find_one({'_id': ObjectId(id)})
    if grid is None:
        error = "grid %s does not exist!" % id
        return dumps({'error': error}), 500

    request_json = {}
    if request.data:
        request_json = loads(request.data)

    query = None
    if 'query' in request_json.keys():
        for filter in request_json['query'].keys():
            if filter not in grid['fields'].keys():
                message = "%s is not a supported filter of this grid" % filter
                return dumps({'error': message}), 500
            if not grid['fields'][filter]['is_filter']:
                message = "%s is not a supported filter of this grid" % filter
                return jsonify({'error': message}), 500
        query = request_json['query']

    ret_doc = None
    if 'fields' in request_json.keys():
        requested_attributes = {}
        for attribute in request_json['fields']:
            if attribute != '_id':
                if attribute not in grid['fields'].keys():
                    message = "%s is not a supported attribute of this grid" % attribute
                    return dumps({'error': message}), 500
                if not grid['fields'][attribute]['is_attribute']:
                    message = "%s is not a supported attribute of this grid" % key
                    return dumps({'error': message}), 500
            requested_attributes[attribute] = True

        if '_id' in request_json['fields']:
            requested_attributes['_id'] = True
        else:
            requested_attributes['_id'] = False
        ret_doc = list(g.client[schema['name']][grid['name']].find(query, fields=requested_attributes, exhaust=True))
    else:
        ret_doc = list(g.client[schema['name']][grid['name']].find(query, exhaust=True))

    if ret_doc is None:
        return dumps({})

    stringify_ids(ret_doc)
    return dumps(ret_doc)

@app.route('/grid/<schema_id>/<id>/_entries/create', methods=['POST'])
def create_entries(schema_id,id):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(schema_id)})
    if schema is None:
        error = "schema %s does not exist!" % schema_id
        return dumps({'error': error}), 500

    grid =  g.client[schema['name']]['grids'].find_one({'_id': ObjectId(id)})
    if grid is None:
        error = "grid %s does not exist!" % id
        return dumps({'error': error}), 500

    request_json = {}
    if request.data:
        request_json = loads(request.data)

    if 'documents' not in request_json.keys():
        return dumps({'error': 'This method allows you to create multiple entries with a documents array.  please supply a document to insert!'}), 500

    documents = request_json['documents']
    for document in documents:
        for field in document.keys():
          if field not in grid['fields'].keys():
                error = "schema %s grid %s does not support field %s" % (schema['name'], grid['name'], field)
                return dumps({'error': error}), 500

    new_inserts = [ str(new_id) for new_id in g.client[schema['name']][grid['name']].insert(documents) ]
    return dumps(new_inserts)

@app.route('/grid/<schema_id>/<id>/_entries/update', methods=['POST'])
def update_entries(schema_id,id):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(schema_id)})
    if schema is None:
        error = "schema %s does not exist!" % schema_id
        return dumps({'error': error}), 500

    grid =  g.client[schema['name']]['grids'].find_one({'_id': ObjectId(id)})
    if grid is None:
        error = "grid %s does not exist!" % id
        return dumps({'error': error}), 500

    request_json = {}
    if request.data:
        request_json = loads(request.data)

    if 'document' not in request_json.keys():
        return dumps({'error': 'This method updates multiple entries with a supplied document hash of update and query. please supply a document to update!'}), 500
    
    document = request_json['document']
    if 'update' not in document.keys():
        return dumps({'error': 'please supply a document[update] hash of attributes and values to update'}), 500

    if 'query' not in document.keys():
        return dumps({'error': 'please supply a document[query] hash of key value pairs to find documents to update'}), 500
    
    for filter in document['query'].keys():
        if not grid['fields'][filter]['is_filter']:
            error = "schema %s grid %s does not support filter %s" % (schema['name'], grid['name'], filter)
            return dumps({'error': error}), 500
        
    for attribute in document['update'].keys():
        if attribute not in grid['fields'].keys():
            return dumps({'error': 'schema %s grid %s does not support attribute %s' % (schema['name'], grid['name'], attribute)})

    return dumps(g.client[schema['name']][grid['name']].update(document['query'],{'$set': document['update']}, multi=True))

@app.route('/grid/<schema_id>/<id>/_entries/remove', methods=['POST'])
def remove_entries(schema_id,id):
    schema = g.client[g.schema_db]['definitions'].find_one({'_id': ObjectId(schema_id)})
    if schema is None:
        error = "schema %s does not exist!" % schema_id
        return dumpsa({'error': error}), 500

    grid =  g.client[schema['name']]['grids'].find_one({'_id': ObjectId(id)})
    if grid is None:
        error = "grid %s does not exist!" % id
        return dumps({'error': error}), 500
    request_json = {}
    if request.data:
        request_json = json.loads(request.data)
    
    query = None
    if 'query' in request_json.keys():
        for filter in request_json['query'].keys():
            if filter == '_id':
                request_json['query']['_id'] = ObjectId(request_json['query']['_id'])
            else:
                if not grid['fields'][filter]['is_filter']:
                    error = "schema %s grid %s does not support filter %s" % (schema['name'], grid['name'], filter)
                    return dumps({'error': error}), 500
        query = request_json['query']
    else:
        if 'all' not in request_json.keys():
            return dumps({'error': 'This method removes multiple entries. Please supply a query with fields to filter removed entries, or {"all":"true"} to remove all entries'}), 500

    return dumps(g.client[schema['name']][grid['name']].remove(query))
