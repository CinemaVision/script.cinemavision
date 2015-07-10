import xbmc
import json


class JSONRPCMethod:
    def __init__(self):
        self.family = None

    def __getattr__(self, method):
        def handler(**kwargs):
            command = {
                'jsonrpc': '2.0',
                'id': 1,
                'method': '{0}.{1}'.format(self.family, method)
            }

            if kwargs:
                command['params'] = kwargs

            print json.dumps(command)

            return json.loads(xbmc.executeJSONRPC(json.dumps(command)))

        return handler

    def __call__(self, family):
        self.family = family
        return self


class KodiJSONRPC:
    def __init__(self):
        self.methodHandler = JSONRPCMethod()

    def __getattr__(self, family):
        return self.methodHandler(family)
