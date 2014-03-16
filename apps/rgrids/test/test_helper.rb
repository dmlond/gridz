ENV["RAILS_ENV"] ||= "test"
ENV["RACK_ENV"] ||= "test"
require File.expand_path('../../config/environment', __FILE__)
require 'rails/test_help'
require 'rack/test'
require File.expand_path('../../lib/grid_rest_api', __FILE__)

class ActiveSupport::TestCase
  include FactoryGirl::Syntax::Methods
  include Rack::Test::Methods
end
