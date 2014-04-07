json.array!(@grids) do |grid|
  json.extract! grid, :id, :name, :description
  json.url schema_grid_url([@schema, grid], format: :json)
end
