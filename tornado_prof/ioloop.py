import select

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

        # Dict to store timing data in
        self._timing = {}

    def get_timings(self, reset=True):
        """Method to return timing data from the IOLoop
        """
        if reset:
            tmp = self._timing
            self._timing = {}
            return tmp
        else:
            return self._timing

    def _run_callback(self, callback):
        """To keep track of how long everything took we need to wrap _run_callback

        This method is called with two groups of things (1) callbacks and (2) coroutines

        #1 Callbacks
            Callbacks are relatively simple, we just need to keep track of how long they took

        #2 Coroutines
            These are a bit trickier-- as they will yield and call back etc. We need to
            do some additional unwrapping to make sure we account correctly
        """
        start = self.time()
        ret = super(ProfilingIOLoop, self)._run_callback(callback)
        took = self.time() - start

        # TODO: find a way to get filename from function?
        # Key will be (module, function_name)
        key = (callback.func.func_closure[-1].cell_contents.__module__, callback.func.func_closure[-1].cell_contents.func_name)

        # TODO: less magic way to do this?
        # If the callback is actually from the tornado.gen section as a lambda we need
        # to figure out if this is a wrapped coroutine
        if key == ('tornado.gen', '<lambda>'):
            # Key will be (filename, function_name)
            # TODO: find a way to get module name from generator? -- otherwise subsequent
            # yields of a coroutine end up showing up as a filepath instead of the module name
            try:
                key = (
                    callback.func.func_closure[-1].cell_contents.func_closure[0].cell_contents.gen.gi_code.co_filename,
                    callback.func.func_closure[-1].cell_contents.func_closure[0].cell_contents.gen.gi_code.co_name,
                )
            except AttributeError:
                return ret

        # TODO: better (faster?) metrics?
        try:
            self._timing[key]['sum'] += took
            self._timing[key]['count'] += 1
            self._timing[key]['max'] = max(self._timing[key]['max'], took)
        except KeyError:
            self._timing[key] = {'sum': took, 'count': 1, 'max': took}
        # Print out the timing info of callbacks
        #print (self._timing)
        return ret
