# Read about factories at https://github.com/thoughtbot/factory_girl

FactoryGirl.define do
  factory :grid_field do
    name "MyString"
    is_filterable false
    grid
  end
end
