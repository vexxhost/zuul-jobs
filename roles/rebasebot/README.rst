Sync a downstream fork branch with its upstream branch using
`rebasebot <https://github.com/openshift-eng/rebasebot>`_.

rebasebot rebases the downstream commits on ``rebasebot_dest`` onto
``rebasebot_source``, pushes the result to ``rebasebot_rebase`` and opens
(or updates) a pull request into ``rebasebot_dest``.  It authenticates as a
GitHub App, which must be able to read the source repository and write
contents and pull requests on the destination repository.

By default it syncs the branch of the project the job runs for, so attaching
the job to a fork's ``periodic`` pipeline syncs every protected branch it
runs on.  If the destination repository is part of the job (for example, listed in
``required-projects``), its Zuul checkout is used as a git alternate so only
objects missing from it are fetched from GitHub.

**Role Variables**

.. zuul:rolevar:: rebasebot_upstream_project

   Upstream repository on GitHub, as ``org/repo`` (for example
   ``openstack/octavia``).  Required unless ``rebasebot_source`` is set.

.. zuul:rolevar:: rebasebot_upstream_branch
   :default: {{ zuul.branch }}

   Upstream branch to sync with.

.. zuul:rolevar:: rebasebot_source
   :default: {{ rebasebot_upstream_project }}:{{ rebasebot_upstream_branch }}

   Upstream repository and branch on GitHub, as ``org/repo:branch``.

.. zuul:rolevar:: rebasebot_dest
   :default: {{ zuul.project.name }}:{{ zuul.branch }}

   Downstream repository and branch on GitHub, as ``org/repo:branch``.

.. zuul:rolevar:: rebasebot_rebase
   :default: {{ zuul.project.name }}:rebasebot/<branch>

   Repository and branch on GitHub to push the rebased result to, as
   ``org/repo:branch``.  Slashes in the branch name are replaced by dashes.

.. zuul:rolevar:: rebasebot_github_app

   GitHub App credentials, normally provided by a Zuul secret.

   .. zuul:rolevar:: app_id

      GitHub App ID.

   .. zuul:rolevar:: app_key

      GitHub App private key (PEM).

.. zuul:rolevar:: rebasebot_tag_policy
   :default: strict

   Which downstream commits to carry, based on their ``UPSTREAM:`` subject
   prefix: ``strict`` (only tagged commits), ``soft`` or ``none``.

.. zuul:rolevar:: rebasebot_git_username
   :default: vexxhost-ci[bot]

   Git author name for commits created by rebasebot.

.. zuul:rolevar:: rebasebot_git_email
   :default: vexxhost-ci[bot]@users.noreply.github.com

   Git author email for commits created by rebasebot.

.. zuul:rolevar:: rebasebot_dry_run
   :default: false

   Perform the rebase without pushing or creating a pull request.

.. zuul:rolevar:: rebasebot_extra_args
   :default: []

   Additional arguments passed to rebasebot.

.. zuul:rolevar:: rebasebot_workdir
   :default: {{ ansible_user_dir }}/rebasebot-work

   Git working directory used by rebasebot.

.. zuul:rolevar:: rebasebot_executable
   :default: {{ ansible_user_dir }}/.local/bin/rebasebot

   rebasebot command, as installed by the ``ensure-rebasebot`` role.
