#!/usr/bin/python
# Copyright (c) 2026 VEXXHOST, Inc.
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = '''
---
module: molecule_install_galaxy_sibling_collections
short_description: Install checked-out Galaxy collection siblings
author:
  - VEXXHOST, Inc.
description:
  - Finds Ansible collections checked out by Zuul that satisfy Galaxy
    dependencies for the project under test and installs those sibling
    collections into the local Galaxy collection path.
  - For ordinary required projects, this module follows Galaxy resolution
    behavior by selecting the highest local release tag that satisfies the
    dependency version spec.
  - For projects in the current buildset, including C(Depends-On) projects,
    this module installs the Zuul-provided speculative checkout directly.
options:
  project_dir:
    description:
      - Directory for the project under test.
    required: true
    type: path
  workspace_dir:
    description:
      - Directory relative Zuul checkout paths are rooted under.
    required: true
    type: path
  projects:
    description:
      - Zuul project dictionaries from C(zuul.projects).
    required: true
    type: list
    elements: dict
  build_refs:
    description:
      - Current Zuul build refs/items. Projects in this list are kept at their
        speculative checkout instead of being checked out to a release tag.
    type: list
    default: []
  collections_path:
    description:
      - Collection installation path passed to C(ansible-galaxy collection
        install --collections-path).
    required: true
    type: path
  executable:
    description:
      - Executable used to run C(ansible-galaxy).
    type: str
    default: uv
'''

EXAMPLES = '''
- name: Install Ansible collection siblings
  molecule_install_galaxy_sibling_collections:
    project_dir: "{{ zuul.project.src_dir }}"
    workspace_dir: "{{ ansible_user_dir }}"
    projects: "{{ zuul.projects.values() | list }}"
    build_refs: "{{ zuul.get('build_refs', []) + zuul.get('items', []) }}"
    collections_path: "{{ ansible_user_dir }}/.ansible/collections"
'''

RETURN = '''
installed:
  description: Collections installed from local checkouts.
  returned: always
  type: list
  elements: dict
checkouts:
  description: Release tag checkouts performed before installation.
  returned: always
  type: list
  elements: dict
log:
  description: Human-readable operation log.
  returned: always
  type: list
  elements: str
'''

import os
import re
import traceback

import yaml

from ansible.module_utils.basic import AnsibleModule


VERSION_RE = re.compile(r'^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$')
VERSION_PARTS_RE = re.compile(
    r'^(\d+)\.(\d+)\.(\d+)(?:[-+]([0-9A-Za-z.-]+))?$')


def abs_path(path, workspace_dir):
    if not path:
        return path
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(workspace_dir, path))


def load_galaxy(path):
    galaxy_path = os.path.join(path, 'galaxy.yml')
    if not os.path.exists(galaxy_path):
        return None
    with open(galaxy_path, 'r') as galaxy_file:
        data = yaml.safe_load(galaxy_file) or {}
    if not isinstance(data, dict):
        return None
    return data


def load_galaxy_at_ref(module, path, ref, log):
    rc, out, err = module.run_command(
        ['git', 'show', '{ref}:galaxy.yml'.format(ref=ref)],
        cwd=path,
    )
    if rc:
        module.fail_json(
            msg='Unable to read galaxy.yml from {ref} in {path}'.format(
                ref=ref,
                path=path,
            ),
            rc=rc,
            stdout=out,
            stderr=err,
            log=log,
        )

    data = yaml.safe_load(out) or {}
    if not isinstance(data, dict):
        module.fail_json(
            msg='Invalid galaxy.yml from {ref} in {path}'.format(
                ref=ref,
                path=path,
            ),
            log=log,
        )
    return data


def collection_name(galaxy):
    namespace = galaxy.get('namespace')
    name = galaxy.get('name')
    if not namespace or not name:
        return None
    return '{namespace}.{name}'.format(namespace=namespace, name=name)


def dependency_items(galaxy):
    dependencies = galaxy.get('dependencies') or {}
    if not isinstance(dependencies, dict):
        return []
    return list(dependencies.items())


def project_names(project):
    names = set()
    if isinstance(project, str):
        names.add(project)
        return names
    if not isinstance(project, dict):
        return names

    for key in ('canonical_name', 'name'):
        value = project.get(key)
        if value:
            names.add(value)
    return names


def build_ref_project_names(build_refs):
    names = set()
    for item in build_refs:
        if isinstance(item, dict) and 'project' in item:
            names.update(project_names(item.get('project')))
        else:
            names.update(project_names(item))
    return names


def project_in_build_refs(project, build_names):
    return bool(project_names(project) & build_names)


