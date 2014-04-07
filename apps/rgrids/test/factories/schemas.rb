FactoryGirl.define do
  factory :schema do
    name "Schema"
    description "A SCHEMA"
    after(:create) do |schema, evaluator|
      create_list(:grid, 1, schema: schema)
    end
  end
end
