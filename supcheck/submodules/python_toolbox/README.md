# Parliamentary Publishing Python toolbox

**A selection of little Python helpers for common/repetitive tasks.**

## Include these helpers in other projects

These helpers are designed to be included in other projects. Include this repository in other GitHub-hosted projects using Git's ```submodule``` functionality.

This will create a ```.gitmodules``` file at the root of your project's repository, including details of the submodules you'd like to use and where they should be located within your project's structure. All good Git clients shoud recognise this and include the relevant repositories in your project when you first clone/fetch it.

Here's the suggested command to include this repository as a submodule in another project:

```
git submodule add https://github.com/hoc-ppu/python_toolbox submodules/python_toolbox
```

You can then import them into other Python scripts by doing something like:

```
import submodules.python_toolbox.pp_cli as pp_cli

pp_cli.clear()
```

> **Note:** Git won't keep submodules up to date after the initial clone. You should refresh them every so often by running:
> 
> ```
> git submodule update --remote
> ```

Full documentation on working with submodules can be found at <https://git-scm.com/book/en/v2/Git-Tools-Submodules>.
