Mint a GitHub App installation token for one repository.

Signs a short-lived JWT with the GitHub App private key, looks up the App's
installation for ``github_app_token_repository`` and creates an installation
token limited to that repository (and, optionally, to a subset of the App's
permissions). The token is saved in the ``github_app_token`` fact; every
task that handles the key or the token uses ``no_log``.

Run it on ``localhost`` from a trusted playbook, so the private key and the
token stay on the executor and never reach a node that runs project code.
It needs the ``community.crypto`` collection and the Python
``cryptography`` library, both of which the Zuul executor's Ansible
environments provide.

**Role Variables**

.. zuul:rolevar:: github_app_token_app

   GitHub App credentials, normally provided by a Zuul secret.

   .. zuul:rolevar:: app_id

      GitHub App ID.

   .. zuul:rolevar:: app_key

      GitHub App private key (PEM).

.. zuul:rolevar:: github_app_token_repository

   Repository the token is for, as ``org/repo``. The App must be installed
   on it.

.. zuul:rolevar:: github_app_token_permissions
   :default: {}

   Permissions to request, for example ``{contents: write}``. Empty requests
   all permissions of the installation. Requesting a permission the App
   does not have fails.

.. zuul:rolevar:: github_app_token_api_url
   :default: https://api.github.com

   GitHub API endpoint.

**Facts**

.. zuul:rolevar:: github_app_token

   The installation token (valid for one hour).

.. zuul:rolevar:: github_app_token_expires_at

   When the token expires.
