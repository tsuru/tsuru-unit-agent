import codecs
import collections
import io
import os
import os.path
import shutil
import string
import subprocess
import sys
import yaml
import json
import signal
from datetime import datetime
from threading import Thread

from honcho import procfile
from tsuru_unit_agent.stream import Stream

WATCHER_TEMPLATE = u"""
[watcher:{name}]
cmd = {cmd}
copy_env = True
uid = {user}
gid = {group}
working_dir = {working_dir}
stdout_stream.class = tsuru.stream.Stream
stdout_stream.watcher_name = {name}
stderr_stream.class = tsuru.stream.Stream
stderr_stream.watcher_name = {name}
"""


def process_output(in_fd, out_fd):
    for line in iter(in_fd.readline, b''):
        if line is None:
            break
        out_fd.write(line)
    out_fd.flush()
    in_fd.close()
    out_fd.close()

running_pipe = None


def sigterm_handler(signum, sigframe):
    try:
        running_pipe.send_signal(signal.SIGTERM)
    except:
        pass
    sys.exit(0)
signal.signal(signal.SIGTERM, sigterm_handler)


def exec_with_envs(commands, with_shell=False, working_dir="/home/application/current", pipe_output=False,
                   envs=None):
    global running_pipe
    if not envs:
        envs = {}
    app_envs = {}
    app_envs.update(os.environ)
    app_envs.update(envs)
    if not os.path.exists(working_dir):
        working_dir = "/"
    for command in commands:
        popen_output = None
        if pipe_output:
            popen_output = subprocess.PIPE
        pipe = subprocess.Popen(command, shell=with_shell, cwd=working_dir, env=app_envs,
                                stdout=popen_output, stderr=popen_output)
        running_pipe = pipe
        if pipe_output:
            stdout = Stream(echo_output=sys.stdout,
                            default_stream_name='stdout',
                            watcher_name='unit-agent',
                            envs=app_envs)
            stderr = Stream(echo_output=sys.stderr,
                            default_stream_name='stderr',
                            watcher_name='unit-agent',
                            envs=app_envs)
            stdout_thread = Thread(target=process_output, args=(pipe.stdout, stdout))
            stdout_thread.start()
            stderr_thread = Thread(target=process_output, args=(pipe.stderr, stderr))
            stderr_thread.start()
        status = pipe.wait()
        running_pipe = None
        if pipe_output:
            stdout_thread.join()
            stderr_thread.join()
        if status != 0:
            sys.exit(status)


def execute_start_script(start_cmd, envs=None, with_shell=True):
    exec_with_envs([start_cmd], with_shell=with_shell, envs=envs)


def run_build_hooks(app_data, envs=None):
    commands = (app_data.get('hooks') or {}).get('build') or []
    exec_with_envs(commands, with_shell=True, envs=envs)


def run_restart_hooks(position, app_data, envs=None):
    restart_hook = (app_data.get('hooks') or {}).get('restart') or {}
    commands = restart_hook.get('{}-each'.format(position)) or []
    commands += restart_hook.get(position) or []
    exec_with_envs(commands, with_shell=True, pipe_output=True,
                   envs=envs)


def load_app_yaml(working_dir="/home/application/current"):
    files_name = ["tsuru.yaml", "tsuru.yml", "app.yaml", "app.yml"]
    for file_name in files_name:
        try:
            fullpath = os.path.join(working_dir, file_name)
            with codecs.open(fullpath, 'r', encoding='utf-8', errors='ignore') as f:
                return yaml.load(f.read()) or {}
        except (IOError, yaml.scanner.ScannerError):
            pass
    return {}


def write_circus_conf(procfile_path=None, conf_path="/etc/circus/circus.ini",
                      envs=None):
    if not envs:
        envs = {}
    expanding_envs = collections.defaultdict(str)
    expanding_envs.update(os.environ)
    expanding_envs.update(envs)
    procfile_path = procfile_path or os.environ.get("PROCFILE_PATH",
                                                    "/home/application/current/Procfile")
    content = ""
    with open(procfile_path) as f:
        content = f.read()
    pfile = procfile.Procfile(content)
    new_watchers = []
    working_dir = os.environ.get("APP_WORKING_DIR", "/home/application/current")
    for name, cmd in pfile.commands.items():
        cmd = string.Template(cmd).substitute(expanding_envs)
        new_watchers.append(WATCHER_TEMPLATE.format(name=name, cmd=cmd,
                                                    user="ubuntu", group="ubuntu",
                                                    working_dir=working_dir))
    base_conf = conf_path + ".base"
    if os.path.exists(conf_path):
        if not os.path.exists(base_conf):
            shutil.copy2(conf_path, base_conf)
        shutil.copy2(base_conf, conf_path)
    if new_watchers:
        with open(conf_path, "a") as f:
            for watcher in new_watchers:
                f.write(watcher)


def save_apprc_file(environs, file_path="/home/application/apprc"):
    with io.open(file_path, "w") as file:
        file.write(u"# generated by tsuru at {}\n".format(datetime.now()))
        for name, value in environs.iteritems():
            value = value.replace("'", "'\\''")
            file.write(u"export {}='{}'\n".format(name, value))


def parse_apprc_file(file_path="/home/application/apprc"):
    # Let the shell parse environment variables for us, there are escaping
    # edge cases we don't want to be aware of.
    pipe = subprocess.Popen('source {}; python -c "import os, json; e=dict(); '.format(file_path) +
                            'e.update(os.environ); print json.dumps(e)"',
                            shell=True, env={}, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = pipe.communicate()
    return json.loads(result[0])
