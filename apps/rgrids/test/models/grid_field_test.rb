require 'test_helper'

class GridFieldTest < ActiveSupport::TestCase

  setup do
    @grid_field = create(:grid_field)
  end

  teardown do
   Mongoid.purge!
  end

  should 'have name and is_filterable?' do
    assert_respond_to @grid_field, 'name'
    assert_respond_to @grid_field, 'is_filterable?'
  end

  should 'be embeded in a grid' do
     assert_respond_to @grid_field, 'grid'
     assert_instance_of Grid, @grid_field.grid
  end

end
