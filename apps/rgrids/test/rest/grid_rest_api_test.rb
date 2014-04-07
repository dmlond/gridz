require 'test_helper'
require_relative '../helpers/json_helpers'

class GridRestApiTest < ActiveSupport::TestCase
  include JsonHelpers

  def app
    GridRestApi
  end

  setup do
    @schema = create(:schema)
    @grid = @schema.grids.create(attributes_for(:grid))
    @grid_field = @grid.grid_fields.create([
                                            {name: 'foo', is_filterable: false},
                                            {name: 'bar', is_filterable: true},
                                            {name: 'baz', is_filterable: true }
                                           ])
    @db = Mongoid.session(:default)
    @new_document_attributes =  {foo: 'foo_value',baz: 3, bar: 'value baz'}
    @non_existent_entry_id = BSON::ObjectId.new
  end

  teardown do
    @db.with(database: @schema.name) do |_session|
      _session.drop
    end
    Mongoid.purge!
  end

  context 'grid/:schema_id/:id/_entry' do
    setup do
      @path = "/#{ @schema.id }/#{ @grid.id }/_entry"
      @db.with(database: @schema.name) do |_session|
        _session[@grid.name].insert(@new_document_attributes)
        @newly_inserted_doc = _session[@grid.name].find(@new_document_attributes).first
      end
    end

    should 'return JSON with error and status 500 when schema does not exist' do
      assert @schema.destroy, 'schema is destroyed'
      assert !Schema.where(_id: @schema.id).exists?, 'the schema should not exist'
      returned_doc = post_json @path, {}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "schema #{ @schema.id } does not exist!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when grid does not exist' do
      assert @grid.destroy, 'grid is destroyed'
      assert !Grid.where(_id: @grid.id).exists?, 'the grid should not exist'
      returned_doc = post_json @path, {document: @new_document_attributes}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "grid #{ @grid.id } does not exist in schema #{ @schema.id }!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when body is nil' do
      returned_doc = post_json @path
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply application/json contentType data!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when request content_type is not application/json' do
      post(@path, { _id: @newly_inserted_doc['_id'].to_s }.to_json)
      rbody = last_response.body
      returned_doc = JSON.parse(rbody)
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply application/json contentType data!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when submitted JSON does not have either an _id or query key' do
      returned_doc = post_json @path, {}
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply either an _id key with ObjectID string value, or a query key and valid query hash as value", returned_doc['error']
    end

    should 'return empty hash JSON when supplied _id key and non-existent entry ObjectID string value JSON' do
      returned_doc = post_json @path, { _id: @non_existent_entry_id.to_s }
      assert_not_nil returned_doc
      assert returned_doc.keys.empty?, 'there should not be any keys in the returned document'
    end

    should 'return entry JSON when supplied _id key and existing entry ObjectID string value JSON' do
      returned_doc = post_json @path, { _id: @newly_inserted_doc['_id'].to_s }
      assert_not_nil returned_doc
      assert_equal @newly_inserted_doc['_id'].to_s, returned_doc['_id']
      @newly_inserted_doc.keys.reject{|k| k == '_id' }.each do |key|
        assert returned_doc.keys.include? key
        assert_equal @newly_inserted_doc[key], returned_doc[key]
      end
    end

    should 'return entry JSON when supplied query key and valid JSON query hash value JSON' do
      this_query = {bar: @newly_inserted_doc[:bar]}
      assert_equal 1, @db.with(database: @schema.name)[@grid.name].find(this_query).count
      returned_doc = post_json @path, { query: this_query }
      assert_not_nil returned_doc
      assert_equal @newly_inserted_doc['_id'].to_s, returned_doc['_id']
      @newly_inserted_doc.keys.reject{|k| k == '_id' }.each do |key|
        assert returned_doc.keys.include? key
        assert_equal @newly_inserted_doc[key], returned_doc[key]
      end
    end

    should 'return empty hash JSON when supplied query key and valid JSON query hash that does not return an entry' do
      this_query = {bar: 'does not exist'}
      assert_equal 0, @db.with(database: @schema.name)[@grid.name].find(this_query).count
      returned_doc = post_json @path, { query: this_query }
      assert_not_nil returned_doc
      assert returned_doc.keys.empty?, 'there should not be any keys in the returned document'
    end

    should 'return json with error and status 500 when a query JSON includes a field that is not filterable' do
      this_query = {foo: @newly_inserted_doc[:foo]}
      assert !@grid.grid_fields.where(name: 'foo').first.is_filterable?, 'foo should not be filterable'
      returned_doc = post_json @path, { query: this_query }
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "field foo is not a valid filter for grid #{ @grid.name }", returned_doc['error']
    end

    should 'support _id json request with fields key and array of attributes as values to request only certain fields in the response' do
      requested_fields = ['foo','baz']
      returned_doc = post_json @path, { _id: @newly_inserted_doc['_id'].to_s, fields: requested_fields }
      assert_not_nil returned_doc
      assert_equal @newly_inserted_doc['_id'].to_s, returned_doc['_id']
      requested_fields.reject{|k| k == '_id' }.each do |rf|
        assert returned_doc.keys.include?(rf), "#{ rf } should be in the fields returned" 
        assert_equal @newly_inserted_doc[rf], returned_doc[rf]
      end
      assert !returned_doc.keys.include?('bar'), "bar should not be in the fields returned in #{ returned_doc.to_json }"
    end

    should 'support query json request with fields key and array of attributes as values to request only certain fields in the response' do
      requested_fields = ['_id','bar']
      this_query = {baz: @newly_inserted_doc[:baz]}
      returned_doc = post_json @path, { query: this_query, fields: requested_fields }
      assert_not_nil returned_doc
      assert_equal @newly_inserted_doc['_id'].to_s, returned_doc['_id']
      requested_fields.reject{|k| k == '_id' }.each do |rf|
        assert returned_doc.keys.include?(rf), "#{ rf } should be in the fields returned" 
        assert_equal @newly_inserted_doc[rf], returned_doc[rf]
      end
      ['foo','baz'].each do |nrf|
        assert !returned_doc.keys.include?(nrf), "#{ nrf } should not be in the fields returned"
      end
    end
  end #grid/:schema_id/:id/_entry

  context 'grid/:schema_id/:id/_entry/create' do
    setup do
      @path = "/#{ @schema.id }/#{ @grid.id }/_entry/create"
    end

    should 'return JSON with error and status 500 when schema does not exist' do
      assert @schema.destroy, 'schema is destroyed'
      assert !Schema.where(_id: @schema.id).exists?, 'the schema should not exist'
      returned_doc = post_json @path, {document: @new_document_attributes}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "schema #{ @schema.id } does not exist!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when grid does not exist' do
      assert @grid.destroy, 'grid is destroyed'
      assert !Grid.where(_id: @grid.id).exists?, 'the grid should not exist'
      returned_doc = post_json @path, {}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "grid #{ @grid.id } does not exist in schema #{ @schema.id }!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when body is nil' do
      returned_doc = post_json @path
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply application/json contentType data!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when request content_type is not application/json' do
      post(@path, {document: @new_document_attributes}.to_json)
      rbody = last_response.body
      returned_doc = JSON.parse(rbody)
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply application/json contentType data!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when there is not a document key in the request JSON' do
      returned_doc = post_json @path, {}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply a document key, and hash value containing the entry to be created!", returned_doc['error']
    end

    should 'accept document key, and new document to create according to grid definition' do
      returned_doc = post_json @path, {document: @new_document_attributes}
      assert_not_nil returned_doc
      assert returned_doc.keys.include? '_id'
      @db.with(database: @schema.name) do |_session|
        @newly_created_doc = _session[@grid.name].find(_id: BSON::ObjectId.from_string(returned_doc['_id'])).one
      end
      assert_equal returned_doc['_id'], @newly_created_doc['_id'].to_s
      @new_document_attributes.keys.each do |k|
        assert_equal @new_document_attributes[k], @newly_created_doc[k]
      end
    end

    should 'return JSON with error and status 500 when document contains fields that are not defined for the grid' do
      field_not_there = 'notthereatall'
      @new_document_attributes[field_not_there] = "This should not be there."
      returned_doc = post_json @path, {document: @new_document_attributes}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "field #{ field_not_there } is not defined for schema #{ @schema.id } grid #{ @grid.id }!", returned_doc['error']
    end
  end #grid/:schema_id/:id/_entry/create

  context 'grid/:schema_id/:id/_entry/update' do
    setup do
      @path = "#{ @schema.id }/#{ @grid.id }/_entry/update"
      @db.with(database: @schema.name) do |_session|
        _session[@grid.name].insert(@new_document_attributes)
        @doc_to_update = _session[@grid.name].find(@new_document_attributes).first
      end
      @new_baz_value = 'a new baz value'
    end

    should 'return JSON with error and status 500 when schema does not exist' do
      assert @schema.destroy, 'schema is destroyed'
      assert !Schema.where(_id: @schema.id).exists?, 'the schema should not exist'
      returned_doc = post_json @path, {}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "schema #{ @schema.id } does not exist!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when grid does not exist' do
      assert @grid.destroy, 'grid is destroyed'
      assert !Grid.where(_id: @grid.id).exists?, 'the grid should not exist'
      returned_doc = post_json @path, {}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "grid #{ @grid.id } does not exist in schema #{ @schema.id }!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when body is nil' do
      returned_doc = post_json @path
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply application/json contentType data!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when request content_type is not application/json' do
      post(@path, {}.to_json)
      rbody = last_response.body
      returned_doc = JSON.parse(rbody)
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply application/json contentType data!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when request does not include a query key with a query to find the document to update' do
      returned_doc = post_json @path, {update: {baz: @new_baz_value}}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply an query key with hash of conditions to match to find the entry to update", returned_doc['error']
    end

    should 'return JSON with error and status 500 when request does not include an update key with the update fields' do
      returned_doc = post_json @path, {query: {_id: @doc_to_update['_id'].to_s}}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply an update key and hash of field, values to update on the queried entry", returned_doc['error']
    end

    should 'return status hash when a valid query and update are sent to update an existing entry' do
      assert_equal 1, @db.with(database: @schema.name)[@grid.name].find({_id: @doc_to_update['_id']}).count
      returned_doc = post_json @path, {query: {_id: @doc_to_update['_id'].to_s}, update: {baz: @new_baz_value}}
      assert_not_nil returned_doc
      assert returned_doc['updatedExisting'], 'updatedExisting should be true'
      assert_equal 1, returned_doc['n']
      just_updated_doc = @db.with(database: @schema.name)[@grid.name].find({_id: @doc_to_update['_id']}).one
      assert_equal @new_baz_value, just_updated_doc['baz']
    end

    should 'return status hash when a valid query and update are sent to update an non-existent entry' do
      assert_equal 0, @db.with(database: @schema.name)[@grid.name].find({_id: @non_existent_entry_id}).count
      returned_doc = post_json @path, {query: {_id: @non_existent_entry_id.to_s}, update: {baz: @new_baz_value}}
      assert_not_nil returned_doc
      assert !returned_doc['updatedExisting'], 'updatedExisting should be false'
      assert_equal 0, returned_doc['n']
    end
  end #grid/:schema_id/:id/_entry/update

  context "grid/:schema_id/:id/_entry/remove" do
    setup do
      @path = "#{ @schema.id }/#{ @grid.id }/_entry/remove"
      @db.with(database: @schema.name) do |_session|
        _session[@grid.name].insert(@new_document_attributes)
        @doc_to_remove = _session[@grid.name].find(@new_document_attributes).first
      end
    end

    should 'return JSON with error and status 500 when schema does not exist' do
      assert @schema.destroy, 'schema is destroyed'
      assert !Schema.where(_id: @schema.id).exists?, 'the schema should not exist'
      returned_doc = post_json @path, {}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "schema #{ @schema.id } does not exist!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when grid does not exist' do
      assert @grid.destroy, 'grid is destroyed'
      assert !Grid.where(_id: @grid.id).exists?, 'the grid should not exist'
      returned_doc = post_json @path, {}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "grid #{ @grid.id } does not exist in schema #{ @schema.id }!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when body is nil' do
      returned_doc = post_json @path
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply application/json contentType data!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when request content_type is not application/json' do
      post(@path, {}.to_json)
      rbody = last_response.body
      returned_doc = JSON.parse(rbody)
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply application/json contentType data!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when request does not include an _id key and ObjectId string value' do
      returned_doc = post_json @path, {}
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply an _id key and ObjectId string for the entry to remove!", returned_doc['error']
    end

    should 'return status hash when provided an _id key and ObjectId string value for an existing entry' do
      assert_equal 1, @db.with(database: @schema.name)[@grid.name].find({_id: @doc_to_remove['_id']}).count
      returned_doc = post_json @path, {_id: @doc_to_remove['_id'].to_s}
      assert_not_nil returned_doc
      assert_equal 1, returned_doc['n']
    end

    should 'return status hash when provided an _id key and ObjectId string value for a non-existent entry' do
      assert_equal 0, @db.with(database: @schema.name)[@grid.name].find({_id: @non_existent_entry_id}).count
      returned_doc = post_json @path, {_id: @non_existent_entry_id.to_s}
      assert_not_nil returned_doc
      assert_equal 0, returned_doc['n']
    end
  end #grid/:schema_id/:id/_entry/remove

  context 'grid/:schema_id/:id/_entries' do
    setup do
      @path = "/#{ @schema.id }/#{ @grid.id }/_entries"
      @new_documents_attributes = []
      (1..10).each do |i|
        @new_documents_attributes << {foo: "foo_value_#{ i }",baz: i, bar: "value baz #{ i }"}
      end
      @db.with(database: @schema.name) do |_session|
        _session[@grid.name].insert(@new_documents_attributes)
        @newly_inserted_docs = _session[@grid.name].find(@new_document_attributes).entries
      end
    end

    should 'return JSON with error and status 500 when schema does not exist' do
      assert @schema.destroy, 'schema is destroyed'
      assert !Schema.where(_id: @schema.id).exists?, 'the schema should not exist'
      returned_doc = post_json @path, {}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "schema #{ @schema.id } does not exist!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when grid does not exist' do
      assert @grid.destroy, 'grid is destroyed'
      assert !Grid.where(_id: @grid.id).exists?, 'the grid should not exist'
      returned_doc = post_json @path, {document: @new_document_attributes}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "grid #{ @grid.id } does not exist in schema #{ @schema.id }!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when body is nil' do
      returned_doc = post_json @path
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply application/json contentType data!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when request content_type is not application/json' do
      post(@path, { _id: @newly_inserted_doc['_id'].to_s }.to_json)
      rbody = last_response.body
      returned_doc = JSON.parse(rbody)
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply application/json contentType data!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when request JSON does not contain a query hash' do
      assert false, 'implement'
    end

    should 'return JSON with error and status 500 when request JSON query hash contains non filterable fields' do
      assert false, 'implement'
    end

    should 'return a list of entries when request JSON contains a query hash that matches entries' do
      assert false, 'implement'
    end

    should 'return a list of entries with _id and defined fields when request JSON query hash matches documents and contains a fields array' do
      assert false, 'implement'
    end

    should 'return a list of entries with just the _id when request JSON query hash matches documents and contains id_only true' do
      assert false, 'implement'
    end

    should 'return a list of all entries when query equals all' do
      assert false, 'implement'
    end

    should 'return a list of all entries with _id and defined fields' do
      assert false, 'implement'
    end

    should 'return a list of all entries with just the _id field' do
      assert false, 'implement'
    end

    should 'return JSON with error and status 500 when fields list contains fields undefined for the schema and grid' do
      assert false, 'implement'
    end
  end #grid/:schema_id/:id/_entries


  context 'grid/:schema_id/:id/_entries/create' do
    setup do
      @path = "/#{ @schema.id }/#{ @grid.id }/_entries"
      @new_documents_attributes = []
      (1..10).each do |i|
        @new_documents_attributes << {foo: "foo_value_#{ i }",baz: i, bar: "value baz #{ i }"}
      end
    end

    should 'return JSON with error and status 500 when schema does not exist' do
      assert @schema.destroy, 'schema is destroyed'
      assert !Schema.where(_id: @schema.id).exists?, 'the schema should not exist'
      returned_doc = post_json @path, {}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "schema #{ @schema.id } does not exist!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when grid does not exist' do
      assert @grid.destroy, 'grid is destroyed'
      assert !Grid.where(_id: @grid.id).exists?, 'the grid should not exist'
      returned_doc = post_json @path, {document: @new_document_attributes}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "grid #{ @grid.id } does not exist in schema #{ @schema.id }!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when body is nil' do
      returned_doc = post_json @path
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply application/json contentType data!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when request content_type is not application/json' do
      post(@path, { _id: @newly_inserted_doc['_id'].to_s }.to_json)
      rbody = last_response.body
      returned_doc = JSON.parse(rbody)
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply application/json contentType data!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when request JSON does not contain a documents key' do
      assert false, 'implement'
    end

    should 'return JSON with error and status 500 when request JSON documents contain undefined fields for the grid and schema' do
      assert false, 'implement'
    end

    should 'return a status JSON when request JSON contains a docuemnts key and array of new documents' do
      assert false, 'implement'
    end
  end #grid/:schema_id/:id/_entries/create

  context 'grid/:schema_id/:id/_entries/remove' do
    setup do
      @path = "/#{ @schema.id }/#{ @grid.id }/_entries"
      @new_documents_attributes = []
      (1..10).each do |i|
        @new_documents_attributes << {foo: "foo_value_#{ i }",baz: i, bar: "value baz #{ i }"}
      end
      @db.with(database: @schema.name) do |_session|
        _session[@grid.name].insert(@new_documents_attributes)
        @newly_inserted_docs = _session[@grid.name].find(@new_document_attributes).entries
      end
    end

    should 'return JSON with error and status 500 when schema does not exist' do
      assert @schema.destroy, 'schema is destroyed'
      assert !Schema.where(_id: @schema.id).exists?, 'the schema should not exist'
      returned_doc = post_json @path, {}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "schema #{ @schema.id } does not exist!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when grid does not exist' do
      assert @grid.destroy, 'grid is destroyed'
      assert !Grid.where(_id: @grid.id).exists?, 'the grid should not exist'
      returned_doc = post_json @path, {document: @new_document_attributes}
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "grid #{ @grid.id } does not exist in schema #{ @schema.id }!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when body is nil' do
      returned_doc = post_json @path
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply application/json contentType data!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when request content_type is not application/json' do
      post(@path, { _id: @newly_inserted_doc['_id'].to_s }.to_json)
      rbody = last_response.body
      returned_doc = JSON.parse(rbody)
      assert_not_nil returned_doc
      assert_equal 500, last_response.status
      assert_not_nil returned_doc
      assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
      assert_equal "please supply application/json contentType data!", returned_doc['error']
    end

    should 'return JSON with error and status 500 when request JSON does not contain a query hash' do
      assert false, 'implement'
    end

    should 'return JSON with error and status 500 when request JSON query hash contains non filterable fields' do
      assert false, 'implement'
    end

    should 'return a status JSON and remove entries when request JSON contains a query hash that matches entries' do
      assert false, 'implement'
    end

    should 'return a status JSON and remove all entries when query equals all' do
      assert false, 'implement'
    end
  end #grid/:schema_id/:id/_entries/remove
end
