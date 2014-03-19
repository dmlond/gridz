module JsonHelpers
  def post_json(url, data = nil)
    document = data.nil? ? nil : data.to_json
    post(url, document, { "CONTENT_TYPE" => "application/json" })
    rbody = last_response.body
    parse_json(rbody)
  end

  private
  def parse_json(string)
    begin
      JSON.parse(string)
    rescue JSON::ParserError
      assert false, "ERROR WITH RETURNED JSON #{ last_response.body }"
    end
  end
end
