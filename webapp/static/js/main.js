$(document).ready(function() {
  $('#start-run').click(function() {
    $.post('/command/start-run', function() {
      $('body').append('<br>Run has begun!');
    });
  });
  $('#end-run').click(function() {
    $.post('/command/end-run', function(data) {
      $('body').append('<br>Run has ended! ' + data);
    });
  });
  $('#retrieve-action').click(function() {
    $.get('/command/actionid/' + $('#retrieve-action-input').val(), function(strdata) {
      console.log(strdata);
      data = $.parseJSON(strdata);
      console.log(data);
      $('body').append('<br>' + data.result);
    });
  });
  setInterval(function() {
    $.post('/command/process');
  }, 1000);
});

