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
  constructor(props) {
    super(props);
  }

  onClick() {
    socket.emit(this.props.socket_event, this.props.socket_msg);
    this.props.onClick(this.props.name);
  }

  render() {
    return <button onClick={this.onClick.bind(this)}>{this.props.name}</button>;
  }
}

class DAQState extends React.Component {
  render() {
    return <h1>State: {this.props.state}</h1>;
  }
}

class ActionMessage extends React.Component {
  render() {
    return <li>{this.props.action_name}: {this.props.result}</li>;
  }
}

class ActionResultsList extends React.Component {
  render() {
    const actionResults = this.props.results.map((r) => (
          <ActionMessage
            key={r.action_name}
            action_name={r.action_name}
            result={r.result} />
    ));
    return <ul>{actionResults}</ul>;
  }
}

class ActionDashboard extends React.Component {
  constructor(props) {
    super(props);
    this.state = {results: [], daqState: 'INIT'};
    onStateUpdate(
        (u) => this.setState({daqState: u.message.result})
    );
  }
  onTriggerClick(name) {
    this.setState((state, props) => state.results.push({action_name: name}));
  }
  render() {
    const actionTriggers = this.props.actions.map((a) => (
          <ActionTrigger
            name={a.action_name}
            socket_event={a.socket_event}
            socket_msm={a.socket_msg}
            onClick={this.onTriggerClick.bind(this)} />
    ));
    const actionTriggersList = actionTriggers.map((a) => (
          <li key={a.props.name}>{a}</li>
    ));
    return (
        <div>
          <DAQState state={this.state.daqState} />
          <br />
          <ul>{actionTriggersList}</ul>
          <br />
          <ActionResultsList results={this.state.results} />
        </div>);
  }
}

function onStateUpdate(cb) {
  socket.on('state-update', function(update) {
    cb(update);
  });
};

const actions = [
  {
    action_name: 'start_run',
    socket_event: 'command/start-run',
    socket_msg: '',
  },
  {
    action_name: 'end_run',
    socket_event: 'command/end-run',
    socket_msg: '',
  },
];

ReactDOM.render(
    <ActionDashboard actions={actions}/>,
    document.getElementById('daq-root')
);
