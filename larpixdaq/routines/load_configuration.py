from larpixdaq.routines.routines import Routine
import os
import larpixdaq

config_dir=os.path.join(larpixdaq.__path__[0], 'configs/')

def _load_configuration(controller, send_data, send_info, chip, *args):
    '''
    load_configuration(configuration_name)

    Load configuration and write configuration to a specified chip

    '''
    config_name = args[0]
    to_return = ''
    try:
        send_info('checking for config in {}'.format(config_dir))
        controller.get_chip(chip).config.load(os.path.join(config_dir, config_name))
        controller.write_configuration(chip)
        to_return = 'success'
    except IOError:
        try:
            send_info('checking for built-in config {}'.format(config_name))
            controller.get_chip(chip).config.load(config_name)
            controller.write_configuration(chip)
            to_return = 'success'
        except IOError:
            send_info('no config {} found'.format(config_name))
            to_return = 'error'
    return controller, to_return

load_configuration = Routine('load_configuration', _load_configuration, ['config_name'])

registration = {'load_configuration': load_configuration}
