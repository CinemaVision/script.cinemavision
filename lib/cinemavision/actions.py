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
        if self.args:
            data = self.args[0]
            if data.startswith('PUT:'):
                data = data[4:].lstrip()
                resp = requests.put(self.commandData, headers=headers, data=data)
            elif data.startswith('DELETE:'):
                data = data[7:].lstrip()
                resp = requests.delete(self.commandData)
            elif data.startswith('HEADERS:'):
                headers = json.loads(data[8:].lstrip())
            else:
                if data.startswith('POST:'):
                    data = data[5:].lstrip()
                resp = requests.post(self.commandData, headers=headers, data=data)
        else:
            resp = requests.get(self.commandData)

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
        for c in self.commands:
            c._threadedExecute()

    def _loadCommands(self):
        data = self.readFile()
        command = None
        for line in data.splitlines():
            if line:
                if line.startswith('#'):
                    continue
                elif line.startswith('\\'):
                    line = line[1:]

                if command:
                    command.addArg(line)
                else:
                    name, data = line.split('://', 1)
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
            else:
                if command:
                    self.commands.append(command)
                command = None

        if command:
            self.commands.append(command)
