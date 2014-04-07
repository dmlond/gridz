# Place all the behaviors and hooks related to the matching controller here.
# All this logic will automatically be available in application.js.
# You can use CoffeeScript in this file: http://coffeescript.org/
onLoad ->
  $('a#add_grid_field').click ->
    clone_grid_field()
    return
  $('a.remove_grid_field').click ->
    remove_grid_field $(this).parent().get(0)
    return
  $('a.destroy_grid_field').click ->
    destroy_grid_field $(this).parent().get(0)
    return
  return

destroy_grid_field = (field) ->
  if $('li.grid_field').length == 1
    alert("Please add a field before you destroy the only existing field")
    return
  id_prefix = 'input#grid_grid_fields_attributes_'+parseInt($(field).find(':input')[0].id.replace(/grid_grid_fields_attributes_(\d+)_name/m, '$1'))
  destroy_checkbox = $(id_prefix+'__destroy')
  destroy_checkbox.attr({'checked': 'checked'})
  id_field = $(id_prefix+'_id')
  $('div.grid_fields').append(id_field)
  $('div.grid_fields').append(destroy_checkbox)
  $(field).remove()
  return

remove_grid_field = (field) ->
  if $('li.grid_field').length > 1
      field.remove()

clone_grid_field = () ->
    new_element = $('li.grid_field:last').clone(false,false)
    elem_id = new_element.find(':input')[0].id
    elem_num = parseInt(elem_id.replace(/grid_grid_fields_attributes_(\d+)_name/m, '$1')) + 1
    hidden_id_field_id = 'grid_grid_fields_attributes_'+elem_num+'_id'

    new_element.find(':input').each ->
        id = this.id.replace('_' + (elem_num - 1) + '_', '_' + elem_num + '_')
        if id == hidden_id_field_id
          $(this).remove()
          return
        name = this.name.replace('['+ (elem_num - 1) + '][', '['+ elem_num + '][')
        $(this).attr({'name': name, 'id': id}).val('')
        return

    new_element.find('label').each ->
        new_for = $(this).attr('for').replace('_' + (elem_num - 1) + '_', '_' + elem_num + '_')
        $(this).attr({'for': new_for})
        return

    new_anchor = $('<a href="javascript:void(0)" class="remove_grid_field">[x]</a>')
    new_element.find('a.destroy_grid_field').replaceWith(new_anchor)
    $('li.grid_field:last').after(new_element)
    $('a.remove_grid_field').click ->
      remove_grid_field $(this).parent().get(0)
      return
    return