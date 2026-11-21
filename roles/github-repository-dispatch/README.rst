Send a ``repository_dispatch`` event to a GitHub repository.

Triggers the GitHub Actions workflows of the repository that listen for
``repository_dispatch`` with the given event type; the payload is available
to them as ``github.event.client_payload``. GitHub only runs workflows from
the repository's default branch for this event.

The token needs ``contents: write`` on the repository, for example an
installation token from the ``github-app-token`` role (the default). Run it
on ``localhost`` from a trusted playbook, like ``github-app-token``.

**Role Variables**

.. zuul:rolevar:: github_repository_dispatch_repository

   Repository to send the event to, as ``org/repo``.

.. zuul:rolevar:: github_repository_dispatch_event_type

   Event type (``github.event.action`` in the workflow).

.. zuul:rolevar:: github_repository_dispatch_client_payload
   :default: {}

   JSON payload, at most 10 top-level keys.

.. zuul:rolevar:: github_repository_dispatch_token
   :default: {{ github_app_token }}

   Token used to send the event.

.. zuul:rolevar:: github_repository_dispatch_api_url
   :default: https://api.github.com

   GitHub API endpoint.
