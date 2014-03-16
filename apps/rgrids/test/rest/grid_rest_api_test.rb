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

    should 'succeed with _id key ObjectID value JSON' do
      returned_doc = post_json @path, { _id: @newly_inserted_doc['_id'].to_s }
      assert_not_nil returned_doc
      assert_equal @newly_inserted_doc['_id'].to_s, returned_doc['_id']
      @newly_inserted_doc.keys.reject{|k| k == '_id' }.each do |key|
        assert returned_doc.keys.include? key
        assert_equal @newly_inserted_doc[key], returned_doc[key]
      end
    end

    should 'succeed with query key and valid JSON query hash value JSON' do
      this_query = {bar: @newly_inserted_doc[:bar]}
      returned_doc = post_json @path, { query: this_query }
      assert_not_nil returned_doc
      assert_equal @newly_inserted_doc['_id'].to_s, returned_doc['_id']
      @newly_inserted_doc.keys.reject{|k| k == '_id' }.each do |key|
        assert returned_doc.keys.include? key
        assert_equal @newly_inserted_doc[key], returned_doc[key]
      end
    end

    should 'return json with error and status 500 when a query JSON includes a field that is not filterable' do
      this_query = {foo: @newly_inserted_doc[:foo]}
      assert !@grid.grid_fields.where(name: 'foo').first.is_filterable?, 'foo should not be filterable'
      begin
        returned_doc = post_json @path, { query: this_query }
        assert_not_nil returned_doc
        assert_equal 500, last_response.status
        assert_not_nil returned_doc
        assert returned_doc.keys.include?('error'), 'there should be an error in the returned json hash'
        assert_equal "field foo is not a valid filter for grid #{ @grid.name }", returned_doc['error']
      rescue JSON::ParserError
        assert false, "ERROR WITH RETURNED JSON #{ last_response.body }"
      end
    end

    should 'support _id json request with fields key and array of attributes as values to request only certain fields in the response' do
      requested_fields = ['foo','baz']
      begin
        returned_doc = post_json @path, { _id: @newly_inserted_doc['_id'].to_s, fields: requested_fields }
        assert_not_nil returned_doc
        assert_equal @newly_inserted_doc['_id'].to_s, returned_doc['_id']
        requested_fields.reject{|k| k == '_id' }.each do |rf|
          assert returned_doc.keys.include?(rf), "#{ rf } should be in the fields returned" 
          assert_equal @newly_inserted_doc[rf], returned_doc[rf]
        end
        assert !returned_doc.keys.include?('bar'), "bar should not be in the fields returned in #{ returned_doc.to_json }"
      rescue JSON::ParserError
        assert false, "ERROR WITH RETURNED JSON #{ last_response.body }"
      end
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
  end
end
