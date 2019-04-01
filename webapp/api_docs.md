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

