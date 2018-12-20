from moddaq import Controller

class Interface(object):
    def __init__(self):
        self.controller = Controller()
        self.state = b''
        self.controller.request_state()

    def run(self):
        print('       Starting Controller...')
        print('------Ctrl-c to enter a message------')
        print('--------Ctrl-c twice to quit---------')
        while True:
            try:
                again = True
                while again:
                    messages = self.controller.receive()
                    again = bool(messages)
                    if again:
                        for message in messages:
                            self.controller.handle(message)
                if self.state != self.controller.state:
                    print('State update. New state: %s' %
                            self.controller.state)
                    self.state = self.controller.state
            except KeyboardInterrupt:
                message = input('\rEnter a message: ')
                if message == 'CLIENTS':
                    self.controller.request_clients()
                elif message == 'STATE':
                    new_state_str = input('Enter the new state: ')
                    new_state = new_state_str.encode('utf-8')
                    self.controller.request_state_change(new_state)
                elif message == 'GET STATE':
                    self.controller.request_state()
                elif message == 'CURRENT STATE':
                    print(self.state)
                else:
                    self.controller.send_message('PRINT', message)

try:
    interface = Interface()
    interface.run()
finally:
    interface.controller.cleanup()
