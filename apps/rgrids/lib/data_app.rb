require 'sinatra'
 
class DataApp < Sinatra::Application
  set :root, File.expand_path(File.join(File.dirname(__FILE__), '..'))

  get '/' do
    'Hello Sinatra'
  end
end
