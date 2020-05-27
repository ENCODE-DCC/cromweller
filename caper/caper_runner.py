import logging
import os

from autouri import AbsPath, AutoURI

from .caper_backend_conf import CaperBackendConf
from .caper_base import CaperBase
from .caper_labels import CaperLabels
from .caper_wdl_parser import CaperWDLParser
from .caper_workflow_opts import CaperWorkflowOpts
from .cromwell import Cromwell
from .cromwell_backend import (CromwellBackendBase, CromwellBackendCommon,
                               CromwellBackendDatabase, CromwellBackendGCP,
                               CromwellBackendLocal)
from .cromwell_metadata import CromwellMetadata
from .cromwell_rest_api import CromwellRestAPI
from .server_heartbeat import ServerHeartbeat
from .singularity import Singularity

logger = logging.getLogger(__name__)


class CaperRunner(CaperBase):
    DEFAULT_FILE_DB_PREFIX = 'default_caper_file_db'
    BASENAME_CROMWELL_STDOUT = 'cromwell.out'
    SERVER_TMP_DIR_PREFIX = '.caper_server'

    def __init__(
        self,
        tmp_dir,
        default_backend,
        out_dir,
        tmp_gcs_bucket=None,
        tmp_s3_bucket=None,
        server_heartbeat_file=CaperBase.DEFAULT_SERVER_HEARTBEAT_FILE,
        server_heartbeat_timeout=ServerHeartbeat.DEFAULT_HEARTBEAT_TIMEOUT_MS,
        server_port=CromwellRestAPI.DEFAULT_PORT,
        cromwell=Cromwell.DEFAULT_CROMWELL,
        womtool=Cromwell.DEFAULT_WOMTOOL,
        java_heap_server=Cromwell.DEFAULT_JAVA_HEAP_CROMWELL_SERVER,
        java_heap_run=Cromwell.DEFAULT_JAVA_HEAP_CROMWELL_RUN,
        java_heap_womtool=Cromwell.DEFAULT_JAVA_HEAP_WOMTOOL,
        disable_call_caching=False,
        max_concurrent_workflows=CromwellBackendCommon.DEFAULT_MAX_CONCURRENT_WORKFLOWS,
        max_concurrent_tasks=CromwellBackendBase.DEFAULT_CONCURRENT_JOB_LIMIT,
        soft_glob_output=False,
        local_hash_strat=CromwellBackendLocal.DEFAULT_LOCAL_HASH_STRAT,
        db=CromwellBackendDatabase.DEFAULT_DB,
        db_timeout=CromwellBackendDatabase.DEFAULT_DB_TIMEOUT_MS,
        mysql_db_ip=CromwellBackendDatabase.DEFAULT_MYSQL_DB_IP,
        mysql_db_port=CromwellBackendDatabase.DEFAULT_MYSQL_DB_PORT,
        mysql_db_user=CromwellBackendDatabase.DEFAULT_MYSQL_DB_USER,
        mysql_db_password=CromwellBackendDatabase.DEFAULT_MYSQL_DB_PASSWORD,
        mysql_db_name=CromwellBackendDatabase.DEFAULT_MYSQL_DB_NAME,
        postgresql_db_ip=CromwellBackendDatabase.DEFAULT_POSTGRESQL_DB_IP,
        postgresql_db_port=CromwellBackendDatabase.DEFAULT_POSTGRESQL_DB_PORT,
        postgresql_db_user=CromwellBackendDatabase.DEFAULT_POSTGRESQL_DB_USER,
        postgresql_db_password=CromwellBackendDatabase.DEFAULT_POSTGRESQL_DB_PASSWORD,
        postgresql_db_name=CromwellBackendDatabase.DEFAULT_POSTGRESQL_DB_NAME,
        file_db=None,
        gcp_prj=None,
        gcp_call_caching_dup_strat=CromwellBackendGCP.DEFAULT_GCP_CALL_CACHING_DUP_STRAT,
        out_gcs_bucket=None,
        aws_batch_arn=None,
        aws_region=None,
        out_s3_bucket=None,
        gcp_zones=None,
        slurm_partition=None,
        slurm_account=None,
        slurm_extra_param=None,
        sge_pe=None,
        sge_queue=None,
        sge_extra_param=None,
        pbs_queue=None,
        pbs_extra_param=None,
    ):
        """See docstring of base class for other arguments.

        Args:
            default_backend:
                Default backend.
            server_port:
                Server port for server mode only.
            cromwell:
                Cromwell JAR URI.
            womtool:
                Womtool JAR URI.

            java_heap_server:
                For this and all below arguments,
                see details in CaperBackendConf.__init__.
            java_heap_womtool:
            disable_call_caching:
            max_concurrent_workflows:
            max_concurrent_tasks:
            soft_glob_output:
            local_hash_strat:
            db:
            db_timeout:
            mysql_db_ip:
            mysql_db_port:
            mysql_db_user:
            mysql_db_password:
            mysql_db_name:
            postgresql_db_ip:
            postgresql_db_port:
            postgresql_db_user:
            postgresql_db_password:
            postgresql_db_name:
            file_db:
            gcp_prj:
            gcp_call_caching_dup_strat:
            out_gcs_bucket:
            aws_batch_arn:
            aws_region:
            out_s3_bucket:
            gcp_zones:
            slurm_partition:
            slurm_account:
            slurm_extra_param:
            sge_pe:
            sge_queue:
            sge_extra_param:
            pbs_queue:
            pbs_extra_param:

            gcp_zones:
                For this and all below arguments,
                see details in CaperWorkflowOpts.__init__.
            slurm_partition:
            slurm_account:
            slurm_extra_param:
            sge_pe:
            sge_queue:
            sge_extra_param:
            pbs_queue:
            pbs_extra_param:
        """
        super().__init__(
            tmp_dir=tmp_dir,
            tmp_gcs_bucket=tmp_gcs_bucket,
            tmp_s3_bucket=tmp_s3_bucket,
            server_heartbeat_file=server_heartbeat_file,
            server_heartbeat_timeout=server_heartbeat_timeout,
        )

        self._cromwell = Cromwell(
            cromwell=cromwell,
            womtool=womtool,
            java_heap_cromwell_server=java_heap_server,
            java_heap_cromwell_run=java_heap_run,
            java_heap_womtool=java_heap_womtool,
            server_port=server_port,
            server_heartbeat=self._server_heartbeat,
        )

        self._caper_backend_conf = CaperBackendConf(
            default_backend=default_backend,
            out_dir=out_dir,
            server_port=server_port,
            disable_call_caching=disable_call_caching,
            max_concurrent_workflows=max_concurrent_workflows,
            max_concurrent_tasks=max_concurrent_tasks,
            soft_glob_output=soft_glob_output,
            local_hash_strat=local_hash_strat,
            db=db,
            db_timeout=db_timeout,
            file_db=file_db,
            mysql_db_ip=mysql_db_ip,
            mysql_db_port=mysql_db_port,
            mysql_db_user=mysql_db_user,
            mysql_db_password=mysql_db_password,
            mysql_db_name=mysql_db_name,
            postgresql_db_ip=postgresql_db_ip,
            postgresql_db_port=postgresql_db_port,
            postgresql_db_user=postgresql_db_user,
            postgresql_db_password=postgresql_db_password,
            postgresql_db_name=postgresql_db_name,
            gcp_prj=gcp_prj,
            out_gcs_bucket=out_gcs_bucket,
            gcp_call_caching_dup_strat=gcp_call_caching_dup_strat,
            aws_batch_arn=aws_batch_arn,
            aws_region=aws_region,
            out_s3_bucket=out_s3_bucket,
            gcp_zones=gcp_zones,
            slurm_partition=slurm_partition,
            slurm_account=slurm_account,
            slurm_extra_param=slurm_extra_param,
            sge_pe=sge_pe,
            sge_queue=sge_queue,
            sge_extra_param=sge_extra_param,
            pbs_queue=pbs_queue,
            pbs_extra_param=pbs_extra_param,
        )

        self._caper_workflow_opts = CaperWorkflowOpts(
            gcp_zones=gcp_zones,
            slurm_partition=slurm_partition,
            slurm_account=slurm_account,
            slurm_extra_param=slurm_extra_param,
            sge_pe=sge_pe,
            sge_queue=sge_queue,
            sge_extra_param=sge_extra_param,
            pbs_queue=pbs_queue,
            pbs_extra_param=pbs_extra_param,
        )

        self._caper_labels = CaperLabels()

    def run(
        self,
        backend,
        wdl,
        inputs=None,
        options=None,
        labels=None,
        imports=None,
        metadata_output=None,
        str_label=None,
        user=None,
        docker=None,
        singularity=None,
        singularity_cachedir=Singularity.DEFAULT_SINGULARITY_CACHEDIR,
        no_build_singularity=False,
        custom_backend_conf=None,
        max_retries=CaperWorkflowOpts.DEFAULT_MAX_RETRIES,
        ignore_womtool=False,
        no_deepcopy=False,
        file_stdout=None,
        fileobj_troubleshoot=None,
        tmp_dir=None,
        dry_run=False,
    ):
        """Run a workflow using Cromwell run mode.

        Args:
            backend:
                Choose among Caper's built-in backends.
                (aws, gcp, Local, slurm, sge, pbs).
                Or use a backend defined in your custom backend config file
                (above "backend_conf" file).
            wdl:
                WDL file.
            inputs:
                Input JSON file. Cromwell's parameter -i.
            options:
                Workflow options JSON file. Cromwell's parameter -o.
            labels:
                Labels JSON file. Cromwell's parameter -l.
            imports:
                imports ZIP file. Cromwell's parameter -p.
            metadata_output:
                Output metadata file path. Metadata JSON file will be written to
                this path. Caper also automatiacally generates it on each workflow's
                root directory.  Cromwell's parameter -m.
            str_label:
                Caper's string label, which will be written
                to labels JSON object.
            user:
                Username. If not defined, find username from system.
            docker:
                Docker image to run a workflow on.
                This will be overriden by "docker" attr defined in
                WDL's task's "runtime {} section.

                If this is None:
                    Docker will not be used for this workflow.
                If this is an emtpy string (working like a flag):
                    Docker will be used. Caper will try to find docker image
                    in WDL (from a comment "#CAPER docker" or
                    from workflow.meta.caper_docker).
            singularity:
                Singularity image to run a workflow on.
                This will be overriden by "singularity" attr defined in
                WDL's task's "runtime {} section.

                If this is None:
                    Singularity will not be used for this workflow.
                If this is an emtpy string:
                    Singularity will be used. Caper will try to find Singularity image
                    in WDL (from a comment "#CAPER singularity" or
                    from workflow.meta.caper_singularlity).
            singularity_cachedir:
                Cache directory for local Singularity images.
                If there is a shell environment variable SINGULARITY_CACHEDIR
                define then this parameter will be ignored.
            no_build_singularity:
                Do not build local singularity image.
                However, a local singularity image will be eventually built on
                env var SINGULARITY_CACHEDIR.
                Therefore, use this flag if you have already built it.
            custom_backend_conf:
                Backend config file (HOCON) to override Caper's
                auto-generated backend config.
            max_retries:
                Number of retrial for a failed task in a workflow.
                This applies to every task in a workflow.
                0 means no retrial. "attemps" attribute in a task's metadata
                increments from 1 as it is retried. attempts==2 means first retrial.
            ignore_womtool:
                Disable Womtool validation for WDL/input JSON/imports.
            no_deepcopy:
                Disable recursive localization of files defined in input JSON.
                Input JSON file itself will still be localized.
            file_stdout:
                File to write Cromwell's STDOUT to.
                If None, then will be written to cromwell.o on tmp_dir.
                Note that STDERR is redirected to STDOUT.
            fileobj_troubleshoot:
                File-like object to print out auto-troubleshooting after workflow is done.
            tmp_dir:
                Local temporary directory to store all temporary files.
                Temporary files mean intermediate files used for running Cromwell.
                For example, backend config file, workflow options file.
                Localized (recursively) data files defined in input JSON
                will NOT be stored here.
                They will be localized on self._tmp_dir instead.
                If this is not defined, then cache directory self._tmp_dir will be used.
            dry_run:
                Stop before running Java command line for Cromwell.

        Returns:
            metadata_file:
                URI of metadata JSON file.
        """
        u_wdl = AutoURI(wdl)
        if not u_wdl.exists:
            raise FileNotFoundError('WDL does not exists. {wdl}'.format(wdl=wdl))

        if str_label is None and inputs:
            str_label = AutoURI(inputs).basename_wo_ext

        if tmp_dir is None:
            tmp_dir = self.create_timestamped_tmp_dir(prefix=u_wdl.basename_wo_ext)

        logger.info('Localizing files on tmp_dir. {d}'.format(d=tmp_dir))
        wdl = u_wdl.localize_on(tmp_dir)

        if inputs:
            inputs = self.localize_on_backend(
                inputs, backend=backend, recursive=not no_deepcopy, make_md5_file=True
            )

        wdl_parser = CaperWDLParser(wdl)
        if imports:
            imports = AutoURI(imports).localize_on(tmp_dir)
        else:
            imports = wdl_parser.create_imports_file(tmp_dir)

        if metadata_output:
            if not AbsPath(metadata_output).is_valid:
                raise ValueError(
                    'metadata_output is not a valid local abspath. {m}'.format(
                        m=metadata_output
                    )
                )
        else:
            metadata_output = os.path.join(
                tmp_dir, CromwellMetadata.DEFAULT_METADATA_BASENAME
            )

        backend_conf = self._caper_backend_conf.create_file(
            directory=tmp_dir, backend=backend, custom_backend_conf=custom_backend_conf
        )

        options = self._caper_workflow_opts.create_file(
            directory=tmp_dir,
            wdl=wdl,
            inputs=inputs,
            custom_options=options,
            docker=docker,
            singularity=singularity,
            singularity_cachedir=singularity_cachedir,
            backend=backend,
            max_retries=max_retries,
        )

        labels = self._caper_labels.create_file(
            directory=tmp_dir,
            backend=backend,
            custom_labels=labels,
            str_label=str_label,
            user=user,
        )

        if not ignore_womtool:
            self._cromwell.validate(wdl=wdl, inputs=inputs, imports=imports)

        logger.info(
            'run ready: wdl={w}, inputs={i}, backend_conf={b}'.format(
                w=wdl, i=inputs, b=backend_conf
            )
        )
        if dry_run:
            return None

        if file_stdout is None:
            file_stdout = os.path.join(tmp_dir, CaperRunner.BASENAME_CROMWELL_STDOUT)
        logger.info('run launched: stdout={stdout}'.format(stdout=file_stdout))

        with open(file_stdout, 'w') as fo:
            rc, metadata_file = self._cromwell.run(
                wdl=wdl,
                backend_conf=backend_conf,
                inputs=inputs,
                options=options,
                imports=imports,
                labels=labels,
                metadata=metadata_output,
                fileobj_stdout=fo,
            )

        if metadata_file:
            if fileobj_troubleshoot:
                cm = CromwellMetadata(metadata_file)
                if cm.workflow_status != 'Succeeded':
                    logger.info('Workflow failed. Auto-troubleshooting...')
                    cm.troubleshoot(fileobj=fileobj_troubleshoot)

        logger.info(
            'run ended: rc={rc}, stdout={stdout}'.format(rc=rc, stdout=file_stdout)
        )

        return metadata_file

    def server(
        self,
        default_backend,
        custom_backend_conf=None,
        file_stdout=None,
        embed_subworkflow=False,
        tmp_dir=None,
        dry_run=False,
    ):
        """Run a Cromwell server.
            default_backend:
                Default backend. If backend is not specified for a submitted workflow
                then default backend will be used.
                Choose among Caper's built-in backends.
                (aws, gcp, Local, slurm, sge, pbs).
                Or use a backend defined in your custom backend config file
                (above "backend_conf" file).
            custom_backend_conf:
                Backend config file (HOCON) to override Caper's
                auto-generated backend config.
            file_stdout:
                File to write Cromwell's STDOUT to.
                If None, then will be written to cromwell.o on tmp_dir.
                Note that STDERR is redirected to STDOUT.
            embed_subworkflow:
                Caper stores/updates metadata.JSON file on
                each workflow's root directory whenever there is status change
                of workflow (or it's tasks).
                This flag ensures that any subworkflow's metadata JSON will be
                embedded in main (this) workflow's metadata JSON.
                This is to mimic behavior of Cromwell run mode's -m parameter.
            tmp_dir:
                Local temporary directory to store all temporary files.
                Temporary files mean intermediate files used for running Cromwell.
                For example, backend config file.
                If this is not defined, then cache directory self._tmp_dir will be used.
            dry_run:
                Stop before running Java command line for Cromwell.
        """
        if tmp_dir is None:
            tmp_dir = self.create_timestamped_tmp_dir(
                prefix=CaperRunner.SERVER_TMP_DIR_PREFIX
            )

        backend_conf = self._caper_backend_conf.create_file(
            directory=tmp_dir,
            backend=default_backend,
            custom_backend_conf=custom_backend_conf,
        )

        logger.info('server ready: backend_conf={b}'.format(b=backend_conf))
        if dry_run:
            return None

        if file_stdout is None:
            file_stdout = os.path.join(tmp_dir, CaperRunner.BASENAME_CROMWELL_STDOUT)
        logger.info('server launched: stdout={stdout}'.format(stdout=file_stdout))

        with open(file_stdout, 'w') as fo:
            rc = self._cromwell.server(
                backend_conf=backend_conf,
                fileobj_stdout=fo,
                embed_subworkflow=embed_subworkflow,
            )
        logger.info(
            'server ended: rc={rc}, stdout={stdout}'.format(rc=rc, stdout=file_stdout)
        )