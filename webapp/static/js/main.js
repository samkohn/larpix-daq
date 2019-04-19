'use strict';

var socket = io();
class ActionTrigger extends React.Component {
  constructor(props) {
    super(props);
    if(this.props.type == 'select') {
      const start_value = this.props.type_options[0];
      this.state = {
        value: start_value,
        input_values: Array(start_value.num_params).fill(''),
        params: [],
        num_params: 0,
      };
    }
    else if(this.props.type == 'button') {
      this.state = {
        input_values: Array(this.props.num_params).fill(''),
        params: this.props.params,
        num_params: this.props.num_params,
      };
    }
    else if(this.props.type == 'pane') {
      this.state = {
        num_params: 0,
        showPane: false,
        pane: null
      };
    }
  }

  handleChange(new_value_name) {
    for(let i in this.props.type_options) {
      if(this.props.type_options[i].name == new_value_name) {
        this.setState(function(state, props){
          const new_value = this.props.type_options[i];
          const params = this.props.type_options[i].params;
          const num_params = this.props.type_options[i].num_params;
          return {
            value: new_value,
            input_values: Array(new_value.num_params).fill(''),
            params: params,
            num_params, num_params,
          };
        });
      }
    }
  }

  handleInputChange(event) {
    const new_value = event.target.value;
    const index = Number(event.target.name);
    this.setState(function(state, props) {
        let new_inputs = state.input_values.slice();
        new_inputs[index] = new_value;
        return {input_values: new_inputs};
    });
  }

  onTriggerClick() {
    const socket_msg = {
      id: this.props.socket_msg
    };
    if(this.props.type == 'select') {
      socket_msg.params = [this.state.value];
      socket_msg.params.push(this.state.input_values);
      console.log(socket_msg);
    }
    else if(this.props.type == 'button') {
      socket_msg.params = [this.state.input_values];
    }
    socket.emit(this.props.socket_event, socket_msg);
    this.props.onButtonClick(this.props.name);
  }

  togglePane() {
    this.setState(function(state, props) {
      return {showPane: !(state.showPane)};
    });
  }

  render() {
    let list = [];
    const button = (
        <ActionTriggerButton
          name={this.props.name}
          key='button'
          disabled={this.props.disabled}
          onClick={this.onTriggerClick.bind(this)} />
    );
    list.push(button);
    if(this.props.type == 'select') {
      const select = (
          <ActionTriggerSelect
            key='select'
            options={this.props.type_options}
            value={this.state.value.name}
            handleChange={this.handleChange.bind(this)} />
      );
      list.push(select);
    }
    if(this.state.num_params > 0) {
      const textInputs = this.state.input_values.map((value, index) =>
          <span key={'span' + index}>
          <label htmlFor={index}>{this.state.params[index]}</label>
          <input
            type="text"
            className="actioninput"
            value={value}
            name={index}
            id={index}
            onChange={this.handleInputChange.bind(this)}>
          </input>
          </span>
      );
      list.push(textInputs);
    }
    return <div>{list}</div>;
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
        <option key={o.name} value={o.name}>{o.name}</option>
    );
    const select = (
        <select value={this.props.value} onChange={this.onSelectChange.bind(this)}>
          {options}
        </select>
    );
    return select;
  }
}


class DAQState extends React.PureComponent {
  render() {
    return <h1>State: {this.props.state}</h1>;
  }
}

class DAQClient extends React.PureComponent {
  render() {
    return <li>{this.props.name}</li>;
  }
}

