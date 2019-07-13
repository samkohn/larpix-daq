from routines import Routine
import copy
from larpix.larpix import Configuration

def _leakage(controller, send_data, send_info, chip, *args):
    '''
    leakage(run_time)

    Measures leakage rate on a given chip by disabling periodic resets. Leakage
    current can be calculated as (rate_leakage - rate_nom) * threshold where
    rate_leakage is the trigger rate during this routine, rate_nom is the nominal
    trigger rate, and threshold is the trigger threshold.

    '''
    run_time = float(args[0])

    chip_key = chip
    chip = controller.get_chip(chip_key)

    orig_config = copy.deepcopy(chip.config)
    chip.config.periodic_reset = 0
    controller.write_configuration(chip_key, Configuration.periodic_reset_address)
    controller.run(run_time,message='leakage {}'.format(chip_key))
    chip.config = orig_config
    controller.write_configuration(chip_key)

    to_return = 'success'
    return controller, to_return

leakage = Routine('leakage', _leakage, ['run_time'])

registration = {'leakage': leakage}
