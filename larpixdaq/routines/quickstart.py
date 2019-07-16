from larpixdaq.routines import Routine
from larpix.quickstart import quickcontroller

def _quickstart(board, send_data, send_info, board_name):
    '''
    quickstart(board_name)

    Start up the board and configure ASICs to a quiescent state.

    '''
    send_info('Running quickstart')
    new_board = quickcontroller(board_name, io=board.io,
            logger=board.logger)
    send_info('Completed quickstart')
    result = 'success'
    return new_board, result

quickstart = Routine('quickstart', _quickstart, ['board'])

registration = {
        'quickstart': quickstart,
        }
