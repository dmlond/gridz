module JsonHelpers
  def post_json(url, data = nil)
    document = data.nil? ? nil : data.to_json
    post(url, document, { "CONTENT_TYPE" => "application/json" })
    rbody = last_response.body
    JSON.parse(rbody)
  end
end
