class Grid
  include Mongoid::Document
  field :name, type: String
  field :description, type: String
  belongs_to :schema
  embeds_many :grid_fields
  accepts_nested_attributes_for :grid_fields, allow_destroy: true
end
