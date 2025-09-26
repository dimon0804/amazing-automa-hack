import io
import pytest

from app import app as flask_app


@pytest.fixture()
def client():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as c:
        yield c


def test_index_page(client):
    r = client.get('/')
    assert r.status_code == 200
    assert b'Desktop2Proxy' in r.data


def test_upload_and_results_flow(monkeypatch, client):
    # Mock heavy network functions
    import app as module

    monkeypatch.setattr(module, 'run_nmap_quick', lambda ip: '<nmap xml>')
    monkeypatch.setattr(module, 'try_ssh', lambda ip,u,p: (False, 'ssh failed'))
    monkeypatch.setattr(module, 'try_ftp', lambda ip,u,p: (False, 'ftp failed'))
    monkeypatch.setattr(module, 'try_http_basic', lambda ip,u,p,https=False: (False, 'http 401'))
    monkeypatch.setattr(module, 'try_smb', lambda ip,u,p: (False, 'smb denied'))

    csv_content = 'ip,username,password\n127.0.0.1,admin,admin\n'
    data = {
        'file': (io.BytesIO(csv_content.encode('utf-8')), 'creds.csv')
    }

    r = client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=False)
    # Should redirect to /results/...
    assert r.status_code in (302, 303)
    assert '/results/' in r.headers.get('Location', '')

    # Follow the redirect
    res = client.get(r.headers['Location'])
    assert res.status_code == 200
    assert b'127.0.0.1' in res.data
