class GridsController < ApplicationController
  before_action :set_schema
  before_action :set_grid, only: [:show, :edit, :update, :destroy]

  # GET /grids
  # GET /grids.json
  def index
    @grids = Grid.all
  end

  # GET /grids/1
  # GET /grids/1.json
  def show
  end

  # GET /grids/new
  def new
    @grid = @schema.grids.build()
    @grid.grid_fields.build(name: nil, is_filterable: false)
  end

  # GET /grids/1/edit
  def edit
  end

  # POST /grids
  # POST /grids.json
  def create
    @grid = @schema.grids.build(grid_params)
    respond_to do |format|
      if @grid.save
        format.html { redirect_to [@schema, @grid], notice: 'Grid was successfully created.' }
        format.json { render action: 'show', status: :created, location: @grid }
      else
        format.html { render action: 'new' }
        format.json { render json: @grid.errors, status: :unprocessable_entity }
      end
    end
  end

  # PATCH/PUT /grids/1
  # PATCH/PUT /grids/1.json
  def update
    respond_to do |format|
      if @grid.update(grid_params)
        format.html { redirect_to [@schema, @grid], notice: 'Grid was successfully updated.' }
        format.json { head :no_content }
      else
        format.html { render action: 'edit' }
        format.json { render json: @grid.errors, status: :unprocessable_entity }
      end
    end
  end

  # DELETE /grids/1
  # DELETE /grids/1.json
  def destroy
    @grid.destroy
    respond_to do |format|
      format.html { redirect_to schema_grids_url(@schema) }
      format.json { head :no_content }
    end
  end

  private

    def set_schema
      @schema = Schema.find(params[:schema_id])
    end

    # Use callbacks to share common setup or constraints between actions.
    def set_grid
      @grid = @schema.grids.find(params[:id])
    end

    # Never trust parameters from the scary internet, only allow the white list through.
    def grid_params
      params.require(:grid).permit(:name, :description, grid_fields_attributes: [:name, :is_filterable, :id, :_destroy] )
    end
end
