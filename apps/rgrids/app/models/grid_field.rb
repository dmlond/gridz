class GridField
  include Mongoid::Document
  field :name, type: String
  field :is_filterable, type: Mongoid::Boolean
  embedded_in :grid
end
