require 'test_helper'

class GridsControllerTest < ActionController::TestCase
  setup do
    @schema = create(:schema)
    @grid = @schema.grids.create(attributes_for(:grid))
    @grid_field = @grid.grid_fields.create(attributes_for(:grid_field))
  end

  teardown do
   Mongoid.purge!
  end

  should "get index" do
    get :index, schema_id: @schema
    assert_response :success
    assert_not_nil assigns(:grids)
  end

  should "get new" do
    get :new, schema_id: @schema
    assert_response :success
  end

  should "create grid" do
    new_grid_attributes = attributes_for(:grid)
    assert_difference('Grid.count') do
      post :create, schema_id: @schema, grid: new_grid_attributes
    end
    assert_not_nil assigns(:grid)
    assert_redirected_to schema_grid_path(@schema, assigns(:grid))
    t_grid = Grid.find(assigns(:grid).id)
    assert_equal new_grid_attributes[:name], t_grid.name
    assert_equal new_grid_attributes[:description], t_grid.description
  end

  should "create grid with grid_fields" do
    new_grid_attributes = attributes_for(:grid)
    new_grid_attributes[:grid_fields_attributes] = [
                                                     {name: 'random_field', is_filterable: "1"},
                                                     {name: 'another_random_field', is_filterable: "0"}
                                                    ]
    assert_difference('Grid.count') do
      post :create, schema_id: @schema, grid: new_grid_attributes
    end
    assert_not_nil assigns(:grid)
    assert_redirected_to schema_grid_path(@schema, assigns(:grid))
    t_grid = Grid.find(assigns(:grid).id)
    assert_equal new_grid_attributes[:name], t_grid.name
    assert_equal new_grid_attributes[:description], t_grid.description
    assert_equal new_grid_attributes[:grid_fields_attributes].count, t_grid.grid_fields.count
    new_grid_attributes[:grid_fields_attributes].each_index do |i|
      assert_equal new_grid_attributes[:grid_fields_attributes][i][:name], t_grid.grid_fields[i].name
      if new_grid_attributes[:grid_fields_attributes][i][:is_filterable] == "1"
        assert t_grid.grid_fields[i].is_filterable?, 'should be filterable'
      else
        assert !t_grid.grid_fields[i].is_filterable?, "should not be filterable"
      end
    end
  end

  should "show grid" do
    get :show, schema_id: @schema, id: @grid
    assert_response :success
  end

  should "get edit" do
    get :edit, schema_id: @schema, id: @grid
    assert_response :success
  end

  should "update grid" do
    new_grid_attributes = {
      name: 'random_name',
      description: 'a random description'
    }
    patch :update, schema_id: @schema, id: @grid, grid: new_grid_attributes
    assert_redirected_to schema_grid_path(@schema, assigns(:grid))
    t_grid = Grid.find(@grid.id)
    assert_equal new_grid_attributes[:name], t_grid.name
    assert_equal new_grid_attributes[:description], t_grid.description
  end

  should 'update existing grid_field' do
    update_field_attributes = @grid_field.attributes.clone
    update_field_attributes['id'] = update_field_attributes['_id'].to_s
    update_field_attributes.delete('_id')
    originally_filterable = @grid_field.is_filterable?
    update_field_attributes[:is_filterable] = originally_filterable ? '0' : '1'
    update_grid_attributes = {
      grid_fields_attributes: [ update_field_attributes ]
    }
    patch :update, schema_id: @schema, id: @grid, grid: update_grid_attributes
    assert_redirected_to schema_grid_path(@schema, assigns(:grid))
    t_grid = Grid.find(@grid.id)
    t_grid_field = t_grid.grid_fields.find(@grid_field.id)
    assert_not_nil t_grid_field
    if originally_filterable
      assert !t_grid_field.is_filterable?, 'updated_field should not be filterable'
    else
      assert t_grid_field.is_filterable?, 'updated_field should be filterable'
    end
    assert t_grid.grid_fields.where({name: t_grid_field.name}).count == 1, 'test_grid_field should not be there more than once'
  end

  should 'add new grid_field' do
    new_grid_attributes = {
      grid_fields_attributes: [
                               {name: 'totally_new_field', is_filterable: "1"},
                               {name: 'even_newer_field', is_filterable: "0"}
                              ]
    }
    patch :update, schema_id: @schema, id: @grid, grid: new_grid_attributes
    assert_redirected_to schema_grid_path(@schema, assigns(:grid))
    t_grid = Grid.find(@grid.id)
    new_grid_attributes[:grid_fields_attributes].each do |field_def|
      assert t_grid.grid_fields.where(field_def).exists?, 'field_def should exist'
    end
  end

  should 'destroy existing grid_field' do
    destroy_field = @grid.grid_fields.create(name: 'test_delete_field', is_filterable: false)
    destroy_field_attributes = destroy_field.attributes.clone.merge(_destroy: "1")
    destroy_field_attributes['id'] = destroy_field_attributes['_id'].to_s
    destroy_field_attributes.delete('_id')
    new_grid_attributes = {
      grid_fields_attributes: [
                               destroy_field_attributes
                              ]
    }
    assert @grid.grid_fields.where({name: destroy_field.name}).exists?, 'test_delete_field should exist'
    patch :update, schema_id: @schema, id: @grid, grid: new_grid_attributes
    assert_redirected_to schema_grid_path(@schema, assigns(:grid))
    t_grid = Grid.find(@grid.id)
    assert !t_grid.grid_fields.where({name: destroy_field.name}).exists?, 'test_delete_field should not exist'
  end

  should 'update, add, and destroy grid_fields all in the same call' do
    update_field = @grid.grid_fields.first
    update_field_attributes = update_field.attributes.clone
    update_field_attributes['id'] = update_field_attributes['_id'].to_s
    update_field_attributes.delete('_id')
    originally_filterable = update_field.is_filterable?
    update_field_attributes[:is_filterable] = update_field.is_filterable ? "0" : "1"
    destroy_field = @grid.grid_fields.create(name: 'test_delete_field', is_filterable: false)
    destroy_field_attributes = destroy_field.attributes.clone.merge(_destroy: "1")
    destroy_field_attributes['id'] = destroy_field_attributes['_id'].to_s
    destroy_field_attributes.delete('_id')
    new_field_attributes = [
                            {name: 'totally_new_field', is_filterable: "1"},
                            {name: 'even_newer_field', is_filterable: "0"}
                           ]
    new_grid_attributes = {
      grid_fields_attributes: [
                               update_field_attributes,
                               destroy_field_attributes,
                              ] + new_field_attributes
    }
    patch :update, schema_id: @schema, id: @grid, grid: new_grid_attributes
    assert_redirected_to schema_grid_path(@schema, assigns(:grid))
    t_grid = Grid.find(@grid.id)
    updated_grid_field = t_grid.grid_fields.find(update_field.id)
    if originally_filterable
      assert !updated_grid_field.is_filterable?, 'updated_grid_field should not now be filterable'
    else
      assert updated_grid_field.is_filterable?, 'updated_grid_field should now be filterable'
    end
    new_field_attributes.each do |field_def|
      assert t_grid.grid_fields.where(field_def).exists?, 'field_def should exist'
    end
    assert !t_grid.grid_fields.where({name: destroy_field.name}).exists?, 'test_delete_field should not exist'
  end

  should "destroy grid" do
    assert_difference('Grid.count', -1) do
      delete :destroy, schema_id: @schema, id: @grid
    end

    assert_redirected_to schema_grids_path(@schema)
  end
end
