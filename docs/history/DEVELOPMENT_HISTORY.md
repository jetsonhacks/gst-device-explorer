# Development History

The milestone-by-milestone development record for this project is preserved in the Git tag:

```
full-development-docs
```

That tag captures the full `docs/milestones/` directory (MILESTONE_1 through
MILESTONE_44 and sub-milestones), along with `docs/ROADMAP.md` and
`docs/GUI_ROADMAP.md` as they existed at the time of archiving.

To browse the archived documentation:

```sh
# View a specific milestone file
git show full-development-docs:docs/milestones/MILESTONE_1.md

# Restore the full milestones directory locally (working tree only)
git checkout full-development-docs -- docs/milestones/

# List all archived docs files
git ls-tree -r --name-only full-development-docs docs/
```

Development history is preserved by Git. Current production documentation
describes the product as it exists now.
