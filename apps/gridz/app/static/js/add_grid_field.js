$(document).ready(function () {
    $('a#add_grid_field').click(function () {
        clone_grid_field('li.grid_field:last');
    });
});

function clone_grid_field(selector) {
    var new_element = $(selector).clone(true);
    var elem_id = new_element.find(':input')[0].id;
    var elem_num = parseInt(elem_id.replace(/grid_form_fields-(\d+)-name/m, '$1')) + 1;
    new_element.find('table').each(function() {
        var id = $(this).attr('id').replace('-' + (elem_num - 1), '-' + elem_num);
        $(this).attr('id', id)
    });
    new_element.find(':input').each(function() {
        var id = $(this).attr('id').replace('-' + (elem_num - 1) + '-', '-' + elem_num + '-');
        $(this).attr({'name': id, 'id': id}).val('')
    });
    new_element.find('label').each(function() {
        var new_for = $(this).attr('for').replace('-' + (elem_num - 1) + '-', '-' + elem_num + '-');
        $(this).attr('for', new_for);
    });
    new_element.find('select').each(function() {
        var id = $(this).attr('id').replace('-' + (elem_num - 1) + '-', '-' + elem_num + '-');
        $(this).attr({'name': id, 'id': id}).val('')
    });
    $(selector).after(new_element);
}