import time
from threading import Timer, Thread
import logging

""" Timer that repeats indefinitely. To stop call the cancel Timer methods.
    Use initial_delay to start the timer later.
    Updated to include stop method. GSD 20200817
"""


class RepeatTimer(Timer):
    def __init__(self, initial_delay, interval, function, *args):
        super().__init__(interval, function, *args)
        self.initial_delay = initial_delay
        self._interrupted = False
        logging.debug(f'Timer: {self.function.__name__} delay = {initial_delay}, interval = {interval}')

    def run(self):
        time.sleep(self.initial_delay)
        if self._interrupted == True:
            return
        t = Thread(target=self.function, args=(*self.args,), daemon=True)
        t.start()
        while not self.finished.wait(self.interval):
            t = Thread(target=self.function, args=(*self.args,), daemon=True)
            t.start()

    def stop(self):
        """ call the stop method to interrupt the reapeating timer """
        self.cancel()
        self._interrupted = True
        logging.debug(f'Timer: {self.function.__name__} stopped')
