from argparse import ArgumentParser
from os import system
from time import strftime, sleep
from traceback import print_exc
from foodExpenses import foodExpenses, credentials


def runAndCommit(triggerTime='04:00', triggerNow=False):
    try:
        while True:
            if strftime('%H:%M') == triggerTime or triggerNow:
                system('git pull')
                foodExpenses(credentials)
                system('git add *.png')
                system('git commit -m \"Automatic update today\"')
                system('git push')
                sleep(45)
            if triggerNow:
                break
    except BaseException:
        print_exc()


# Input argument parser
def grabInputArgs():
    parser = ArgumentParser(description='Run foodExpenses daily and push '
                                        'results to Github')
    parser.add_argument('-t', '--triggerTime', type=str, default='04:00',
                        help='Trigger time in HH:MM format. Default 04:00.')
    parser.add_argument('--triggerNow',
                        help='Would trigger immediately.',
                        action='store_true')
    return parser.parse_args()


if __name__ == "__main__":  # triger input parser on call
    args = grabInputArgs()
    runAndCommit(triggerTime=args.triggerTime, triggerNow=args.triggerNow)
