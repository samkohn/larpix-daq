from routines import Routine

start_dac=255
end_dac=100

def _test_pulse(controller, send_data, send_info, chip, *args):
    '''
    test_pulse(pulse_ampl, n_pulses)

    Issues ``n_pulses`` of amplitude ``pulse_ampl`` to each channel on the
    specified chip

    '''
    pulse_ampl = int(args[0])
    n_pulses = int(args[1])

    chip_key = chip

    for channel in range(32):
        controller.enable_testpulse(chip_key, channel_list=[channel], start_dac=start_dac)
        for pulse in range(n_pulses):
            try:
                controller.issue_testpulse(chip_key, pulse_ampl, min_dac=end_dac)
            except:
                controller.enable_testpulse(chip_key, channel_list=[channel], start_dac=start_dac)
                controller.issue_testpulse(chip_key, pulse_ampl, min_dac=end_dac)
        controller.disable_testpulse(chip_key, channel_list=[channel])

    to_return = 'success'
    return controller, to_return

test_pulse = Routine('test_pulse', _test_pulse, ['pulse_ampl','n_pulses'])

registration = {'test_pulse': test_pulse}
