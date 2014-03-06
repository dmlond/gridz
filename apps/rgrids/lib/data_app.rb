APP_ROOT = File.expand_path(File.join(File.dirname(__FILE__), '..'))
 
require 'sinatra'
 
class DataApp < Sinatra::Application
  set :root, APP_ROOT

  get '/' do
    'Hello Sinatra'
  end
end