def collect_collection_projects(projects, project_dir, workspace_dir,
                                build_names, log):
    collection_projects = {}

    for project in projects:
        if not isinstance(project, dict):
            continue

        src_dir = project.get('src_dir')
        if not src_dir:
            continue

        src_path = abs_path(src_dir, workspace_dir)
        if os.path.abspath(src_path) == os.path.abspath(project_dir):
            continue

        galaxy = load_galaxy(src_path)
        if not galaxy:
            continue

        name = collection_name(galaxy)
        if not name:
            log.append('Skipping {path}: no collection name'.format(
                path=src_path))
            continue

        collection_projects[name] = {
            'name': name,
            'path': src_path,
            'project': project,
            'in_build_refs': project_in_build_refs(project, build_names),
        }
        log.append('Sibling collection {name} at {path}'.format(
            name=name,
            path=src_path,
        ))

    return collection_projects


def normalize_spec(spec):
    if spec is None:
        return '*'
    spec = str(spec).strip()
    if not spec:
        return '*'
    parts = [part.strip().replace(' ', '') for part in spec.split(',')]
    parts = [part for part in parts if part]
    return ','.join(parts) or '*'


def combined_spec(specs):
    normalized = [normalize_spec(spec) for spec in specs]
    normalized = [spec for spec in normalized if spec != '*']
    return ','.join(normalized) or '*'


def version_from_tag(tag):
    name = tag.rsplit('/', 1)[-1]
    if name.startswith('v') and len(name) > 1 and name[1].isdigit():
        name = name[1:]
    if not VERSION_RE.match(name):
        return None
    return name


def version_sort_key(version):
    match = VERSION_PARTS_RE.match(version)
    if not match:
        return (0, 0, 0, 0, '')

    suffix = match.group(4) or ''
    # Stable releases sort after pre-release variants for the same numeric
    # version.
    stable = 1 if not suffix else 0
    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
        stable,
        suffix,
    )


def compare_versions(left, right):
    left_key = version_sort_key(left)
    right_key = version_sort_key(right)
    if left_key == right_key:
        return 0
    return 1 if left_key > right_key else -1


def meets_version_requirement(version, requirement):
    requirement = normalize_spec(requirement)
    if requirement == '*':
        return True

    operators = ('!=', '==', '>=', '<=', '>', '<', '=')
    for part in requirement.split(','):
        if not part or part == '*':
            continue

        op = None
        wanted = part
        for candidate in operators:
            if part.startswith(candidate):
                op = candidate
                wanted = part[len(candidate):]
                break
        if op is None:
            op = '=='

        if wanted == '*':
            continue

        cmp_result = compare_versions(version, wanted)
        if op in ('==', '=') and cmp_result != 0:
            return False
        if op == '!=' and cmp_result == 0:
            return False
        if op == '>=' and cmp_result < 0:
            return False
        if op == '>' and cmp_result <= 0:
            return False
        if op == '<=' and cmp_result > 0:
            return False
        if op == '<' and cmp_result >= 0:
            return False

    return True


def list_release_tags(module, source, log):
    rc, out, err = module.run_command(
        ['git', 'tag', '--list'],
        cwd=source['path'],
    )
    if rc:
        module.fail_json(
            msg='Unable to list tags for {name}'.format(
                name=source['name']),
            rc=rc,
            stdout=out,
            stderr=err,
            log=log,
        )

    releases = []
    for tag in out.splitlines():
        version = version_from_tag(tag)
        if version is None:
            continue
        releases.append({
            'tag': tag,
            'version': version,
        })
    return releases


def select_release(module, source, specs, log):
    requirement = combined_spec(specs)
    matches = []
    for release in list_release_tags(module, source, log):
        try:
            if meets_version_requirement(release['version'], requirement):
                matches.append(release)
        except Exception as exc:
            log.append(
                'Skipping {name} tag {tag}: {exc}'.format(
                    name=source['name'],
                    tag=release['tag'],
                    exc=exc,
                ))

    if not matches:
        module.fail_json(
            msg='No local release tag for {name} satisfies {spec}'.format(
                name=source['name'],
                spec=requirement,
            ),
            log=log,
        )

    return sorted(matches, key=lambda item: version_sort_key(item['version']))[-1]


def resolve_sibling_collections(module, root_galaxy, collection_projects,
                                log):
    requirements = {}
    queue = []
    resolutions = {}

    def add_requirement(name, spec):
        if name not in collection_projects:
            log.append('Skipping {name}: no checked-out sibling'.format(
                name=name))
            return
        spec = normalize_spec(spec)
        specs = requirements.setdefault(name, [])
        if spec not in specs:
            specs.append(spec)
            queue.append(name)

    for dependency, spec in dependency_items(root_galaxy):
        add_requirement(dependency, spec)

    while queue:
        name = queue.pop(0)
        source = collection_projects[name]
        specs = list(requirements[name])

        if source['in_build_refs']:
            galaxy = load_galaxy(source['path'])
            if not galaxy:
                module.fail_json(
                    msg='Missing galaxy.yml for {name}'.format(name=name),
                    log=log,
                )
            release = {
                'tag': None,
                'version': galaxy.get('version'),
            }
            log.append(
                'Keeping {name} at speculative checkout'.format(name=name))
        else:
            release = select_release(module, source, specs, log)
            galaxy = load_galaxy_at_ref(module, source['path'],
                                        release['tag'], log)
            log.append(
                'Resolved {name} to {tag} for {spec}'.format(
                    name=name,
                    tag=release['tag'],
                    spec=combined_spec(specs),
                ))

        existing = resolutions.get(name)
        if existing and existing.get('tag') == release['tag']:
            existing['specs'] = specs
            continue

        resolutions[name] = {
            'name': name,
            'path': source['path'],
            'specs': specs,
            'tag': release['tag'],
            'version': release['version'],
            'in_build_refs': source['in_build_refs'],
        }

        for dependency, spec in dependency_items(galaxy):
            add_requirement(dependency, spec)

    return resolutions


