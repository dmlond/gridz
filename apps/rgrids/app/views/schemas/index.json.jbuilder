json.array!(@schemas) do |schema|
  json.extract! schema, :id, :name, :description
  json.url schema_url(schema, format: :json)
end
