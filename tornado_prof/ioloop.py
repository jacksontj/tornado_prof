import sys
import select

import tornado.gen
import tornado.ioloop


# TODO: Method for getting/resetting the metrics
class ProfilingIOLoop(tornado.ioloop.PollIOLoop):
    """An IOLoop which keeps metrics on callback/coroutine execution times
    """
    def initialize(self, impl=None, **kwargs):
        # TODO: I don't like re-implementing the "select" selection here
        if hasattr(select, "epoll"):
            impl = select.epoll()
        elif hasattr(select, "kqueue"):
            impl = select.kqueue()
        else:
            impl = select.select()
        super(ProfilingIOLoop, self).initialize(impl=impl, **kwargs)

        # Whether we should collect timing info
        self.timing_enabled = True

        # Dict to store timing data in
        self._timing = {}

        # map of filename -> module for generators that we see
        self._generator_map = {}

    def get_timings(self, reset=True):
        """Method to return timing data from the IOLoop
        """
        if reset:
            tmp = self._timing
            self._timing = {}
            return tmp
        else:
            return self._timing

    def _store_timing(self, key, took):
        """Store timing information internally
        """
        # Store the metrics
        try:
            self._timing[key]['sum'] += took
            self._timing[key]['count'] += 1
            self._timing[key]['max'] = max(self._timing[key]['max'], took)
        except KeyError:
            self._timing[key] = {'sum': took, 'count': 1, 'max': took}

    def _run_callback(self, callback):
        """To keep track of how long everything took we need to wrap _run_callback

        This method is called with two groups of things (1) callbacks and (2) coroutines

        #1 Callbacks
            Callbacks are relatively simple, we just need to keep track of how long they took

        #2 Coroutines
            These are a bit trickier-- as they will yield and call back etc. We need to
            do some additional unwrapping to make sure we account correctly
        """
        if not self.timing_enabled:
            return super(ProfilingIOLoop, self)._run_callback(callback)

        start = self.time()
        ret = super(ProfilingIOLoop, self)._run_callback(callback)
        try:
            took = self.time() - start

            try:
                # If we are a coroutine, there are 2 paths we can have here
                coroutine = callback.func.func_closure[-1].cell_contents.func_closure[0].cell_contents

                # (1) If this is a Runner (from a yield)
                if isinstance(coroutine, tornado.gen.Runner):
                    key = (
                        coroutine.gen.gi_code.co_filename,
                        coroutine.gen.gi_code.co_name,
                        coroutine.gen.gi_code.co_firstlineno,
                    )
                # (2) Otherwise this is the first call of a coroutine
                else:
                    key = (
                        coroutine.func_code.co_filename,
                        coroutine.func_code.co_name,
                        coroutine.func_code.co_firstlineno,
                    )
            except:
                # If this wasn't a coroutine, then this is a straight callback
                key = (
                    callback.func.func_closure[-1].cell_contents.func_code.co_filename,
                    callback.func.func_closure[-1].cell_contents.func_code.co_name,
                    callback.func.func_closure[-1].cell_contents.func_code.co_firstlineno,
                )

            self._store_timing(key, took)
        except KeyboardInterrupt:
            raise
        except:
            # TODO: log an error-- since we goofed somehow, but we don't want to break
            # IOLoop processing
            pass
        finally:
            return ret
