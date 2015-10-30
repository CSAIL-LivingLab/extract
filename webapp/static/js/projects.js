$(document).ready(function() {
  $('.file-selector').change(function() {
    var inp = $(this).get(0);
    var text = inp.files.item(0).name;
    for (var i = 1; i < inp.files.length; i++) {
      var name = inp.files.item(i).name;
      text += ', ' + name
    }
    $(this).closest('.input-group').find('.file-selections').val(text);
  });
});
