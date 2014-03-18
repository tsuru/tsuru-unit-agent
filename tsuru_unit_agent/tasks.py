import subprocess


def execute_start_script():
    subprocess.call(["/var/lib/tsuru/start"])
