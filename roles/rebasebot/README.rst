Sync a downstream fork branch with its upstream branch using
`rebasebot <https://github.com/openshift-eng/rebasebot>`_.

rebasebot rebases the downstream commits on ``rebasebot_dest`` onto
``rebasebot_source``, pushes the result to ``rebasebot_rebase`` and opens
(or updates) a pull request into ``rebasebot_dest``.  It authenticates as a
GitHub App, which must be able to read the source repository and write
contents and pull requests on the destination repository.

If the destination repository is part of the job (for example, listed in
``required-projects``), its Zuul checkout is used as a git alternate so only
objects missing from it are fetched from GitHub.

**Role Variables**

.. zuul:rolevar:: rebasebot_source

   Upstream repository and branch on GitHub, as ``org/repo:branch``.

.. zuul:rolevar:: rebasebot_dest

   Downstream repository and branch on GitHub, as ``org/repo:branch``.

.. zuul:rolevar:: rebasebot_rebase

   Repository and branch on GitHub to push the rebased result to, as
   ``org/repo:branch``.

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
   :default: rebasebot

   rebasebot command; set by the ``ensure-rebasebot`` role.
