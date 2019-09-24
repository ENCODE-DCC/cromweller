#!/usr/bin/env python3
"""CaperCheck: Caper arguments/configuration checker

Author:
    Jin Lee (leepc12@gmail.com) at ENCODE-DCC
"""

import os


DEFAULT_FILE_DB_PREFIX = 'caper_file_db'


def check_caper_conf(args_d):
    """Check arguments/configuration for Caper
    """
    docker = args_d.get('docker')
    if docker is not None:
        use_docker = True
    else:
        use_docker = False
    if isinstance(docker, list):
        if len(docker) > 0:
            docker = docker[0]
        else:
            docker = None
    elif isinstance(docker, str) and docker == '':
        docker = None
    args_d['docker'] = docker
    args_d['use_docker'] = use_docker

    singularity = args_d.get('singularity')
    if singularity is not None:
        use_singularity = True
    else:
        use_singularity = False
    if isinstance(singularity, list):
        if len(singularity) > 0:
            singularity = singularity[0]
        else:
            singularity = None
    elif isinstance(singularity, str) and singularity == '':
        singularity = None
    args_d['singularity'] = singularity
    args_d['use_singularity'] = use_singularity

    if use_docker and use_singularity:
        raise Exception('--docker and --singularity are mutually exclusive')

    # init some important path variables
    if args_d.get('out_dir') is None:
        args_d['out_dir'] = os.getcwd()

    if args_d.get('tmp_dir') is None:
        args_d['tmp_dir'] = os.path.join(args_d['out_dir'], '.caper_tmp')

    if args_d.get('tmp_s3_bucket') is None:
        if args_d.get('out_s3_bucket'):
            args_d['tmp_s3_bucket'] = os.path.join(args_d['out_s3_bucket'],
                                                   '.caper_tmp')
    if args_d.get('tmp_gcs_bucket') is None:
        if args_d.get('out_gcs_bucket'):
            args_d['tmp_gcs_bucket'] = os.path.join(args_d['out_gcs_bucket'],
                                                    '.caper_tmp')
    backend = args_d.get('backend')
    if backend is not None:
        if backend == 'google':
            backend = 'gcp'
        elif backend == 'amazon':
            backend = 'aws'
        args_d['backend'] = backend

    file_db = args_d.get('file_db')
    if file_db is not None:
        file_db = os.path.abspath(os.path.expanduser(file_db))
    else:
        basename = DEFAULT_FILE_DB_PREFIX
        out_dir = args_d['out_dir']
        inputs = args_d.get('inputs')
        if inputs is not None:
            inputs_wo_ext, ext = os.path.splitext(
                os.path.basename(inputs))
            basename += '.' + inputs_wo_ext
        file_db = os.path.join(out_dir, basename)
    args_d['file_db'] = file_db

    singularity_cachedir = args_d.get('singularity_cachedir')
    if singularity_cachedir is not None:
        singularity_cachedir = os.path.abspath(
            os.path.expanduser(singularity_cachedir))
        args_d['singularity_cachedir'] = singularity_cachedir
        os.makedirs(singularity_cachedir, exist_ok=True)

    if args_d.get('str_label') is None:
        if args_d.get('inputs') is not None:
            basename = os.path.basename(args_d['inputs'])
            args_d['str_label'] = os.path.splitext(basename)[0]

    return args_d
