JSON API for LArPixDAQ Webapp
=============================

## DAQ Commands

The frontend can send commands using the following interface:

```
{
  id: an integer ID unique to the frontend,
  params: a list of parameters
}
```

The backend will send responses using the following interface:

```
{
  id: the ID provided when the command was sent,
  result: the result as specified by the ModDAQ protocol format
}
```

The ``id`` is not used by the backend. It is only to help the frontend
keep track of actions.

## Action list

The format for the action list is:

```
{
  action_name: short name for the action,
  socket_event: the event name to call for SocketIO,
  enabled_states: list of state names where action is available,
  type: 'button', 'pane', or 'select' (select also has a button, and
          either type can have text inputs)
  type_options (if type === 'select'): list of options for the dropdown,
          with the format
      {
        name: name of the option,
        num_params: number of text input parameters,
        params: list of label names for text input parameters
      }
  num_params (if type === 'button'): number of text input parameters,
  params (if type === 'button'): list of label names for text input
          parameters
}
```

## Configuration register list

The format for the configuration register list is:

```
{
  name: register name
  type: one of 'normal', 'channel value', or 'channel binary',
}
```
