# Releasing the Driver

The following guide details the steps for releasing the Ansible Lifecycle Driver. This may only be performed by a user with admin rights to this Git repository and the `icr.io/cp4na-drivers` IBM Cloud Container Registry.

**Ensure you've followed the steps in [configure your development environment](dev-env.md) as there are libraries required to complete the release.**

## 1. Ensure Milestone

Ensure there is a milestone created for the release at: [https://github.com/IBM/ansible-lifecycle-driver/milestones](https://github.com/IBM/ansible-lifecycle-driver/milestones).

Also ensure all issues going into this release are assigned to this milestone. **Move any issues from unreleased milestones into this release if the code has been merged**

## 2. Update version (on develop)

Ensure the version in `pkg_info.json` starts with the corresponding version for the release.

For example, if releasing `3.2.0`, ensure the `pkg_info.json` contains:

```
{"version": "3.2.0.dev0"}
```

This should have been done after the last release but it's good to check as the planned version may have changed (we expected to release a patch `3.2.1` but due to the nature of changes we've decided it's a minor release `3.3.0` instead)

Commit and push these changes.

## 3. Update CHANGELOG (on develop)

Update the `CHANGELOG.md` file with a list of issues fixed by this release (see other items in this file to get an idea of the desired format).

Commit and push these changes.

## 4. Merge Develop to Main

Development work is normally carried out on the `develop` branch. Merge this branch to `main`, by creating a PR.

Then perform the release from the `main` branch. This ensures the `main` branch is tagged correctly. 

> Note: do NOT delete the `develop` branch

## 5. Build and Release (on main)

Access the `ansible-lifecycle-driver` build job on the internal CI/CD tool (maintainers should be aware and have access to this. Speak to another maintainer if not).

Navigate to the job for the `main` branch. The merge to `main` should have already triggered a build. Let this build complete in order to verify there were no issues with the merge. The automated job will not complete the release, it will only build and run the unit tests.

Once ready, click `Build with Parameters` for on the `main` branch job. Enable the `release` option and click `BUILD`.

Wait for the build to complete successfully. 

The build will generate the release candidate artifacts and publish them to an internal registry (as above, maintainers should be aware and have access to this. Speak to another maintainer if not).

## 6. Artifact promotion

When the release artifacts are ready to be published, access the `Promote-Drivers` build job on the internal CI/CD tool

Click `Build with Parameters` and enter the version numbers of the drivers that you wish to promote and click `BUILD`.

Wait for the build to complete successfully.

The job will publish the artifacts and create a [release on Github](https://github.com/IBM/ansible-lifecycle-driver/releases).

## 7. Verify Release

Verify the CI/CD job has created a [release on Github](https://github.com/IBM/ansible-lifecycle-driver/releases).

Ensure the tag, title and changelog are all correct. Also ensure the documentation and helm `tgz` files have been attached.

## 8. Cleanup

Complete the following steps to ensure development can continue as normal:

- Merge `main` to `develop` so any release updates and the post-version are copied over from main (doesn't require a PR)
- Close the Milestone for this release on [Github](https://github.com/IBM/ansible-lifecycle-driver/milestones)
- Create a new Milestone for next release (if one does not exist).

# Manual Approach

**Please use the instructions above. The manual approach is now legacy and only kept for the rare circumstances**

## 1-4. Prepare Release

Complete steps 1-4 from the main release instructions (found above).
 
## 5. Build and Release (on main)

The `build.py` script automates the following steps: 

- Update the release version in pkg_info.json
- Build the Python whl for the driver library
- Build and Tag Docker Image
- Build Helm Chart
- Package Documentation
- Push Docker Image to `icr.io/cp4na-drivers` group on IBM Cloud Container Registry
- Create a tagged commit in the git repository to mark this release

To perform a release, run `build.py` and set the following options:

```
python3 build.py --release --version <THE VERSION TO BE RELEASED> --post-version <VERSION TO BE USED AFTER THE RELEASE> --ignition-version <VERSION OF IGNITION TO BE USED>
```

> Note: check the `ignition-version` in `pkg_info.json`, if it's already at the correct version then you do not need to include `--ignition-version`

For example:
```
python3 build.py --release --version 1.0.0 --post-version 1.0.1.dev0
```

## 6. Release artifacts

The Docker image has been pushed by the `build.py` script but the documentation and Helm chart packages must be uploaded manually to Github.

Complete the following:

- Visit the [releases](https://github.com/IBM/ansible-lifecycle-driver/releases) section of the driver repository
- Click `Draft a new release`
- Input the version the `--version` option earlier as the tag e.g. 1.0.0
- Use the same value for the `Release title` e.g. 1.0.0
- Add release notes in the description of the release. Look at previous releases to see the format. Usually, we will list the issues fixed. This is essentially the same content you have already added to `CHANGELOG.md` so just copy and paste the entry for this release, edit the header to say `Release Notes`.
- Attach the Helm chart `tgz` file produced by `build.py` in the `release-artifacts` directory
- Attach the documentation `tgz` file produced by `build.py` in the `release-artifacts` directory

## 7. Cleanup

Complete step 7 from the main release instructions (found above).
