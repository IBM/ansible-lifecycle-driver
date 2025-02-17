# kubectltest

Simple package to ensure the kubectl binary can be called from a Playbook.

The `kubectltest` resource runs `kubectl` on the Install lifecycle and registers the stdout output on the `result` property. After deploying the resource (using the included `wrapper` assembly), the property should show the `kubectl` help output.
