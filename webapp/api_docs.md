JSON API for LArPixDAQ Webapp
=============================

## DAQ Commands

The frontend can send commands using the following interface:

```
{
  id: an integer ID unique to the frontend,
  params: a list of parameters,
  display: true to display eventual result in list of messages
}
```

The backend will send responses using the following interface:

```
{
  id: the ID provided when the command was sent,
  header: the ModDAQ message header
  message: {
    result: the result of the command,
    metadata: (optional) metadata
  },
  display: true to display result in list of messages
}
```

The ``id`` is not used by the backend. It is only to help the frontend
keep track of actions.

