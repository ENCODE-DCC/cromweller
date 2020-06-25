"""This does not cover all CLI parameters defined in caper/caper_args.py.
gcp (Google Cloud Platform) backend is tested here with server/client functions.
"""
import os
import time

from caper.cli import main as cli_main
from caper.cromwell_rest_api import CromwellRestAPI
from caper.wdl_parser import WDLParser

from .example_wdl import make_directory_with_wdls

TIMEOUT_SERVER_SPIN_UP = 240
TIMEOUT_SERVER_RUN_WORKFLOW = 480


def test_server_client(tmp_path, gcs_root, ci_prefix, cromwell, womtool, gcp_prj):
    """Test server, client stuffs
    """
    # server command line
    server_port = 8015

    out_gcs_bucket = os.path.join(gcs_root, 'caper_out', ci_prefix)
    tmp_gcs_bucket = os.path.join(gcs_root, 'caper_tmp')

    cmd = ['server']
    cmd += ['--tmp-dir', str(tmp_path / 'tmp_dir')]
    cmd += ['--backend', 'gcp']
    cmd += ['--gcp-prj', gcp_prj]
    cmd += ['--out-gcs-bucket', out_gcs_bucket]
    cmd += ['--gcp-memory-retry-error-keys', 'OutOfMemory,Killed']
    cmd += ['--gcp-memory-retry-multiplier', '1.3']
    cmd += ['--tmp-gcs-bucket', tmp_gcs_bucket]
    cmd += ['--cromwell-stdout', str(tmp_path / 'cromwell_stdout.o')]
    # test with file type DB
    cmd += ['--db', 'file']
    cmd += ['--db-timeout', '50000']
    cmd += ['--file-db', str(tmp_path / 'file_db_prefix')]
    cmd += ['--max-concurrent-tasks', '2']
    cmd += ['--max-concurrent-workflows', '2']
    cmd += ['--disable-call-caching']
    cmd += ['--local-hash-strat', 'path']
    cmd += ['--out-dir', str(tmp_path / 'out_dir')]
    cmd += ['--cromwell', cromwell]
    cmd += ['--java-heap-server', '4G']
    cmd += ['--port', str(server_port)]
    print(' '.join(cmd))

    try:
        th = cli_main(cmd, nonblocking_server=True)

        # wait until server is ready to take submissions
        t_start = time.time()
        while th.status is None:
            time.sleep(1)
            if time.time() - t_start > TIMEOUT_SERVER_SPIN_UP:
                raise TimeoutError('Timed out waiting for Cromwell server spin-up.')

        # prepare WDLs and input JSON, imports to be submitted
        make_directory_with_wdls(str(tmp_path))
        wdl = tmp_path / 'main.wdl'
        inputs = tmp_path / 'inputs.json'
        p = WDLParser(str(wdl))
        imports = p.zip_subworkflows(str(tmp_path / 'imports.zip'))

        # test "submit" with on_hold
        cmd = ['submit', str(wdl)]
        cmd += ['--inputs', str(inputs)]
        cmd += ['--imports', str(imports)]
        cmd += ['--gcp-zones', 'us-central1']
        cmd += ['--ignore-womtool']
        cmd += ['--java-heap-womtool', '2G']
        cmd += ['--max-retries', '1']
        cmd += ['--docker', 'ubuntu:latest']
        cmd += ['--backend', 'gcp']
        cmd += ['--hold']
        cli_main(cmd)

        time.sleep(5)

        # find workflow ID
        cra = CromwellRestAPI(hostname='localhost', port=server_port)
        workflow_id = cra.find(['*'])[0]['id']

        m = cra.get_metadata([workflow_id])[0]
        assert m['status'] == 'On Hold'

        # unhold it
        cmd = ['unhold', workflow_id]
        cli_main(cmd)

        time.sleep(5)

        m = cra.get_metadata([workflow_id])[0]
        assert m['status'] in ('Submitted', 'Running')

        t_start = time.time()
        while True:
            time.sleep(5)
            m = cra.get_metadata([workflow_id])[0]
            print('polling: ', workflow_id, m['status'])
            if m['status'] in ('Done', 'Failed', 'Succeeded'):
                break
            if time.time() - t_start > TIMEOUT_SERVER_RUN_WORKFLOW:
                raise TimeoutError('Timed out waiting for workflow being done.')

    finally:
        # all done. so stop the server
        th.stop()
        th.join()