class DAQClientList extends React.PureComponent {
  constructor(props) {
    super(props);
    this.state = {clients: []};
    onClientUpdate(
        (u) => {
          const result = u.message.result;
          const existing = this.state.clients;
          let same = true;
          if(result.length !== existing.length) {
            same = false;
          }
          else {
            for(let i in existing) {
              if(result[i] !== existing[i]) {
                same = false;
              }
            }
          }
          if(!same) {
            this.setState({clients: result})
          }
        }
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
      return <li>{name}: {r.header} {JSON.stringify(r.message.result)} ({JSON.stringify(r.message.metadata)})</li>;
    }
    else {
      return <li>{name}: {r.header} {JSON.stringify(r.message.result)}</li>;
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
    this.state = {
      results: [],
      configuration_pane: {
        chip: null,
        values: null,
      },
    };
    onActionUpdate((u) => {
      this.setState(function(state, props) {
        let newResults = state.results.slice();
        u.name = newResults[u.id].name;
        newResults[u.id] = u;
        return {results: newResults};
      });
      if(u.name === 'retrieve_config') {
        const new_configs = JSON.parse(JSON.stringify(u.message.result));
        const chipid = u.message.metadata.params[0];
        this.setState(function(state, props) {
          const copy = {...state.configuration_pane};
          copy.values[chipid] = {...copy.values[chipid], ...new_configs};
          return {configuration_pane: copy};
        });
      }
    });
  }

  initConfigPane(chip, values) {
    this.setState({configuration_pane: {chip: chip, values:values}});
  }

  onRegisterChange(name, newValue) {
    this.setState(function(state, props) {
      const pane = {...state.configuration_pane};
      const chip = pane.chip;
      pane.values[chip][name] = newValue;
      return {configuration_pane: pane};
    });
  }

  onChipChange(newChip) {
    this.setState(function(state, props) {
      const pane = {...state.configuration_pane};
      pane.chip = newChip;
      return {configuration_pane: pane};
    });
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
    this.setState((state, props) => {
      let new_results = state.results.slice();
      new_results.push(first_description);
      return {results: new_results};
    });
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
            type_options={a.type_options}
            params={a.params}
            num_params={a.num_params} />
      );
    });
    const pane = <ConfigurationPane
      key="pane"
      next_id={this.state.results.length}
      chip={this.state.configuration_pane.chip}
      values={this.state.configuration_pane.values}
      onInit={this.initConfigPane.bind(this)}
      onRegisterChange={this.onRegisterChange.bind(this)}
      onChipChange={this.onChipChange.bind(this)}
      onButtonClick={this.onTriggerClick.bind(this)} />;
    const actionTriggersList = actionTriggers.map((a) => (
          <li key={a.props.name}>{a}</li>
    ));
    return (
        <div>
          <ul>{actionTriggersList}</ul>
          <br />
          {pane}
          <br />
          <ActionResultsList results={this.state.results} />
        </div>);
  }
}

class ConfigSendButton extends React.Component {
  render() {
    return <button>Send</button>;
  }
}

class ConfigRetrieveButton extends React.Component {
  onButtonClick(event) {
    this.props.onButtonClick();
  }
  render() {
    return <button onClick={this.onButtonClick.bind(this)}>Retrieve</button>;
  }
}

class ConfigChipSelect extends React.Component {
  onChange(event) {
    const newChip = event.target.value;
    this.props.onChange(newChip);
  }
  render() {
    const options = this.props.options.map((name) =>
        <option key={name} value={name}>{name}</option>
    );
    return (
        <select value={this.props.value} onChange={this.onChange.bind(this)}>
          {options}
        </select>
    );
  }
}

class ConfigList extends React.Component {
  render() {
    const items = [];
    for(let i in this.props.registers) {
      const register = this.props.registers[i];
      const name = register.name
      const currentValue = this.props.values[name];
      const registerComponent = (
          <ConfigRegister
            key={register.name}
            name={register.name}
            type={register.type}
            index={i}
            value={currentValue}
            onChange={this.props.onChange} />
      );
      items.push(registerComponent);
    }
    return <div>{items}</div>;
  }
}

class ConfigRegister extends React.Component {
  onChangeSimple(event) {
    const newValue = event.target.value;
    this.props.onChange(this.props.index, newValue);
  }
  onChangeComplex(index) {
    const func = function(event) {
      const target = event.target;
      const val = target.type === 'checkbox' ? target.checked : target.value;
      const newValue = {
        index: index,
        value: val
      };
      this.props.onChange(this.props.index, newValue);
    };
    func.bind(this);
    return func;
  }
  render() {
    const label = (
        <label htmlFor={this.props.name + (this.props.type[0]==='c'?'_0':'')}>
          {this.props.name}
        </label>
    );
    let inputs = null;
    if(this.props.type === 'normal') {
      inputs = <input
        type="text"
        className="configinput"
        name={this.props.name}
        id={this.props.name}
        value={this.props.value}
        onChange={this.onChangeSimple.bind(this)} />;
    }
    else
    {
      let type = '';
      if(this.props.type === 'channel value') {
        type = "text";
        inputs = Array(32).fill('').map((v, i) =>
            <input
              className="configinput"
              key={i}
              type={type}
              name={this.props.name + '_' + i}
              id={this.props.name + '_' + i}
              value={this.props.value[i]}
              onChange={this.onChangeComplex(i).bind(this)} />
        );
      }
      else if(this.props.type == 'channel binary') {
        type = "checkbox";
        inputs = Array(32).fill('').map((v, i) =>
            <input
              key={i}
              type={type}
              name={this.props.name + '_' + i}
              id={this.props.name + '_' + i}
              checked={this.props.value[i]}
              onChange={this.onChangeComplex(i).bind(this)} />
        );
      }
    }
    return <div>{label} {inputs}</div>;
  }
}

