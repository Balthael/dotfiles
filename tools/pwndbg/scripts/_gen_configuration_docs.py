#!/usr/bin/env python
"""
You should use scripts/generate_docs.sh and scripts/verify_docs.sh instead
of using this.

If the PWNDBG_GEN_DOC_JUST_VERIFY environment variable
is set, then    : Exit with non-zero exit status if the docs/configuration/ files
                  aren't up to date with the sources. Don't modify anything.

If it isn't, this fixes up the docs/configuration/ files to be up
to date with the information from the sources. Except docs/configuration/index.md
which is hand-written.
"""

from __future__ import annotations

import os
import sys
from typing import Dict

from mdutils.mdutils import MdUtils

import pwndbg
from pwndbg.lib.config import HELP_DEFAULT_PREFIX
from pwndbg.lib.config import HELP_VALID_VALUES_PREFIX
from pwndbg.lib.config import Parameter
from scripts._gen_docs_generic import update_files_simple
from scripts._gen_docs_generic import verify_existence
from scripts._gen_docs_generic import verify_files_simple


def extract_params() -> Dict[str, list[Parameter]]:
    """
    Returns a dictionary that maps a scope name to a list of Parameter's
    in that scope.
    """
    scope_dict: Dict[str, list[Parameter]] = {}
    parameters = pwndbg.config.params

    # could use pwndbg.config.get_params() here but whatever

    for param in parameters.values():
        scope_name = param.scope.name
        if scope_name not in scope_dict:
            scope_dict[scope_name] = []
        scope_dict[scope_name].append(param)

    # Sort the parameters by name
    for scope in scope_dict:
        scope_dict[scope].sort(key=lambda p: p.attr_name())

    assert len(scope_dict) == len(pwndbg.lib.config.Scope) and (
        "The amount of detected scopes "
        "does not match the number of scopes defined in the source."
    )

    return scope_dict


def convert_to_markdown(scoped: Dict[str, list[Parameter]]) -> Dict[str, str]:
    """
    Returns a dict which maps filenames to their markdown contents.
    """
    markdowned: Dict[str, str] = {}
    for scope, param_list in scoped.items():
        filename = base_path + scope + ".md"
        mdFile = MdUtils(filename)
        mdFile.new_header(level=1, title=scope)

        # first generate some index

        for param in param_list:
            mdFile.new_header(level=2, title="**" + param.name + "**")
            set_show_doc = param.set_show_doc
            # Uppercase first letter and add dot to make it look like a sentence.
            set_show_doc = set_show_doc[0].upper() + set_show_doc[1:] + "."
            mdFile.new_paragraph(set_show_doc)

            assert not param.help_docstring or (
                param.help_docstring.count(HELP_DEFAULT_PREFIX) == 1
                and "The configuration generator expects to find the string "
                f"'{HELP_DEFAULT_PREFIX}' exactly once in order to perform proper bolding."
            )
            assert (
                param.help_docstring.count(HELP_VALID_VALUES_PREFIX) <= 1
                and "The configuration generator expects to find the string "
                f"'{HELP_VALID_VALUES_PREFIX}' exactly once in order to perform proper bolding."
            )

            help_docstring = param.help_docstring.replace(
                HELP_DEFAULT_PREFIX, f"**{HELP_DEFAULT_PREFIX}**"
            )
            help_docstring = help_docstring.replace(
                HELP_VALID_VALUES_PREFIX, f"**{HELP_VALID_VALUES_PREFIX}**"
            )
            mdFile.new_paragraph(help_docstring)

        autogen_warning = "<!-- THIS WHOLE FILE IS AUTOGENERATED. DO NOT MODIFY IT. See scripts/generate_docs.sh -->"
        markdowned[filename] = autogen_warning + "\n" + mdFile.get_md_text()

    return markdowned


def check_index(scoped_params: Dict[str, list[Parameter]]):
    assert (
        len(scoped_params.keys()) == 3
        and "It seems a new scope has been added, "
        f"please update the index file ({index_path}) and bump this number accordingly."
    )


base_path = "docs/configuration/"  # Must have trailing slash.
index_path = base_path + "index.md"

# NOTE: the docs/configuration/index.md file is
# not autogenerated.

# ==== Start ====

if len(sys.argv) > 1:
    print("This script doesn't accept any arguments.")
    print("See top of the file for usage.")
    sys.exit(1)

just_verify = False
if os.getenv("PWNDBG_GEN_DOC_JUST_VERIFY"):
    just_verify = True

print("\n==== Parameter Documentation ====")

scoped_params = extract_params()
markdowned = convert_to_markdown(scoped_params)

if just_verify:
    print("Checking if all files are in place..")
    missing, extra = verify_existence(list(markdowned.keys()) + [index_path], base_path)
    if missing or extra:
        print("To add mising files please run ./scripts/generate_docs.sh.")
        print("To remove extra files please remove them manually.")
        sys.exit(2)
    print("Every file is where it should be!")

    print("Verifying contents...")
    err = verify_files_simple(markdowned, skip=[index_path])
    if err:
        print("VERIFICATION FAILED. The files differ from what would be auto-generated.")
        print("Error:", err)
        print("Please run ./scripts/generate_docs.sh from project root and commit the changes.")
        sys.exit(3)

    print("Verification successful!")
else:
    print("Updating files...")
    update_files_simple(markdowned)
    print("Update successful.")

    missing, extra = verify_existence(list(markdowned.keys()) + [index_path], base_path)
    if len(missing) == 1 and missing[0] == index_path:
        print(f"The index ({index_path}) is missing. That is a hand-written file, please write it.")
        sys.exit(4)

    assert not missing and "Some files (and not the index) are missing, which should be impossible."

    if extra:
        sys.exit(5)

# Always check if the index is valid since it is not autogenerated.
check_index(scoped_params)
