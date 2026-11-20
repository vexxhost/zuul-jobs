Install `rebasebot <https://github.com/openshift-eng/rebasebot>`_.

Installs ``rebasebot`` with ``uv tool install`` (the ``setup-uv`` role must
have run first) and sets ``rebasebot_executable`` to the installed command.

**Role Variables**

.. zuul:rolevar:: rebasebot_repo
   :default: https://github.com/openshift-eng/rebasebot

   Git repository to install rebasebot from.

.. zuul:rolevar:: rebasebot_ref
   :default: fc1edb4e18f8d7e025ac6754449f637716610740

   Git ref (preferably a commit) of rebasebot to install.
