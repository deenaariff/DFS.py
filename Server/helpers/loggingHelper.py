class Logger:

    def __init__(self, display):
        self.display_logs = display

    # Output in Logs with a given context
    def output(self, context, msg):
        if self.display_logs:
            print "[" + context + "]: " + msg

