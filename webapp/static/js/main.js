'use strict';

var socket = io();
class ActionTrigger extends React.Component {
  constructor(props) {
    super(props);
    if(this.props.type == 'select') {
      this.state = {value: this.props.type_options[0]};
    }
  }

  handleChange(new_value) {
    this.setState({value: new_value});
  }

  onTriggerClick() {
    const socket_msg = [this.props.socket_msg];
    if(this.props.type == 'select') {
      socket_msg.push(this.state.value);
      console.log(socket_msg);
    }
    socket.emit(this.props.socket_event, socket_msg);
    this.props.onButtonClick(this.props.name);
  }

  render() {
    const button = (
        <ActionTriggerButton
          name={this.props.name}
          disabled={this.props.disabled}
          onClick={this.onTriggerClick.bind(this)} />
    );
    if(this.props.type == 'select') {
      const select = (
          <ActionTriggerSelect
            options={this.props.type_options}
            value={this.state.value}
            handleChange={this.handleChange.bind(this)} />
      );
      return <div>{button} {select}</div>;
    }
    return button;
  }
}
class ActionTriggerButton extends React.Component {
  constructor(props) {
    super(props);
  }

  onClick() {
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

class ActionTriggerSelect extends React.Component {
  onSelectChange(event) {
    const new_value = event.target.value;
    this.props.handleChange(new_value);
  }
  render() {
    const options = this.props.options.map((o) =>
        <option key={o} value={o}>{o}</option>
    );
    const select = (
        <select value={this.props.value} onChange={this.onSelectChange.bind(this)}>
          {options}
        </select>
    );
    return select;
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
    this.state = {results: []};
    onActionUpdate(
        (u) => this.setState(function(state, props) {
          const old_result = state.results[u.id];
          state.results[u.id] = {...old_result, ...u};
        })
    );
  }
  onTriggerClick(name) {
    const first_description = {
      header: '_PRELIM',
      id: this.state.results.length,
      name: name,
      message: {
        result: '',
      },
    };
    this.setState((state, props) => state.results.push(first_description));
  }
  render() {
    const obj = this;
    const actionTriggers = this.props.actions.map(function(a) {
      return (
          <ActionTrigger
            name={a.action_name}
            socket_event={a.socket_event}
            socket_msg={obj.state.results.length}
            disabled={a.enabled_states.indexOf(obj.props.daqState) < 0}
            onButtonClick={obj.onTriggerClick.bind(obj)}
            type={a.type}
            type_options={a.type_options} />
      );
    });
    const actionTriggersList = actionTriggers.map((a) => (
          <li key={a.props.name}>{a}</li>
    ));
    return (
        <div>
          <ul>{actionTriggersList}</ul>
          <br />
          <ActionResultsList results={this.state.results} />
        </div>);
  }
}

class DAQPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {daqState: 'INIT'}
    onStateUpdate(
        (u) => this.setState({daqState: u.message.result})
    );
  }
  render() {
    return (
        <div>
          <img src="/static/larpix.png" width="100px"/>
          <DAQState state={this.state.daqState} />
          <br />
          <DAQClientList />
          <ActionDashboard
            actions={this.props.actions}
            daqState={this.state.daqState} />
        </div>
    );
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
    action_name: 'prepare_run',
    socket_event: 'command/prepare-run',
    enabled_states: ['INIT', 'START'],
    type: 'button',
  },
  {
    action_name: 'start_run',
    socket_event: 'command/start-run',
    enabled_states: ['READY'],
    type: 'button',
  },
  {
    action_name: 'end_run',
    socket_event: 'command/end-run',
    enabled_states: ['RUN'],
    type: 'button',
  },
  {
    action_name: 'data_rate',
    socket_event: 'command/data-rate',
    enabled_states: ['READY', 'RUN'],
    type: 'button',
  },
  {
    action_name: 'packets',
    socket_event: 'command/packets',
    enabled_states: ['READY', 'RUN'],
    type: 'button',
  },
  {
    action_name: 'run_routine',
    socket_event: 'command/run_routine',
    enabled_states: ['INIT',  'READY', 'RUN', 'START'],
    type: 'select',
    type_options: [
      'quickstart',
      'leakage_current_scan',
    ],
  },
];

ReactDOM.render(
    <DAQPage actions={actions} />,
    document.getElementById('daq-root')
);
