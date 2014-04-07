require 'sinatra'
require 'json'

class GridRestApi < Sinatra::Application
  before do
    unless request.content_type == 'application/json'
      halt 500, { error:  "please supply application/json contentType data!"}.to_json
    end
    @db = Mongoid.session(:default)
  end

  before '/:schema_id/:id/_entry*' do
    begin
      @schema = Schema.find(params[:schema_id])
    rescue Mongoid::Errors::DocumentNotFound
      halt 500, { error: "schema #{ params[:schema_id] } does not exist!" }.to_json
    end

    begin
      @grid = Grid.find(params[:id])
    rescue Mongoid::Errors::DocumentNotFound
      halt 500, {error: "grid #{ params[:id] } does not exist in schema #{ @schema.id }!"}.to_json
    end
    rbody = request.body.read
    if rbody.nil? || rbody.empty?
      halt 500, {error:  "please supply application/json contentType data!"}.to_json
    end
  end

  helpers do
    def stringify_ids(docs)
      docs.each do |doc|
        doc['_id'] = doc['_id'].to_s
      end
    end

    def contains_nonqueryable_field?(query_fields)
      queryable_fields = @grid.grid_fields.where(is_filterable: true).collect{ |gf| gf.name }
      queryable_fields << '_id'
      query_fields.keys.each do |qf|
        unless queryable_fields.include?(qf)
          halt 500, {error: "field #{ qf } is not a valid filter for grid #{ @grid.name }" }.to_json
        end
      end
    end

    def contains_undefined_field?(fields)
      grid_fields = @grid.grid_fields.collect{|gf| gf.name }
      fields.keys.each do |_field|
        unless grid_fields.include? _field
          halt 500, {error: "field #{ _field } is not defined for schema #{ @schema.id } grid #{ @grid.id }!"}.to_json
        end
      end
    end

    def selected_fields(field_list)
      selected_fields = {}
      field_list.each do |f|
        selected_fields[f] = 1
      end
      selected_fields
    end
  end

  post '/:schema_id/:id/_entry' do
    content_type :json
    request.body.rewind  # in case someone already read it
    rbody = request.body.read
    request_json = JSON.parse(rbody)
    current_doc = nil
    if request_json['_id']
      @db.with(database: @schema.name) do |_session|
        current_doc = _session[@grid.name].find(_id: BSON::ObjectId.from_string(request_json['_id']))
      end
    elsif request_json['query']
      contains_nonqueryable_field? request_json['query']
      @db.with(database: @schema.name) do |_session|
        current_doc = _session[@grid.name].find(request_json['query'])
      end
    else
      halt 500, {error: "please supply either an _id key with ObjectID string value, or a query key and valid query hash as value"}.to_json
    end

    if request_json.include? 'fields'
      current_doc.select(selected_fields(request_json['fields']))
    end
    requested_entry = current_doc.one
    if requested_entry.nil?
      return {}.to_json
    end
    stringify_ids [requested_entry]
    return requested_entry.to_json
  end

  post '/:schema_id/:id/_entry/create' do
    content_type :json
    request.body.rewind  # in case someone already read it
    rbody = request.body.read
    request_json = JSON.parse(rbody)
    document = request_json['document']
    if document.nil?
      halt 500, {error: "please supply a document key, and hash value containing the entry to be created!"}.to_json
    end
    contains_undefined_field? document

    document['_id'] = BSON::ObjectId.new
    response = nil
    @db.with(database: @schema.name) do |_session|
      begin
        response = _session[@grid.name].insert(document)
      rescue Moped::Errors::SocketError
        response = _session[@grid.name].find(_id: document['_id']).upsert(document)
      end
    end
    body = {_id: document['_id'].to_s}.to_json
  end

  post '/:schema_id/:id/_entry/update' do
    content_type :json
    request.body.rewind  # in case someone already read it
    rbody = request.body.read
    request_json = JSON.parse(rbody)

    query = request_json['query']
    if query.nil?
      halt 500, {error: "please supply an query key with hash of conditions to match to find the entry to update"}.to_json
    end
    contains_nonqueryable_field? query
    if query.include? '_id'
      query['_id'] = BSON::ObjectId.from_string(query['_id'])
    end
    update = request_json['update']
    if update.nil?
      halt 500, {error: "please supply an update key and hash of field, values to update on the queried entry"}.to_json
    end
    contains_undefined_field? update

    response = nil
    @db.with(database: @schema.name) do |_session|
      response = _session[@grid.name].find(query).update(update)
    end
    body = response.to_json
  end

  post '/:schema_id/:id/_entry/remove' do
    content_type :json
    request.body.rewind  # in case someone already read it
    rbody = request.body.read
    request_json = JSON.parse(rbody)

    if request_json.keys.include? '_id'
      response = nil
      @db.with(database: @schema.name) do |_session|
        response = _session[@grid.name].find(_id: BSON::ObjectId.from_string(request_json['_id'])).remove
      end
      body = response.to_json
    else
      halt 500, {error: "please supply an _id key and ObjectId string for the entry to remove!"}.to_json
    end
  end
end
