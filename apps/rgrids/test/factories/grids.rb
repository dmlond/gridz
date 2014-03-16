# Read about factories at https://github.com/thoughtbot/factory_girl

FactoryGirl.define do
  factory :grid do
    name "NEW_GRID"
    description "This is a new grid"
    schema
    after(:create) do |grid, evaluator|
      create_list(:grid_field, 1, grid: grid)
    end
  end
end
