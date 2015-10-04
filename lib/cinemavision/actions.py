import os
import util
import threading


class ActionCommand:
    type = None

    def __init__(self, data):
        self.thread = None
        self.commandData = data
        self.args = []

    def addArg(self, arg):
        self.args.append(arg)

    def _threadedExecute(self):
        self.thread = threading.Thread(target=self.execute)
        self.thread.start()

    def execute(self):
        return False


class SleepCommand(ActionCommand):
    type = 'SLEEP'

    def _threadedExecute(self):
        import time

        try:
            ms = int(self.commandData)
        except:
            util.ERROR()

        time.sleep(ms/1000.0)


class ModuleCommand(ActionCommand):
    type = 'MODULE'
    importPath = os.path.join(util.STORAGE_PATH, 'import')

    def checkImportPath(self):
        import os
        if not os.path.exists(self.importPath):
            os.makedirs(self.importPath)

    def copyModule(self):
        import shutil
        shutil.copyfile(self.commandData, os.path.join(self.importPath, 'cinema_vision_command_module.py'))

    def execute(self):
        self.checkImportPath()
        self.copyModule()

        import sys
        if self.importPath not in sys.path:
            sys.path.append(self.importPath)

        import cinema_vision_command_module
        cinema_vision_command_module.main(*self.args)


class ScriptCommand(ActionCommand):
    type = 'SCRIPT'

    def execute(self):
        command = ['python', self.commandData]
        command += self.args

        import subprocess

        util.DEBUG_LOG('Action (Script) Command: {0}'.format(repr(' '.join(command))))
        subprocess.Popen(command)


class CommandCommand(ActionCommand):
    type = 'COMMAND'

    def execute(self):
        command = [self.commandData]
        command += self.args

        import subprocess

        util.DEBUG_LOG('Action (Script) Command: {0}'.format(repr(' '.join(command))))
        subprocess.Popen(command)


class AddonCommand(ActionCommand):
    type = 'ADDON'

    def execute(self):
        try:
            import xbmc
        except:
            return False

        xbmc.executebuiltin('RunScript({commandData},{args})'.format(commandData=self.commandData, args=','.join(self.args)))
        return True


class HTTPCommand(ActionCommand):
    type = 'HTTP'

    def execute(self):
        import requests
        import json

        headers = None
        method = None
        data = None
        args = list(self.args)

        while args:
            arg = args.pop()
            if arg.startswith('PUT:'):
                data = arg[4:].lstrip()
                method = requests.put
            elif arg.startswith('DELETE:'):
                method = requests.delete
            elif arg.startswith('HEADERS:'):
                headers = json.loads(arg[8:].lstrip())
            else:
                if arg.startswith('POST:'):
                    data = arg[5:].lstrip()
                    method = requests.post
                else:
                    data = arg
                    method = method or requests.post
        else:
            if method:
                resp = method(self.commandData, headers=headers, data=data)
            else:
                resp = requests.get(self.commandData, headers=headers)

        util.DEBUG_LOG('Action (HTTP) Response: {0}'.format(repr(resp.text)))


class ActionFileProcessor:
    def __init__(self, path):
        self.path = path
        self.commands = []
        self.init()

    def __repr__(self):
        return 'AFP ({0})'.format(','.join([a.type for a in self.commands]))

    def init(self):
        try:
            self._loadCommands()
        except:
            util.ERROR()

    def readFile(self):
        with util.vfs.File(self.path, 'r') as f:
            return f.read()

    def run(self):
        threading.Thread(target=self._run).start()

    def _run(self):
        for c in self.commands:
            c._threadedExecute()

    def _loadCommands(self):
        data = self.readFile()
        command = None
        lineno = 0
        for line in data.splitlines():
            lineno += 1
            if line:
                if line.startswith('#'):
                    continue
                elif line.startswith('\\'):
                    line = line[1:]

                if command:
                    command.addArg(line)
                else:
                    try:
                        name, data = line.split('://', 1)
                    except ValueError:
                        util.DEBUG_LOG('    -| ACTION ERROR (line {0}): {1}'.format(lineno, repr(self.path)))
                        util.DEBUG_LOG('    -| {0}'.format(repr(line)))
                        util.DEBUG_LOG('    -| First action line must have the form: protocol://whatever')
                        return

                    if name in ('http', 'https'):
                        command = HTTPCommand(name + '://' + data)
                    elif name == 'script':
                        command = ScriptCommand(data)
                    elif name == 'addon':
                        command = AddonCommand(data)
                    elif name == 'module':
                        command = ModuleCommand(data)
                    elif name == 'command':
                        command = CommandCommand(data)
                    elif name == 'sleep':
                        command = SleepCommand(data)
            else:
                if command:
                    self.commands.append(command)
                command = None

        if command:
            self.commands.append(command)