def run_command(module, args, cwd, log):
    rc, out, err = module.run_command(args, cwd=cwd)
    command = ' '.join(args)
    log.append('Running: {command}'.format(command=command))
    if out:
        log.extend(out.splitlines())
    if err:
        log.extend(err.splitlines())
    if rc:
        module.fail_json(
            msg='Command failed: {command}'.format(command=command),
            rc=rc,
            stdout=out,
            stderr=err,
            log=log,
        )
    return out


def git_head(module, path):
    rc, out, err = module.run_command(
        ['git', 'rev-parse', 'HEAD'],
        cwd=path,
    )
    if rc:
        module.fail_json(
            msg='Unable to read git HEAD in {path}'.format(path=path),
            rc=rc,
            stdout=out,
            stderr=err,
        )
    return out.strip()


def checkout_release(module, resolution, log):
    before = git_head(module, resolution['path'])
    rc, out, err = module.run_command(
        ['git', 'checkout', '--quiet', resolution['tag']],
        cwd=resolution['path'],
    )
    if rc:
        module.fail_json(
            msg='Unable to check out {name} to {tag}'.format(
                name=resolution['name'],
                tag=resolution['tag'],
            ),
            rc=rc,
            stdout=out,
            stderr=err,
            log=log,
        )

    after = git_head(module, resolution['path'])
    log.append('Checked out {name} to {tag}'.format(
        name=resolution['name'],
        tag=resolution['tag'],
    ))
    return before != after


def install_collections(module, resolutions, project_dir, collections_path,
                        executable, log):
    installed = []
    checkouts = []
    changed = False

    for name in sorted(resolutions):
        resolution = resolutions[name]
        installed.append({
            'name': name,
            'path': resolution['path'],
            'spec': combined_spec(resolution['specs']),
            'tag': resolution['tag'],
            'version': resolution['version'],
            'in_build_refs': resolution['in_build_refs'],
        })

        if module.check_mode:
            continue

        if resolution['tag'] is not None:
            checkout_changed = checkout_release(module, resolution, log)
            checkouts.append({
                'name': name,
                'path': resolution['path'],
                'tag': resolution['tag'],
                'changed': checkout_changed,
            })
            changed = changed or checkout_changed

        args = [
            executable,
            'run',
            'ansible-galaxy',
            'collection',
            'install',
            '--force',
            '--no-deps',
            '--collections-path',
            collections_path,
            resolution['path'],
        ]
        run_command(module, args, project_dir, log)
        changed = True

    return changed, installed, checkouts


def main():
    module = AnsibleModule(
        argument_spec=dict(
            project_dir=dict(required=True, type='path'),
            workspace_dir=dict(required=True, type='path'),
            projects=dict(required=True, type='list', elements='dict'),
            build_refs=dict(type='list', default=[]),
            collections_path=dict(required=True, type='path'),
            executable=dict(type='str', default='uv'),
        ),
        supports_check_mode=True,
    )

    log = []
    workspace_dir = module.params['workspace_dir']
    project_dir = abs_path(module.params['project_dir'], workspace_dir)
    collections_path = abs_path(
        module.params['collections_path'],
        workspace_dir,
    )
    executable = module.params['executable']

    try:
        root_galaxy = load_galaxy(project_dir)
        if not root_galaxy:
            module.exit_json(
                changed=False,
                msg='No galaxy.yml, no action needed.',
                installed=[],
                checkouts=[],
                log=log,
            )

        build_names = build_ref_project_names(module.params['build_refs'])
        collection_projects = collect_collection_projects(
            module.params['projects'],
            project_dir,
            workspace_dir,
            build_names,
            log,
        )
        resolutions = resolve_sibling_collections(
            module,
            root_galaxy,
            collection_projects,
            log,
        )
        changed, installed, checkouts = install_collections(
            module,
            resolutions,
            project_dir,
            collections_path,
            executable,
            log,
        )

        msg = '\n'.join(log) or 'No sibling collections to install.'
        module.exit_json(
            changed=changed,
            msg=msg,
            installed=installed,
            checkouts=checkouts,
            log=log,
        )
    except Exception as exc:
        tb = traceback.format_exc()
        log.append(str(exc))
        log.append(tb)
        module.fail_json(msg=str(exc), log=log)


if __name__ == '__main__':
    main()
