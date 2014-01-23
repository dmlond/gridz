import os
import app
import unittest
import tempfile
from pyquery import PyQuery as pq
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import dumps, loads

class GridzTestCase(unittest.TestCase):

    def insert_schema(self):
        return str(self.client['testing_schemas']['definitions'].insert({'name': self.test_name, 'description': self.test_description}))

    def insert_grid(self):
        new_grid = {
            'name': self.test_grid_name,
            'description': self.test_grid_description,
            'fields': self.grid_fields
        }
        return str(self.client[self.test_name]['grids'].insert(new_grid))

    def setUp(self):
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()
        self.test_name = "NEW_SCHEMA"
        self.test_description = "THIS IS A NEW SCHEMA"
        self.test_grid_name = "NEW_GRID"
        self.grid_fields =  {
            'foo': { 'is_attribute': True, 'is_filter': False },
            'bar': { 'is_attribute': True, 'is_filter': False},
            'baz': { 'is_attribute': False, 'is_filter': True }
        }
        self.test_grid_description = "THIS IS A NEW GRID"
        self.client = MongoClient()
        self.not_there = '52b85fb0e4ba084049f4f9db'
        
    def tearDown(self):
        self.client['testing_schemas']['definitions'].remove()
        self.client['testing_schemas'].drop_collection('definitions')
        self.client[self.test_name]['grids'].remove()
        self.client[self.test_name].drop_collection('grids')
        self.client[self.test_name][self.test_grid_name].remove()
        self.client[self.test_name].drop_collection(self.test_grid_name)
        self.client.drop_database(self.test_name)
        self.client.drop_database('testing_schemas')

    def test_schemas(self):
        new_id = self.insert_schema()
        rv = self.app.get('/')
        self.assertNotEqual(rv.data, None, 'its None!')
        assert '<title>Gridz</title>' in rv.data
        assert self.test_name in rv.data
        assert self.test_description in rv.data

        rv = self.app.get('/schemas')
        self.assertNotEqual(rv.data, None, 'its None!')
        assert '<title>Gridz</title>' in rv.data
        assert self.test_name in rv.data
        assert self.test_description in rv.data

        rv = self.app.get('/schemas/json')
        schemas = loads(rv.data)
        self.assertEqual(1, len(schemas))
        schema = schemas[0]
        self.assertEqual(ObjectId(new_id), schema['_id'])
        self.assertEqual(self.test_name, schema['name'])
        self.assertEqual(self.test_description, schema['description'])

    def test_schema(self):
        new_id = self.insert_schema()
        path = "/schema/%s" % new_id
        rv = self.app.get(path)
        assert self.test_name in rv.data
        assert self.test_description in rv.data
        assert "%s/destroy" % path in rv.data

    def test_schema_new(self):
       rv = self.app.get('/schema/new')
       assert 'Name' in rv.data
       assert 'Description' in rv.data

    def test_create_schema(self):
        self.app.post('/schema/create', data=dict(
            name=self.test_name,
            description=self.test_description
            ), follow_redirects=True)        
        count = self.client['testing_schemas']['definitions'].find({'name': self.test_name, 'description': self.test_description}).count()
        self.assertEqual(1, count)

    def test_destroy_schema(self):
        new_id = self.insert_schema()
        path = "/schema/%s/destroy" % new_id
        rv = self.app.get(path,follow_redirects=True)
        count = self.client['testing_schemas']['definitions'].find({'name': self.test_name, 'description': self.test_description}).count()
        self.assertEqual(0, count)
        
    def test_gridz(self):
        schema_id = self.insert_schema()
        grid_id = self.insert_grid()

        path = '/gridz/%s' % schema_id
        rv = self.app.get(path)
        assert self.test_name in rv.data
        assert self.test_grid_name in rv.data
        assert self.test_grid_description in rv.data

        path = '/gridz/%s/json' % schema_id
        rv = self.app.get(path)
        gridz = loads(rv.data)
        assert self.test_name in gridz.keys()
        self.assertEqual(1, len(gridz[self.test_name]))
        self.assertEqual(ObjectId(grid_id), gridz[self.test_name][0]['_id'])
        self.assertEqual(self.test_grid_name, gridz[self.test_name][0]['name'])
        self.assertEqual(self.test_grid_description, gridz[self.test_name][0]['description'])
        
    def test_grid(self):
        schema_id = self.insert_schema()
        grid_id = self.insert_grid()

        path = '/grid/%s/%s' % (schema_id,grid_id)
        rv = self.app.get(path)
        assert self.test_name in rv.data
        assert self.test_grid_name in rv.data
        assert self.test_grid_description in rv.data
        jq = pq(rv.data)
        for grid_field in self.grid_fields.keys():
            if self.grid_fields[grid_field]['is_attribute']:
                assert grid_field in jq("#attributes").html()
            if self.grid_fields[grid_field]['is_filter']:
                assert grid_field in jq("#filters").html()

    def test_new_grid(self):
        schema_id = self.insert_schema()
        path = '/grid/%s/new' % (schema_id,)
        rv = self.app.get(path)
        jq = pq(rv.data)
        assert jq.is_('#grid_name_input')
        assert jq.is_('#grid_description_input')
        assert jq.is_('ul#grid_fields')

    def test_create_grid(self):
        schema_id = self.insert_schema()
        path = '/grid/%s/create' % (schema_id,)
        # post data does NOT support passing dict of dict, it thinks it is a file descriptor!!!
