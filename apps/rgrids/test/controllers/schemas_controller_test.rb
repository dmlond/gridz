require 'test_helper'

class SchemasControllerTest < ActionController::TestCase
  setup do
    @schema = create(:schema)
  end

  teardown do
   Mongoid.purge!
  end

  should "get index" do
    get :index
    assert_response :success
    assert_not_nil assigns(:schemas)
  end

  should "get new" do
    get :new
    assert_response :success
  end

  should "create schema" do
    new_schema_attributes = attributes_for(:schema)
    assert_difference('Schema.count') do
      post :create, schema: new_schema_attributes
    end
    assert_not_nil assigns(:schema)
    assert_redirected_to schema_path(assigns(:schema))
    assert_equal new_schema_attributes[:name], assigns(:schema).name
    assert_equal new_schema_attributes[:description], assigns(:schema).description
  end

  should "show schema" do
    get :show, id: @schema
    assert_response :success
    assert_not_nil assigns(:schema)
  end

  should "get edit" do
    get :edit, id: @schema
    assert_response :success
    assert_not_nil assigns(:schema)
  end

  should "update schema" do
    new_name = 'new_random_name'
    patch :update, id: @schema, schema: { name: new_name }
    assert_not_nil assigns(:schema)
    assert_redirected_to schema_path(assigns(:schema))
    t_schema = Schema.find(@schema.id)
    assert_equal new_name, t_schema.name

    new_description = 'a random new description'
    patch :update, id: @schema, schema: { description: new_description }
    assert_not_nil assigns(:schema)
    assert_redirected_to schema_path(assigns(:schema))
    t_schema = Schema.find(@schema.id)
    assert_equal new_description, t_schema.description
  end

  should "destroy schema" do
    assert_difference('Schema.count', -1) do
      assert_difference('Grid.count', -@schema.grids.count) do
        delete :destroy, id: @schema
      end
    end

    assert_redirected_to schemas_path
  end

  should 'not destroy schema if there are any grids defined for the schema' do
    assert false 'implement'
  end
end
