#!/usr/bin/env groovy

String tarquinBranch = "CPNA-1579"

library "tarquin@$tarquinBranch"

pipelinePy {
  pkgInfoPath = 'ansibledriver/pkg_info.json'
  applicationName = 'ansible-lifecycle-driver'
  releaseArtifactsPath = 'release-artifacts'
  attachDocsToRelease = true
  attachHelmToRelease = true
}