#        grid_form_fields = [
#            {'is_queryable_by': ['filter', 'attribute'], 'name': 'foo'},
#            {'is_queryable_by': ['attribute'], 'name': 'bar'}
#        ]
        self.app.post(path, data={
            'name':self.test_grid_name,
            'description':self.test_grid_description
#            'grid_form_fields': grid_form_fields
            }, follow_redirects=True)
        count = self.client[self.test_name]['grids'].find({'name': self.test_grid_name, 'description': self.test_grid_description}).count()
        self.assertEqual(1, count)
#        for grid_form_field in grid_form_fields:
#            grid_select = [grid_form_field['name']]
#            is_filter = 0
#            if 'filter' in grid_form_field['is_queryable_by']:
#                is_filter = 1
#            grid_select.append(is_filter)
#            is_attribute = 0
#            if 'attribute' in grid_form_field['is_queryable_by']:
#                is_attribute = 1
#            grid_select.append(is_attribute)
#            cur = self.db.execute('select count(*) from grid_fields where name = ? and is_filter = ? an is_attribute = ?', grid_select)
#            row = cur.fetchone()
#            count = row[0]
#            self.assertEqual(1, count)

    def test_destroy_grid(self):
        schema_id = self.insert_schema()
        grid_id = self.insert_grid()
        path = "/grid/%s/%s/destroy" % (schema_id,grid_id)
        rv = self.app.get(path,follow_redirects=True)
        count = self.client[self.test_name]['grids'].find({'name': self.test_grid_name, 'description': self.test_grid_description}).count()
        self.assertEqual(0, count)

    #REST
    def test_create_grid_entry(self):
        path = "/grid/%s/%s/_entry/create" % (self.not_there,self.not_there)
        rv = self.app.post(path, content_type = 'application/json', data = dumps({}))
        resp = loads(rv.data)
        expected_message = "schema %s does not exist!" % self.not_there
        self.assertEqual(expected_message, resp['error'])

        schema_id = self.insert_schema()
        path = "/grid/%s/%s/_entry/create" % (schema_id,self.not_there)
        rv = self.app.post(path, data = dumps({}))
        resp = loads(rv.data)
        expected_message = "grid %s does not exist!" % self.not_there
        self.assertEqual(expected_message, resp['error'])

        grid_id = self.insert_grid()
        path = "/grid/%s/%s/_entry/create" % (schema_id,grid_id)
        rv = self.app.post(path, data = dumps({}))
        resp = loads(rv.data)
        expected_message = "please supply a document to insert!"
        self.assertEqual(expected_message, resp['error'])

        document = {'document': {'foo': 'foo_value','bar': 3, 'baz': 'value baz'}}
        rv = self.app.post(path, data = dumps(document))
        resp_doc = loads(rv.data)
        assert '_id' in resp_doc.keys()
        new_id = resp_doc['_id']
        self.assertEqual(1, self.client[self.test_name][self.test_grid_name].find({'_id': ObjectId(new_id)}).count())
        new_doc = self.client[self.test_name][self.test_grid_name].find_one({'_id': ObjectId(new_id)})
        for key in document['document'].keys():
            self.assertEqual(document['document'][key], new_doc[key])

    def test_get_entry(self):
        schema_id = self.insert_schema()
        grid_id = self.insert_grid()
        new_document = {'foo': 'foo_value','baz': 3, 'bar': 'value baz'}
        new_id = self.client[self.test_name][self.test_grid_name].insert(new_document)
        
        path = "/grid/%s/%s/_entry" % (schema_id,grid_id)
        rv = self.app.post(path, data=dumps({}))
        resp = loads(rv.data)
        expected_message = 'please supply either a document ID with the _id key, or a query!'
        self.assertEqual(expected_message, resp['error'])

        self.assertEqual(0, self.client[self.test_name][self.test_grid_name].find({'_id': ObjectId(self.not_there)}).count())
        rv = self.app.post(path, data=dumps({'_id': self.not_there }))
        resp_doc = loads(rv.data)
        self.assertEqual({}, resp_doc)
    
        rv = self.app.post(path, data=dumps({'_id': str(new_id)}))
        resp_doc = loads(rv.data)
        for key in new_document.keys():
            assert key in resp_doc.keys()
            self.assertEqual(str(new_document[key]), str(resp_doc[key]))

        bad_fields = ['not_in_fields']
        rv = self.app.post(path, data=dumps({'_id': str(new_id), 'fields': bad_fields}))
        resp = loads(rv.data)
        expected_message = "%s is not a supported attribute of this grid" % bad_fields[0]
        self.assertEqual(expected_message, resp['error'])
        
        fields = ['foo','bar']
        rv = self.app.post(path, data=dumps({'_id': str(new_id), 'fields': fields}))
        resp_doc = loads(rv.data)
        for key in new_document.keys():
            if key in fields:
                assert key in resp_doc.keys()
                self.assertEqual(new_document[key], resp_doc[key])
            else:
                assert key not in resp_doc.keys()

        query = {'baz': {'$gt': 2}}
        rv = self.app.post(path, data=dumps({'query': query}))
        resp_doc = loads(rv.data)
        for key in new_document.keys():
            assert key in resp_doc.keys()
            self.assertEqual(str(new_document[key]), str(resp_doc[key]))

        rv = self.app.post(path, data=dumps({'query': query, 'fields': fields}))
        resp_doc = loads(rv.data)
        for key in new_document.keys():
            if key in fields:
                assert key in resp_doc.keys()
                self.assertEqual(str(new_document[key]), str(resp_doc[key]))
            else:
                assert key not in resp_doc.keys()

if __name__ == '__main__':
    unittest.main()
