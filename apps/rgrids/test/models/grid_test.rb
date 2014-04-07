require 'test_helper'

class GridTest < ActiveSupport::TestCase
  setup do
    @grid = create(:grid)
  end

  teardown do
   Mongoid.purge!
  end

  should 'have name and description' do
    assert_respond_to @grid, 'name'
    assert_respond_to @grid, 'description'
  end

  should 'belong_to a schema' do
     assert_respond_to @grid, 'schema'
     assert_instance_of Schema, @grid.schema
  end

  should 'embed_many grid_fields' do
    assert_respond_to @grid, 'grid_fields'
    assert_instance_of GridField, @grid.grid_fields.first
  end

  should 'save grid_fields when grid is saved' do
    new_grid = @grid.schema.grids.build(name: 'new_grid', description: 'a totally new grid')
    new_grid_field = new_grid.grid_fields.build(name: 'new_field', is_filterable: false)

    assert new_grid.save, 'new grid should have saved'
    assert_not_nil new_grid.id
    test_grid = Grid.find(new_grid.id)
    assert_equal 1, test_grid.grid_fields.count
    assert_equal 'new_field', test_grid.grid_fields.first.name
    assert !(test_grid.grid_fields.first.is_filterable?)
  end
end
