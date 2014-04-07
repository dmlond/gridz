class SchemasController < ApplicationController
  before_action :set_schema, only: [:show, :edit, :update, :destroy]

  # GET /schemas
  # GET /schemas.json
  def index
    @schemas = Schema.all
  end

  # GET /schemas/1
  # GET /schemas/1.json
  def show
  end

  # GET /schemas/new
  def new
    @schema = Schema.new
  end

  # GET /schemas/1/edit
  def edit
  end

  # POST /schemas
  # POST /schemas.json
  def create
    @schema = Schema.new(schema_params)

    respond_to do |format|
      if @schema.save
        format.html { redirect_to @schema, notice: 'Schema was successfully created.' }
        format.json { render action: 'show', status: :created, location: @schema }
      else
        format.html { render action: 'new' }
        format.json { render json: @schema.errors, status: :unprocessable_entity }
      end
    end
  end

  # PATCH/PUT /schemas/1
  # PATCH/PUT /schemas/1.json
  def update
    respond_to do |format|
      if @schema.update(schema_params)
        format.html { redirect_to @schema, notice: 'Schema was successfully updated.' }
        format.json { head :no_content }
      else
        format.html { render action: 'edit' }
        format.json { render json: @schema.errors, status: :unprocessable_entity }
      end
    end
  end

  #TODO do not destroy if there is any grid defined for the schema
  def destroy
    @schema.destroy
    respond_to do |format|
      format.html { redirect_to schemas_url }
      format.json { head :no_content }
    end
  end

  private
    # Use callbacks to share common setup or constraints between actions.
    def set_schema
      @schema = Schema.find(params[:id])
    end

    # Never trust parameters from the scary internet, only allow the white list through.
    def schema_params
      params.require(:schema).permit(:name, :description)
    end
end
