'use strict';

var socket = io();
$(document).ready(function() {
  console.log(socket);
  socket.on('/', function(msg) {
    console.log(msg);
  });
  socket.emit('', 'World');
  $('#start-run').click(function() {
    socket.emit('command/start-run', '', function(msg) {
      msg = JSON.stringify(JSON.parse(msg), null, 5);
      console.log(msg);
      $('body').append('<br>Run has begun! ' + msg);
    });
  });
  $('#end-run').click(function() {
    socket.emit('command/end-run', '', function(msg) {
      $('body').append('<br>Run has ended! ' + msg);
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
});

class ActionTrigger extends React.Component {
  render() {
    return <button onClick={this.props.onClick}>{this.props.name}</button>;
  }
}

ReactDOM.render(
    <ActionTrigger name="start-run" onClick={()=>socket.emit('command/start-run', '')} />,
    document.getElementById('daq-root')
);
