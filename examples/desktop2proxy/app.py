from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash
import csv
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
import paramiko
import requests
import socket
import telnetlib


app = Flask(__name__)
app.secret_key = 'please-change-me'
BASE_DIR = Path(__file__).parent
OUT_DIR = BASE_DIR / 'out'
OUT_DIR.mkdir(exist_ok=True)


TIMEOUT = 6


def run_nmap_quick(ip):
    try:
        ports = '22,23,21,80,443,445,3389,5900,161,5985,5986'
        p = subprocess.run(['nmap', '-sV', '-p', ports, ip, '-oX', '-'], capture_output=True, text=True, timeout=60)
        return p.stdout
    except Exception as e:
        return str(e)


def try_ssh(ip, user, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, port=22, username=user, password=pwd, timeout=TIMEOUT, banner_timeout=TIMEOUT, auth_timeout=TIMEOUT)
        stdin, stdout, stderr = client.exec_command('uname -a || ver', timeout=TIMEOUT)
        out = stdout.read().decode(errors='ignore')
        client.close()
        return True, out.strip()
    except Exception as e:
        return False, str(e)


def try_ftp(ip, user, pwd):
    try:
        import ftplib
        ftp = ftplib.FTP()
        ftp.connect(ip, 21, timeout=TIMEOUT)
        ftp.login(user, pwd)
        txt = ftp.getwelcome()
        ftp.quit()
        return True, txt
    except Exception as e:
        return False, str(e)


def try_http_basic(ip, user, pwd, https=False):
    proto = 'https' if https else 'http'
    url = f"{proto}://{ip}/"
    try:
        r = requests.get(url, auth=(user, pwd), timeout=TIMEOUT, verify=False)
        return r.status_code < 400, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)


def try_telnet(ip):
    try:
        tn = telnetlib.Telnet(ip, 23, timeout=TIMEOUT)
        b = tn.read_some().decode(errors='ignore')
        tn.close()
        return True, b
    except Exception as e:
        return False, str(e)


def try_smb(ip, user, pwd):
    try:
        p = subprocess.run(['smbclient', '-L', f'//{ip}/', '-U', f'{user}%{pwd}'], capture_output=True, text=True, timeout=20)
        ok = p.returncode == 0
        return ok, p.stdout + p.stderr
    except Exception as e:
        return False, str(e)


def parse_csv(stream):
    stream.seek(0)
    text = stream.read().decode('utf-8')
    reader = csv.DictReader(text.splitlines())
    items = []
    for r in reader:
        ip = r.get('ip') or r.get('host')
        u = r.get('username') or r.get('user') or r.get('login')
        p = r.get('password') or r.get('pass')
        if ip and u and p:
            items.append((ip.strip(), u.strip(), p.strip()))
    return items


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('file')
    if not f:
        flash('Файл не выбран')
        return redirect(url_for('index'))
    items = parse_csv(f.stream)
    if not items:
        flash('CSV не содержит ip/username/password')
        return redirect(url_for('index'))
    ts = int(time.time())
    out_json = OUT_DIR / f'results_{ts}.json'
    results = []
    by_ip = {}
    for ip, u, p in items:
        by_ip.setdefault(ip, []).append((u, p))

    for ip, creds in by_ip.items():
        rec = {'ip': ip, 'nmap': None, 'attempts': []}
        rec['nmap'] = run_nmap_quick(ip)
        for u, p in creds:
            ok, info = try_ssh(ip, u, p)
            rec['attempts'].append({'proto': 'ssh', 'user': u, 'pass': p, 'ok': ok, 'info': info})
            if ok:
                continue
            ok, info = try_ftp(ip, u, p)
            rec['attempts'].append({'proto': 'ftp', 'user': u, 'pass': p, 'ok': ok, 'info': info})
            ok, info = try_http_basic(ip, u, p, https=False)
            rec['attempts'].append({'proto': 'http', 'user': u, 'pass': p, 'ok': ok, 'info': info})
            ok, info = try_http_basic(ip, u, p, https=True)
            rec['attempts'].append({'proto': 'https', 'user': u, 'pass': p, 'ok': ok, 'info': info})
            ok, info = try_smb(ip, u, p)
            rec['attempts'].append({'proto': 'smb', 'user': u, 'pass': p, 'ok': ok, 'info': info})
        results.append(rec)
    with open(out_json, 'w', encoding='utf-8') as fo:
        json.dump(results, fo, indent=2, ensure_ascii=False)
    return redirect(url_for('results', fname=out_json.name))


@app.route('/results/<fname>')
def results(fname):
    path = OUT_DIR / fname
    if not path.exists():
        flash('Результаты не найдены')
        return redirect(url_for('index'))
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return render_template('results.html', results=data)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
