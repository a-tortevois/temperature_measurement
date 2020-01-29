import asyncio
from utils.asynchelpers import show_timer

DEBUG = False


class TimerStartError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class TimerStopError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class Timer:
    def __init__(self, name, interval, callback):
        self.name = name
        self.interval = self.checkInterval(interval)
        self.callback = callback
        self.task = None
        self.timeout = False

    async def start(self):
        """It starts a new timeout. Do some checking before running another timeout."""
        if self.task:
            await self.cancel()
        if not self.task:
            if self.interval > 0:
                if DEBUG: show_timer(f"{self.name}.start")
                self.task = asyncio.create_task(self.run())
        else:
            raise TimerStartError(f"{self.name} start error")

    async def run(self):
        """Internal function to run the asynchronous task. Waits for the interval delay and executes the callback when
           time is out. Calls init() when task a cancelation is intercepted"""
        try:
            if DEBUG: show_timer(f"{self.name}.run")
            self.timeout = False
            await asyncio.sleep(self.interval)
            self.timeout = True
            await self.callback()
        except asyncio.CancelledError:
            if DEBUG: show_timer(f"{self.name} is cancelled now from run")
            self.init()
        except Exception as e:
            if DEBUG: show_timer(f"{self.name}.run Exception : {type(e)}")
            # raise NotImplementedError

    async def cancel(self):
        """Cancels the internal asynchronous task"""
        if self.task:
            if DEBUG: show_timer(f"{self.name}.cancel")
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                if DEBUG: show_timer(f"{self.name} is cancelled now from cancel")
            except Exception as e:
                if DEBUG: show_timer(f"{self.name}.cancel Exception : {type(e)}")
                # raise NotImplementedError
            finally:
                self.init()
                return
        raise TimerStopError(f"{self.name} stop error")

    def init(self):
        """Internal function to initialize variables: task and timeout"""
        if DEBUG: show_timer(f"{self.name}.init")
        self.task = None
        self.timeout = False

    def isTimeout(self):
        """Returns True if time is out or interval is null"""
        if self.interval > 0:
            return self.timeout if self.task else False
        else:
            return True

    def setInterval(self, interval):
        """Setter for interval"""
        self.interval = self.checkInterval(interval)

    # def getInterval(self):
    #     return self.interval

    def checkInterval(self, interval):
        """Returns interval value if is an instance of integer and greater than zero else raise an error"""
        if isinstance(interval, int):
            if interval >= 0:
                return interval
            else:
                raise ValueError(f"{self.name} must be greater than or equals to 0")
        else:
            raise TypeError(f"{self.name} must be set to an integer")

    # def __str__(self):
    #     # since 3.8 self.taskget_coro()
    #     return "name:{self.name} interval:{self.interval} isrunning:{self.isrunning} task:{self.task} callback:{self.callback}".format(self=self)