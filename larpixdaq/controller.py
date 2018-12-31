from __future__ import absolute_import
from __future__ import print_function
from moddaq import Controller

try:
    input = raw_input
except NameError:
    pass

class Interface(object):
    def __init__(self):
        self.controller = Controller()
        self.state = ''
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
                    new_state = input('Enter the new state: ')
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
