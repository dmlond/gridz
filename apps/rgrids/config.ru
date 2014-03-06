# This file is used by Rack-based servers to start the application.

require ::File.expand_path('../config/environment',  __FILE__)
require './lib/data_app.rb'

map "/" do
  run Rails.application
end

map "/data" do
  run DataApp
end
