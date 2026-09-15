---
title: "How to Download Assets from GitHub using a screen reader."
date: '2026-09-12T19:28:50.020427+00:00'
tags: [blog and journal, new]
permalink: "/posts/how-to-download-assets-from-github-using-a-screen-reader/"
---

GitHub, and by extension, other git based websites are very popular because they all have version control.

I've decided to make this small guide on how to download things from GitHub just in case someone might need a resource somewhere for screen reader users.

This will not be a screen reader guide on how to authenticate with GitHub, upload to GitHub, or anything else related to GitHub.

[Before proceeding with reading this guide, I suggest you brush up on working with GitHub via their desktop program](https://accessibility.github.com/documentation) or [brush up on using GitHub via the command line interface.](https://accessibility.github.com/documentation/guide/cli/)

[Optional, but not required, Git documentation is here, and is kind of like the massive Git explainer](https://git-scm.com/book/en/v2)

Now you are familiar with GitHub, let's talk downloading things from GitHub.

GitHub currently calls downloadable packages assets. The term "asset" is what is used to generically describe anything a project will allow you to download, be that an .EXE file, source code in a ZIP file, or anything else. GitHub is used to manage so many different projects that a term to describe "releases you can download" was needed, and "asset" is that term for now.

I've included graphical instructions but below the GUI instructions, I provide command line instructions.

To explain the GUI bits, I will showcase some GitHub projects I use.

## Main example project pages:

[YT-DLP, a tool to download audio and video from the web.](https://github.com/yt-dlp/yt-dlp)

[The Accessible Markdown editor fork I use.](https://github.com/stefano-pogliani/AME)

And finally, [Pandoc, which is utterly amazing.](https://github.com/jgm/pandoc/)

## Find the releases pages.

To download release packages from a repository, or project, you need to find the releases page. There are multiple ways to get to the releases page.

The easiest, and fastest, way to get to all releases page is to tack on the ending /releases at the end of any project URL. For example, Pandoc  releases URL is this.

https://github.com/jgm/pandoc/releases/

It's always best practice to add /latest to the end of all URLs so you can get to the latest release quickly. [For example, Pandocs latest release URL can be found here](https://github.com/jgm/pandoc/releases/latest)

Over time, I am sure the interface will change, so the most evergreen way I can think of to find the releases is to go straight to the releases URL, but let's say you can't guess the releases URL or don't know that every releases page ends in a /releases ending. How do you get there?

After landing on a main project, or repo, page, Invoke your screen reader's *find command.* Type, releases, then press enter. The releases link will be immediately after the heading results for the moment.

## After getting to the releases page.

Releases for any project are listed in reverse chronological order, most recent release first, and at the end of each release section are one of two things, depending on how the developer has chosen to present Assets:

1. An Asset button that announces as, ""Assets {number} button collapsed." If his is the case, you must activate the button to expand and have the actual list of assets presented.  
2. The asset files list (e.g., the zips or EXEs or whatever is appropriate for the context) that you can download.  The Assets button is set to "auto-expand" in some way.  It's there, but already expanded and the list is visible.

Searching on the word "Assets" is the direct and fastest route to this location.

Most often, for projects with relatively few assets, you will simply have the list of assets showing at the end of each release's section.  For projects with larger numbers of assets, the assets button is used.

Usually, for now, the release items will be in a list after you expand the assets button, so you can find whatever you want to download by navigating via list item.

So  now you know how to download assets via the GUI, let's tackle downloading via CLI.

## A brief intro to GitHub CLI.

If you love the command line the way I love a hunky man’s pecs, there is a way to download assets from the CLI as well. The CLI is my most preferred method of downloading.

In order to download via CLI, you do need [the GitHub command line tool.](https://docs.github.com/en/github-cli/github-cli/about-github-cli) GitHub CLI is a command-line tool that brings pull requests, issues, GitHub Actions, and other GitHub features to your terminal, so you can do all your work in one place.

[The easiest way to get it, I've found, is to install GitHub CLI via Winget.](https://winget.run/pkg/GitHub/cli)

[This getting started CLI guide for screen reader users should get you started](https://accessibility.github.com/documentation/guide/cli/) but you can also [Read the GitHub CLI manual to learn everything you can do.](https://cli.github.com/manual)

I've provided a custom Windows terminal/command line/PowerShell command below that will download GitHub CLI, install it, then authenticate it after enabling some accessibility settings. I've never tried downloading something without an account, so your milage may wildly vary if you don't authenticate with a GitHub account using the CLI.

```
winget install --id Git.Git -e; winget install --id GitHub.cli -e; gh config set accessible_prompter enabled; gh config set accessible_colors enabled; gh config set spinner disabled; gh auth login
```

[After you authenticated your GitHub CLI,](https://cli.github.com/manual/gh_auth_login) now we can download assets!

## Downloading assets via the CLI

[Once you authenticated your Github](https://accessibility.github.com/documentation/guide/cli/) the command to actually download assets is actually all in one command, unless you want to target kinds of files and or versions.

To download the latest of the project, you need to download the source code archive or fetch a particular extension package. There isn't one command to download everything. Because you need to use one or the other, an archive, or a targeted package file extension type, use a command similar to the below command, making sure to swap out the type of release you want to download.

gh release download --archive=EXTENSION, or, --pattern '*.EXTENSION' --repo <[HOST/]OWNER/REPO>

To break this command down a little bit... we're telling GitHub CLI what to download and where to get it.

gh release download tells GitHub CLI what to do.



--archive=EXTENSION, or, --pattern '*.EXTENSION' tell GitHub CLI what to download.

--repo <[HOST/]OWNER/REPO> tells GitHub Cli where to find the assets in question.

## Example CLI download commands.

So, in the case of Pandoc, we would use the Pattern flag to find all Windows installers that are packaged. Pandoc calls its Windows binaries "MSI" extensions, so, the pattern command would look like,

gh release download --pattern '*.msi' --repo jgm/pandoc

If a message comes back saying it can't find any assets, try the below, swapping out, MSI, in the below commands, for any other file extension types. So for example, some alternate patterns to look for are,

--pattern '*.exe'

--pattern '*.msi'

--pattern '*.zip'

You can also download the source code if you use a command like this, making sure to include the --archive tag.

gh release download --archive=zip --repo jgm/pandoc

### What if you wanted a different version?

To get a certain version, you would include the version number as well as the type of thing you are looking for, even if you want the source code. You must keep the --repo flag as before because that tells the client where to fetch. To demonstrate this with Pandoc again, we will include an older version but use the pattern flag to find an older MSI installer.

gh release download 3.9.0.2 --pattern '*.msi' --repo jgm/pandoc

And to demonstrate downloading an older source code archive, we would use a command like the below, keeping the --repo flag as before because that tells the client where to fetch.

gh release download 3.9.0.2 --archive=zip --repo jgm/pandoc

And that's all! There's one more thing before we go, but first, allow me to preach for a second. I know this is not the most intuitive via the CLI. Blame GitHub, not me. There's no one command to download all release assets, yet.

[If you hate the web interface, like me, and wanna release stuff via the GitHub CLI, GitHub developers can use this releases command to upload assets via the CLI as well.](https://cli.github.com/manual/gh_release_create)

[Thanks for reading! If you found this guide helpful, give me money so I can keep writing.](/tip)