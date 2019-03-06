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
    return (
        <button
            onClick={this.onClick.bind(this)}
            disabled={this.props.disabled}>
          {this.props.name}
        </button>
    );
  }
}

class DAQState extends React.Component {
  render() {
    return <h1>State: {this.props.state}</h1>;
  }
}

class DAQClient extends React.Component {
  render() {
    return <li>{this.props.name}</li>;
  }
}

class DAQClientList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {clients: []};
    onClientUpdate(
        (u) => this.setState({clients: u.message.result})
    );
  }
  render() {
    const clientList = this.state.clients.map((name) =>
        <DAQClient key={name} name={name} />);
    return (
        <div>
          <h2>Client list</h2>
          <ul>{clientList}</ul>
        </div>
    );
  }
}

class ActionMessage extends React.Component {
  render() {
    const r = this.props.result;
    const name = r.name;
    if (r.header == '_PRELIM') {
      return <li>Awaiting more info for: {name}</li>;
    }
    else if (r.message.metadata) {
      return <li>{name}: {r.header} {r.message.result} ({JSON.stringify(r.message.metadata)})</li>;
    }
    else {
      return <li>{name}: {r.header} {r.message.result}</li>;
    }
  }
}

class ActionResultsList extends React.Component {
  render() {
    const actionResults = this.props.results.map((r) => (
          <ActionMessage
            key={r.id}
            result={r} />
    ));
    return <ol>{actionResults}</ol>;
  }
}

class ActionDashboard extends React.Component {
  constructor(props) {
    super(props);
    this.state = {results: [], daqState: 'INIT'};
    onActionUpdate(
        (u) => this.setState(function(state, props) {
          const old_result = state.results[u.id];
          state.results[u.id] = {...old_result, ...u};
        })
    );
    onStateUpdate(
        (u) => this.setState({daqState: u.message.result})
    );
  }
  onTriggerClick(name) {
    const first_description = {
      header: '_PRELIM',
      id: name,
      name: name,
      message: {
        result: '',
      },
    };
    this.setState((state, props) => state.results.push(first_description));
  }
  render() {
    const actionTriggers = this.props.actions.map((a) => (
          <ActionTrigger
            name={a.action_name}
            socket_event={a.socket_event}
            socket_msg={this.state.results.length}
            disabled={a.enabled_states.indexOf(this.state.daqState) < 0}
            onClick={this.onTriggerClick.bind(this)} />
    ));
    const actionTriggersList = actionTriggers.map((a) => (
          <li key={a.props.name}>{a}</li>
    ));
    return (
        <div>
          <DAQState state={this.state.daqState} />
          <br />
          <DAQClientList />
          <br />
          <ul>{actionTriggersList}</ul>
          <br />
          <ActionResultsList results={this.state.results} />
        </div>);
  }
}

function onActionUpdate(cb) {
  socket.on('action-update', function(update) {
    console.log(update);
    cb(update);
    });
};

function onStateUpdate(cb) {
  socket.on('state-update', function(update) {
    cb(update);
  });
};

function onClientUpdate(cb) {
  socket.on('client-update', function(update) {
    cb(update);
  });
};

const actions = [
  {
    action_name: 'start_run',
    socket_event: 'command/start-run',
    enabled_states: ['READY'],
  },
  {
    action_name: 'end_run',
    socket_event: 'command/end-run',
    enabled_states: ['RUN'],
  },
];

const clients = ['LArPix Board', 'Aggregator', 'Run Data'];

ReactDOM.render(
    <ActionDashboard actions={actions} clients={clients} />,
    document.getElementById('daq-root')
);
