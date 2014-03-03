require 'test_helper'

class SchemaTest < ActiveSupport::TestCase
  setup do
    @schema = create(:schema)
  end

  teardown do
   Mongoid.purge!
  end

  should 'have name and description' do
    assert_respond_to @schema, 'name'
    assert_respond_to @schema, 'description'
  end

  should 'have_many grids' do
    assert_respond_to @schema, 'grids'
    assert_instance_of Grid, @schema.grids.first
  end
end
