import os
import re
from argparse import ArgumentParser
from enum import Enum
from pathlib import Path
from typing import Tuple

cur_dir = Path(__file__).parent
changelog_path = cur_dir.parent / "CHANGELOG.md"

with_hash = False
commitizens = (
    r"(?:build|chore|ci|docs?|feat!?|fix|perf|refactor|rft|style|test|i18n|typo|debug)"
)
ignore_commitizens = r"(?:build|ci|style|debug)"

raw_commits_info = {}


class Translation(Enum):
    FIX = "fix"
    FEAT = "feat"
    PERF = "perf"
    DOCS = "docs"
    OTHER = "other"


def individual_commits(oper, commits: dict, indent: str = "") -> Tuple[str, list]:
    if not commits:
        return ""
    ret_message = ""

    for commit_hash, commit_info in commits.items():
        if commit_info["skip"]:
            continue

        commit_message = commit_info["message"]

        if re.match(rf"^{ignore_commitizens} *(?:\([^\)]*\))*: *", commit_message):
            continue

        ret_message += indent + "* " + commit_message

        mes = individual_commits(oper, commit_info["branch"], indent + "   ")

        ret_message += f" ({commit_hash})\n" if with_hash else "\n"
        if with_merge:
            ret_message += mes

    return ret_message


def update_commits(commit_message, sorted_commits, update_dict):
    oper = "other"
    for trans in Translation:
        if commit_message.startswith(trans.value):
            oper = trans.value
            break

    sorted_commits[oper].update(update_dict)


def update_message(sorted_commits: dict):
    ret_message = ""
    for oper, commits in sorted_commits.items():
        mes = individual_commits(oper, commits, "")
        if mes:
            ret_message += mes
    return (ret_message,)


def print_commits(commits: dict):
    sorted_commits = {
        "perf": {},
        "feat": {},
        "fix": {},
        "docs": {},
        "other": {},
    }
    for commit_hash, commit_info in commits.items():
        commit_message = commit_info["message"]
        update_commits(commit_message, sorted_commits, {commit_hash: commit_info})

    return update_message(sorted_commits)


def build_commits_tree(commit_hash: str):
    if commit_hash not in raw_commits_info:
        return {}
    raw_commit_info = raw_commits_info[commit_hash]
    if "visited" in raw_commit_info and raw_commit_info["visited"]:
        return {}
    raw_commit_info.update(
        {"visited": True}
    )  # Prevent a commit from being traversed by multiple branches

    res = {
        commit_hash: {
            "hash": raw_commit_info["hash"],
            "message": raw_commit_info["message"],
            "branch": {},
            "skip": raw_commit_info.get("skip", False),
        }
    }

    res.update(build_commits_tree(raw_commit_info["parent"][0]))

    # The second parent is the merged branch of Merge commit
    if len(raw_commit_info["parent"]) == 2:
        if raw_commit_info["message"].startswith("Release") or raw_commit_info[
            "message"
        ].startswith("Merge"):
            # Avoid having only one Release main commit after a merge
            # Ignore without information Merge commit (eg. Merge remote-tracking branch; Merge branch 'dev' of xxx into dev)
            res.update(build_commits_tree(raw_commit_info["parent"][1]))
        else:
            res[commit_hash]["branch"].update(
                build_commits_tree(raw_commit_info["parent"][1])
            )
        if (
            raw_commit_info["message"].startswith("Merge")
            and not res[commit_hash]["branch"]
        ):
            res.pop(commit_hash)
    return res


def call_command(command: str):
    with os.popen(command) as fp:
        bf = fp._stream.buffer.read()
    try:
        command_ret = bf.decode().strip()
    except:
        command_ret = bf.decode("gbk").strip()
    return command_ret


def main(tag_name=None, latest=None):
    global raw_commits_info
    tags = os.popen('git tag --list "v*"').read().strip().split("\n")
    latest = tags[-1]
    penultimate = tags[-2]

    if not tag_name:
        tag_name = os.popen('git describe --tags --match "v*"').read().strip()
    print("From:", penultimate, ", To:", latest, "\n")

    git_command = (
        rf'git log {penultimate}..{latest} --pretty=format:"%H%n%aN%n%cN%n%s%n%P%n"'
    )
    raw_gitlogs = call_command(git_command)

    raw_commits_info = {}
    for _raw in raw_gitlogs.split("\n\n"):
        commit_hash, author, committer, message, parent = _raw.split("\n")

        raw_commits_info[commit_hash] = {
            "hash": commit_hash[:8],
            "message": message,
            "parent": parent.split(),
        }

    git_skip_command = (
        rf'git log {latest}..HEAD --pretty=format:"%H%n" --grep="\[skip changelog\]"'
    )
    raw_gitlogs = call_command(git_skip_command)

    for commit_hash in raw_gitlogs.split("\n\n"):
        if commit_hash not in raw_commits_info:
            continue
        git_show_command = rf"git show -s --format=%b%n {commit_hash}"
        raw_git_shows = call_command(git_show_command)
        for commit_body in raw_git_shows.split("\n"):
            if not commit_body.startswith("* ") and "[skip changelog]" in commit_body:
                raw_commits_info[commit_hash]["skip"] = True

    res = print_commits(build_commits_tree([x for x in raw_commits_info.keys()][0]))

    changelog_content = res[0]
    print(changelog_content)
    with open(changelog_path, "w", encoding="utf8") as f:
        f.write(changelog_content)


def ArgParser():
    parser = ArgumentParser()
    parser.add_argument(
        "--tag", help="release tag name", metavar="TAG", dest="tag_name", default=None
    )
    parser.add_argument(
        "--base",
        "--latest",
        help="base tag name",
        metavar="TAG",
        dest="latest",
        default=None,
    )
    parser.add_argument(
        "-wh",
        "--with-hash",
        help="print commit message with hash",
        action="store_true",
        dest="with_hash",
    )
    parser.add_argument(
        "-wm",
        "--with-merge",
        help="print merge commits tree",
        action="store_true",
        dest="with_merge",
    )
    return parser


if __name__ == "__main__":
    args = ArgParser().parse_args()
    with_hash = args.with_hash
    with_merge = args.with_merge
    main(tag_name=None, latest=None)