function configurationFactory() {
  return {
    pixel_trim_thresholds: Array(32).fill(16),
    global_threshold: '16',
    channel_mask: Array(32).fill(false),
  };
};

class ConfigurationPane extends React.Component {
  constructor(props) {
    super(props);
    this.chipOptions = ['246', '245', '252', '243'];
    this.registers = [{
      name: 'pixel_trim_thresholds',
      type: 'channel value'
    },
    {
      name: 'global_threshold',
      type: 'normal'
    },
    {
      name: 'channel_mask',
      type: 'channel binary'
    }];
    const referenceValues = {
      '246': configurationFactory(),
      '245': configurationFactory(),
      '252': configurationFactory(),
      '243': configurationFactory(),
    };
    this.props.onInit(this.chipOptions[0], referenceValues);
  }

  onChipChange(newChip) {
    this.props.onChipChange(newChip);
  }

  onRegisterChange(index, newValue) {
    const type = this.registers[index].type;
    const name = this.registers[index].name;
    if(type === 'normal') {
      this.props.onRegisterChange(name, newValue);
    }
    else if(type[0] == 'c') {
      const channel = newValue.index;
      const value = newValue.value;
      const toUpdate = this.props.values[this.props.chip][name];
      toUpdate[channel] = value;
      this.props.onRegisterChange(name, toUpdate);
    }
    else {
      console.log(type);
    }
  }

  onRetrieveButtonClick() {
    const socket_event = 'command/retrieve_config';
    const socket_msg = {
      id: this.props.next_id,
      params: [this.props.chip]
    };
    socket.emit(socket_event, socket_msg);
    this.props.onButtonClick('retrieve_config');
  }

  render() {
    if(!(this.props.chip)) {
      return null;
    }
    return (
      <div>
        <ConfigSendButton />
        <ConfigRetrieveButton
          onButtonClick={this.onRetrieveButtonClick.bind(this)} />
        <ConfigChipSelect
          options={this.chipOptions}
          value={this.props.chip}
          onChange={this.onChipChange.bind(this)} />
        <ConfigList
          registers={this.registers}
          values={this.props.values[this.props.chip]}
          onChange={this.onRegisterChange.bind(this)} />
      </div>
    );
  }
}

class DAQPage extends React.PureComponent {
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
    num_params: 0,
  },
  {
    action_name: 'start_run',
    socket_event: 'command/start-run',
    enabled_states: ['READY'],
    type: 'button',
    num_params: 0,
  },
  {
    action_name: 'end_run',
    socket_event: 'command/end-run',
    enabled_states: ['RUN'],
    type: 'button',
    num_params: 0,
  },
  {
    action_name: 'data_rate',
    socket_event: 'command/data-rate',
    enabled_states: ['READY', 'RUN'],
    type: 'button',
    num_params: 0,
  },
  {
    action_name: 'packets',
    socket_event: 'command/packets',
    enabled_states: ['READY', 'RUN'],
    type: 'button',
    num_params: 0,
  },
  {
    action_name: 'run_routine',
    socket_event: 'command/run_routine',
    enabled_states: ['INIT',  'READY', 'RUN', 'START'],
    type: 'select',
    type_options: [
    {name: 'quickstart',
      num_params: 0},
    {name: 'leakage_current_scan',
      num_params: 1,
      params: ['chips']},
    ],
  },
  {
    action_name: 'write_configuration',
    socket_event: 'command/write_config',
    enabled_states: ['INIT', 'READY', 'RUN', 'START'],
    type: 'button',
    num_params: 1,
    params: ['chip'],
  },
  {
    action_name: 'verify_configuration',
    socket_event: 'command/verify_config',
    enabled_states: ['INIT', 'READY', 'RUN', 'START'],
    type: 'button',
    num_params: 1,
    params: ['chip'],
  },

];

ReactDOM.render(
    <DAQPage actions={actions} />,
    document.getElementById('daq-root')
);
