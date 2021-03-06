# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Open Source Robotics Foundation, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Open Source Robotics Foundation, Inc. nor
#    the names of its contributors may be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import shutil
import subprocess
import tempfile

from rosdistro import logger
from rosdistro.manifest_provider import get_release_tag


workspace_base = '/tmp/rosdistro-workspace'


def git_manifest_provider(_dist_name, repo, pkg_name):
    assert repo.version
    try:
        release_tag = get_release_tag(repo, pkg_name)
        package_xml = _get_package_xml(repo.url, release_tag)
        return package_xml
    except Exception:
        raise RuntimeError('unable to fetch package.xml')


def _get_package_xml(url, tag):
    base = tempfile.mkdtemp('rosdistro')
    package_xml = None
    # git 1.7.9 does not support cloning a tag directly, so doing it in two steps
    cmd = [_git_client_executable, 'clone', '--depth', '0', url, base]
    result = _run_command(cmd, base)
    if result['returncode'] != 0:
        logger.debug('Could not shallow clone repository "%s"' % url)
    else:
        cmd = [_git_client_executable, 'checkout', tag]
        result = _run_command(cmd, base)
        if result['returncode'] != 0:
            logger.debug('Could not checkout tag "%s" of repository "%s"' % (tag, url))
        else:
            filename = os.path.join(base, 'package.xml')
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    package_xml = f.read()
            else:
                logger.debug('Could not find package.xml in repository "%s"' % url)
    shutil.rmtree(base)
    if package_xml is None:
        raise RuntimeError('unable to fetch package.xml')
    return package_xml


def _run_command(cmd, cwd, env=None):
    result = {'cmd': ' '.join(cmd), 'cwd': cwd}
    try:
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        output, _ = proc.communicate()
        result['output'] = output.rstrip()
        result['returncode'] = proc.returncode
    except subprocess.CalledProcessError as e:
        result['output'] = e.output
        result['returncode'] = e.returncode
    return result


def _find_executable(file_name):
    for path in os.getenv('PATH').split(os.path.pathsep):
        file_path = os.path.join(path, file_name)
        if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
            return file_path
    return None

_git_client_executable = _find_executable('git')
