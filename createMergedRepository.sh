#!/bin/bash

# list of branches to merge
merge_branch_list=()

# add a subdirectory from a git repository, using a given git ref (tag/branch)
function addSubdirectoryFromRepo() {
    repourl=git@gitserver:/$1
    head_ref=$2
    subdir=$3
    mkdir -p $subdir
    pushd $subdir
    git archive --remote=$repourl $head_ref:$subdir | tar -x --warning=no-timestamp
    popd
    git add $subdir
}

# add a repo to the merge repo, moving code to its own subdirectory
function addRepo() {
    repourl=git@gitserver:/$1
    reponame=`basename $1`
    head_ref=$2
    subdir=$3/$reponame
    # clone the repo to /tmp
    pushd /tmp
    rm -rf $reponame
    git clone $repourl
    # check out the required commit as a new branch "mergebranch"
    pushd $reponame
    git checkout -b mergebranch $head_ref
    # move the code to its own subdirectory, and commit on mergebranch
    mkdir -p $subdir
    readarray -t <<<$(git ls-tree --name-only mergebranch)
    git mv "${MAPFILE[@]}" $subdir
    git commit -m "DUK-112 Move contents to subdirectory $subdir"$'\n\n'"Signed-off-by: Steve Folly <Steve.Folly2@cubic.com>"
    # return to the merge repo
    popd
    popd
    # add the new repository as a remote and fetch all content
    git remote add $reponame /tmp/$reponame
    git fetch $reponame
    # add content to the staging area
    git archive --remote=/tmp/$reponame mergebranch | tar -x --warning=no-timestamp
    git add $subdir
    # add branch to list
    merge_branch_list+=("$reponame/mergebranch")
}

# clone the (empty) repo
git clone git@gitserver:gate/TfL_LCP3_EGate
pushd TfL_LCP3_EGate

# add third-party code (without history)
mkdir -p third-party
pushd third-party
addSubdirectoryFromRepo  ftp2/third-party  third-party_1.2.0.64  rapidjson
addSubdirectoryFromRepo  ftp2/third-party  third-party_1.2.0.64  CURL
popd

# symlink to third-party directory (as created by gatepackage/scriptfiles/get_master.sh)
mkdir -p libraries/third-party
pushd libraries/third-party
ln -s ../third-party
git add third-party
popd

# add all the other shared/common repos
addRepo  gate/gatepackage                   master               .
addRepo  gate/Gate_Common                   master               .

addRepo  DefinesAndTypes/GBL_Globals        Common_1.17.1.9      CTSCommon
addRepo  OSAbstraction/CTS_Assert           CTS_Assert_1.10.0.1  CTSCommon
addRepo  OSAbstraction/CtslVCL              CtslVCL_1.12.0.4     CTSCommon
addRepo  OSAbstraction/MaccosConnectivity   Common_1.17.1.9      CTSCommon
addRepo  OSAbstraction/MaccosLib            MaccosLib_1.12.0.4   CTSCommon
addRepo  OSAbstraction/MOSP                 Common_1.17.1.9      CTSCommon
addRepo  Protocols/SHRUB                    Common_1.17.1.9      CTSCommon
addRepo  Protocols/Swap                     Common_1.17.1.9      CTSCommon
addRepo  Utilities/CTSSysLog                Common_1.17.1.9      CTSCommon
addRepo  Utilities/CUT_CommonUtilities      Common_1.17.1.9      CTSCommon
addRepo  Utilities/NAM_NVRAMAccessManager   Common_1.17.1.9      CTSCommon

addRepo  Common/asio_ext                    Common_1.17.1.9      libraries
addRepo  Common/Calendar                    Common_1.2.0.90      libraries
addRepo  Common/Log                         Common_1.17.1.9      libraries
addRepo  Common/SNMPMgr                     Common_1.17.1.9      libraries
addRepo  Common/Status                      Common_1.17.1.9      libraries
addRepo  Common/Tables                      Common_1.17.0.8      libraries
addRepo  Common/TableSync                   Common_1.17.1.9      libraries
addRepo  Common/TimeLib                     Common_1.17.1.9      libraries
addRepo  Common/Utilities                   Common_1.17.0.8      libraries
addRepo  Utilities/ServiceDiscovery         Common_1.17.1.9      libraries

# commit all the code
git commit -m "DUK-112 Single repository for all LCP3 EGate code"$'\n\n'"Signed-off-by: Steve Folly <Steve.Folly2@cubic.com>"

# merge
git merge --allow-unrelated-histories "${merge_branch_list[@]}" --no-commit
git commit -m "DUK-112 Merge history of all shared and common repositories"$'\n\n'"Signed-off-by: Steve Folly <Steve.Folly2@cubic.com>"
