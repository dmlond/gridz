require 'sinatra'
require 'json'

class GridRestApi < Sinatra::Application
  before do
    @db = Mongoid.session(:default)
  end

  helpers do
    def stringify_ids(docs)
      docs.each do |doc|
        doc['_id'] = doc['_id'].to_s
      end
    end
  end

  post '/:schema_id/:id/_entry' do
    unless request.content_type == 'application/json'
      status 500
      return body = { error:  "please supply application/json contentType data!"}.to_json
    end

    content_type :json
    begin
      @schema = Schema.find(params[:schema_id])
    rescue Mongoid::Errors::DocumentNotFound
      status 500
      return body = { error: "schema #{ params[:schema_id] } does not exist!" }.to_json
    end

    begin
      @grid = Grid.find(params[:id])
    rescue Mongoid::Errors::DocumentNotFound
      status 500
      return body = {error: "grid #{ params[:id] } does not exist in schema #{ @schema.id }!"}.to_json
    end

    request.body.rewind  # in case someone already read it
    rbody = request.body.read
    if rbody.nil? || rbody.empty?
      status 500
      body = {error:  "please supply application/json contentType data!"}.to_json
    else
      request_json = JSON.parse(rbody)
      queryable_fields = @grid.grid_fields.where(is_filterable: true).collect{ |gf| gf.name }
      current_doc = nil
      if request_json['_id']
        @db.with(database: @schema.name) do |_session|
          current_doc = _session[@grid.name].find(_id: BSON::ObjectId.from_string(request_json['_id']))
        end
      elsif request_json['query']
        contains_nonqueryable_field = nil
        request_json['query'].keys.each do |rf|
          if contains_nonqueryable_field.nil?
            unless queryable_fields.include?(rf)
              contains_nonqueryable_field = rf
            end
          end
        end
        unless contains_nonqueryable_field.nil?
          status 500
          return body = {error: "field #{ contains_nonqueryable_field } is not a valid filter for grid #{ @grid.name }" }.to_json
        end
        @db.with(database: @schema.name) do |_session|
          current_doc = _session[@grid.name].find(request_json['query'])
        end
      else
        status 500
        return body = {error: "please supply either an _id key with ObjectID string value, or a query key and valid query hash as value"}.to_json
      end

      if current_doc.nil?
        status 500
        return body = {error: "UNKNOWN PROBLEM OR DOCUMENT NOT FOUND!"}.to_json
      end

      if request_json.include? 'fields'
        selected_fields = {}
        @grid.grid_fields.each do |gf|
          if request_json['fields'].include?(gf.name)
            selected_fields[gf.name] = 1
          end
        end
        current_doc.select(selected_fields)
      end
      requested_entry = current_doc.one
      stringify_ids [requested_entry]
      return requested_entry.to_json
    end
  end
end
