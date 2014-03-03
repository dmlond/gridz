json.array!(@grids) do |grid|
  json.extract! grid, :id, :name, :description
  json.url grid_url(grid, format: :json)
end
