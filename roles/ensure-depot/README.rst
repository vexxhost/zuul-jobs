Install the `Depot <https://depot.dev>`_ CLI.

Downloads a pinned release of ``depot`` from GitHub, verifies its SHA-256
checksum and installs it into ``depot_install_prefix``/bin. Authentication is
left to the caller (for example a trusted pre-run that writes ``api_token``
to ``~/.config/depot/depot.yaml``, or ``DEPOT_TOKEN`` in the environment).

**Role Variables**

.. zuul:rolevar:: depot_version
   :default: 2.103.33

   Release of the Depot CLI to install.

.. zuul:rolevar:: depot_checksums

   SHA-256 checksums of the release archive, keyed by architecture
   (``amd64``, ``arm64``). Update together with ``depot_version``.

.. zuul:rolevar:: depot_install_prefix
   :default: /usr/local

   Prefix to install into; the binary ends up in ``<prefix>/bin/depot``.
