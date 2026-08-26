---
title: "How to convert Markdown to Shun manuscript format"
date: 2026-08-25T10:17:48.000Z
permalink: /posts/shun/
redirect_from: /posts/5926
tags:
  - blog and journal
  - guides
---

This has been updated with better links, better commands, and some extra optional advanced configuration tutorials.

Notes about writing manuscripts in Markdown are after the conversion tutorials.

[You can also find other Shun Manuscript templates on this website](https://pandoc-templates.org/)

## Introduction.

[I love Markdown.](https://www.markdownguide.org/basic-syntax) I love it so much that I’ve adapted my whole workflow around it! [From writing fiction podcast scripts](/posts/5913) to drafting blog posts, it’s just pure plain text, and I love it because it’s so portable and universal.

I wanted to write Markdown manuscripts and then convert them to [Shun format industry standard documents.](https://www.shunn.net/format/) In short, I’ve figured out how to do it, but it’s a very involved process. If just opening up Word or otherwise works for you, do that. Seriously, don’t try to adopt this workflow unless you really, really, love writing in Markdown as much as I do.

Because I’m a Windows user, the below is going to be Windows focused.

I write all my stuff in Markdown and then convert it to other formats using Pandoc. This way, my work is very portable, and I don’t have to transfer every single Macro to new computers. Text files are much smaller than document files so they don’t take up space in my cloud drives.

## Requirements.

The below, though, will definitely take some time to set up. It requires you [knowing Markdown basics,](https://www.markdownguide.org/basic-syntax) being comfortable with using the command line and downloading things from the internet and installing programs, as well as [working with styles and editing styles in Microsoft Word.](https://support.microsoft.com/en-us/office/customize-or-create-new-styles-d38d6e47-f6fc-48eb-a607-1eb120dec563)

[JAWS tutorials for Microsoft Office are here](https://www.freedomscientific.com/category/webinar/microsoft-office/) and [NVDA tutorials for Word are here](https://www.nvaccess.org/product/microsoft-word-training-for-nvda-ebook/)

[A Microsoft Word Styles tutorial is here](https://support.microsoft.com/en-us/word/customize-or-create-new-styles)

[Getting started with Powershell is a great basic tutorial, enough so you understand what we will be doing below.](https://learn.microsoft.com/en-us/powershell/scripting/learn/ps101/01-getting-started?view=powershell-7.6)

For the command line, we’re going to use PowerShell for this because it’s more versatile.

[If you’d rather use templates for Word instead of writing in Markdown, Shun made templates](https://www.shunn.net/format/templates.html) and [I made modern versions of his templates for Word](https://github.com/rkingett/writertools/tree/8a7a4cda92ad337bb5efecb512643a681b179fa8/Microsoft%20Word%20related)

Let’s get started!

## Downloading Pandoc.

[Before we do anything, download Pandoc for your operating system and install it.](https://pandoc.org/installing.html)

[Then, make your Pandoc data directory folder.](https://pandoc.org/MANUAL.html#option--data-dir)

Alternatively, you can run this command in Windows Powershell to install Pandoc and make a data directory folder, something you will need.

```
winget install -e --id JohnMacFarlane.Pandoc; New-Item -Path "$env:APPDATA" -Name "pandoc" -ItemType Directory; CD CD $env:APPDATA\pandoc
```

If you use Chocolatey, the below command will install it for you.

```
choco install pandoc; New-Item -Path "$env:APPDATA" -Name "pandoc" -ItemType Directory; CD CD $env:APPDATA\pandoc
```

After you install Pandoc, restart your computer. Now, you should be good to go.

## Use my Pandoc templates instead of making your own

[Download my Pandoc reference templates here](https://github.com/rkingett/writertools/archive/refs/heads/main.zip) or make your own below.

If you want one command that will download all of my templates, use the below command to download Pandoc, make a Pandoc data folder, then download all the pre made templates into that folder.

```
winget install JohnMacFarlane.Pandoc; $d="$env:APPDATA\pandoc"; if(!(Test-Path $d)){New-Item -ItemType Directory -Path $d | Out-Null}; @("https://github.com/rkingett/writertools/blob/8a7a4cda92ad337bb5efecb512643a681b179fa8/Pandoc%20templates/story.docx", "https://github.com/rkingett/writertools/blob/8a7a4cda92ad337bb5efecb512643a681b179fa8/Pandoc%20templates/novel.docx", "https://github.com/rkingett/writertools/blob/8a7a4cda92ad337bb5efecb512643a681b179fa8/Pandoc%20templates/ShunNewPagesLibreOfficeTemplate.odt") | ForEach-Object { Invoke-WebRequest -Uri "$_`?raw=true" -OutFile (Join-Path $d ([System.Web.HttpUtility]::UrlDecode((Split-Path $_ -Leaf)))) }
```

[You can also download my  whole templates directory here and move them as you see fit, later.](https://github.com/rkingett/writertools/archive/refs/heads/main.zip)

After running the above command, all the templates are in [your Pandoc data directory](https://pandoc.org/MANUAL.html#option--data-dir) so you only need to convert stuff with commands like the below.

If you rename something, reference.docx, you won't need to specify the template when converting. You could just use a command like this command.

```
pandoc -s Draft.md -o Book.docx
```

To use a particular template in question, reference it directly in your convert command, like the below. The below automatically looks in [your Pandoc data directory](https://pandoc.org/MANUAL.html#option--data-dir)

```
pandoc -s Draft.md --reference-doc=$env:APPDATA\pandoc\novel.docx -o Book.docx
```

Otherwise, make the templates yourself below!

## Creating your own Shun Manuscript templates.

The below sections will walk you through, step by step, on making your own Shun Manuscript Pandoc reference templates.

[If you don't want to go through the process of making your own Shun reference templates, download all of my templates, here](https://github.com/rkingett/writertools/archive/refs/heads/main.zip) and then [unzip them into your Pandoc data directory](https://pandoc.org/MANUAL.html#option--data-dir)

This method requires a lot of setting up, but it’s going to be worth it in the end. You will only need to set this up once. After you set it up, you can just make copies of your reference document.

[First, make sure your Pandoc data directory is created](https://pandoc.org/MANUAL.html#option--data-dir)

then, [get acquainted with Pandocs commands with this getting started page.](https://pandoc.org/getting-started.html) All commands start with -Pandoc, and are usually one line for this tutorial.

## Pandoc reference files.

The first thing we’re going to need to do is make a reference file for Microsoft Word. When exporting into a Word format, Pandoc references templates so it knows how to style your outputs.

It can’t reference any random template, though. It needs to reference a template based on its structure. This is why we need to make our own template.

## Navigating to make your reference template.

[In order for this to work, we need to make a Pandoc User Data directory folder.](https://pandoc.org/MANUAL.html#option--data-dir) after the Pandoc installation.

Here is a Powershell command that makes a reference document after making a user data directory, the below command will first make a user data directory, then go into the directory, then make a reference file.

```
New-Item -Path "$env:APPDATA" -Name "pandoc" -ItemType Directory; CD CD $env:APPDATA\pandoc; pandoc -o reference.docx --print-default-data-file reference.docx
```

You can also do this step by step below.

### Making a user data directory in Windows, step-by-step GUI version.

Once Pandoc is installed, Open up, Run, by pressing, Windows key plus R.

After the Run dialog opens, put this.

```
%APPDATA%
```

Press enter.

Press, Control, Shift, N, to make a new folder inside of this AppData folder. Call it Pandoc

Now, open up Powershell and the below command will first navigate to your Pandoc directory you just created, then make a reference document, all with one command.

```
CD $env:APPDATA\pandoc; pandoc -o reference.docx --print-default-data-file reference.docx
```

Or, open up Powershell in this user data directory with Windows Explorer.

Open the run dialog, then type,

`%APPDATA%\pandoc`

Next, to open Powershell with windows explorer, press, Alt D, Delta, then type, Powershell, all one word, and then hit enter.

After opening up powershell above or doing it first then navigate to where your Pandoc user data folder is or any directory where you want to store templates. To navigate to the Pandoc user data folder quickly, you’d do this,

```
CD $env:APPDATA\pandoc
```

CD in command line speak means, change directory. If you have an external hard drive, you’d first enter that external hard drive by typing,

CD DRIVELETTER, where DRIVELETTER is the letter of your actual drive.

If you keep everything on your computer, you need to enter the full path after the, CD, command. For example, to get to the desktop, you could use,

```
CD $home\Desktop
```

Alternatively, you can open up a powershell window at any location from Windows explorer.

To open powershell at any location, navigate to the folder you want to store your templates and manuscripts in. It works best if everything is in one folder, but we’ll worry about that later.

In the address bar, type,

Powershell

And hit enter. No spaces should be between power, and shell.

Now that powershell is open where you want to have it, Let’s make a reference document.

## Generating a generic Pandoc reference document.

To make a reference document, you’d type,

```
pandoc -o reference.docx --print-default-data-file reference.docx
```

To make a LibreOffice reference document,

```
pandoc -o reference.odt --print-default-data-file reference.odt
```

After your reference document is created, open up your reference document in Word or LibreOffice Writer.

## Editing styles in Microsoft Word.

In the past, I had you edit one style at a time, but editing the, normal style, will be the fastest way, leaving us to only change some other things such as changing our heading styles.

[Use this guide to get acquainted with styles and editing styles before continuing.](https://support.microsoft.com/en-us/office/customize-or-create-new-styles-d38d6e47-f6fc-48eb-a607-1eb120dec563) so that the  line spacing is double, first line is indented 0.5 inches, and the font is 12 PT, Times New Roman.

The easiest way to edit the styles with a keyboard is to do the following.

After your reference document is open in word,

1. Press control+alt+shift+s to open the "Styles" pane.
2. Press the up and or down arrow until you find, normal.
3. Press, either, your applications key, if you have one, or, Shift F10. A context menu should open up.
4. Arrow down to, Modify, then press enter.

If your cursor is on a style in the document, control+alt+shift+s to open the "Styles" pane should have you landing on that style in the styles pane.

## Normal style attributes to change.

Once the Modify style dialog box is open, tab to the font ComboBox. Change it to Times New Roman.

Tab to change the size to size 12.

Press, Alt O, to open the format menu. Go down and select, paragraph.

Change the below attributes.

• Font: Times New Roman, 12 pt.
• Alignment: Left-aligned (do not justify Shunn manuscripts).
• Spacing Before: 0 pt.
• Spacing After: 0 pt.
• Line Spacing: Double.
• First Line Indent: 0.5 inches (Set via Alt + S to skip to the special combo box, then arrow down to select, first line. Tab and enter 0.5 in that edit field if it is empty.

Tab to the, okay, button. Press enter. You should land on another okay button. Remember, our modify dialog is still open, so we need to close this one too by pressing enter on, okay.

[After editing the Normal Style,](https://support.microsoft.com/en-us/office/customize-or-create-new-styles-d38d6e47-f6fc-48eb-a607-1eb120dec563) save your edited reference document before we move on to fixing the remaining styles.

## Fixing our heading styles in our reference document.

Because we edited the, normal, style, now we need to fix our headings.

If you didn't close your document, press F6, to navigate to the styles. Arrow up and down until you get to, heading 1.

Press your applications key, or Shift F10, to open the context menu. Arrow down to the modify option and press enter to modify the style the same way we modified the normal style.

### Heading 1 style attributes to change.

* Font. Times new Roman.
* Size. 12.
* Alignment. Centered.
* Spacing Before: 144 pt. This makes the chapter heading start a few inches down from the top, which looks nice.
* Spacing After: 24 pt. This puts a clean break between the heading style and the text body.
* Line spacing. Double.
* Page Break Before: Checked (Found under the Line and Page Breaks tab). To switch tabs, press Control tab.

## Heading level 2 values to change.

* Font. Times new Roman.
* Size. 12.
* Alignment. Centered.
* Space Before: 24 pt (Inserts exactly one blank double-spaced line above the sub-heading).
* Space After: 24 pt (Inserts exactly one blank double-spaced line below the sub-heading).
* Line Spacing: Double.

## Changing the top headers on pages.

Having the page headers nicely done will help out editors and agents that read on electronic devices.

### Step 1: Isolate the First Page Header

Before typing anything, you must tell Word to leave the first page blank.

1. Press Alt + N, then H, then E to open the header area. Your screen reader will announce that you are in the header.
2. Press Alt + J, to open the Header options ribbon menu.
3. Press, A, to enable, different first pages. Your screen reader will say, different first page on.
4. Press page down until you hear "header section, page 2, or "Header - Section 1" or "Header page 2"

### Step 2: Set Right Alignment and Add Your Last Name

Shunn format requires the header to sit on the right side of the page.

1. Press Ctrl + R to right-align the paragraph. Your screen reader may say "Align Right" or confirm the change.
2. Type your Last Name followed by a forward slash and a space.

For example

Smith / 

### Step 3: Insert the Automated Title Property

Instead of typing your book title manually, insert a field that updates automatically when you convert from Markdown.

1. Press Alt + N to open the Insert tab.
2. Press Q, then A (or use your screen reader to search for Quick Parts in the Text group).
3. Press Arrow Down to highlight Document Property and press Right Arrow to expand the menu.
4. Arrow down until you hear Title and press Enter.
5. Word inserts a dynamic field block. Press Right Arrow once to move your cursor past this field box.
6. Type a space, a forward slash, and another space. (Your text line now should read: Last Name / [Title Field] / ).

### Step 4: Insert the Automated Page Number Field

Why type page numbers manually when Word can automatically assign them. More than not, people will want page numbers so it is best to add them now.

1. Make sure you inserted a, space, then a, slash, after we inserted our title field.
2. Press Alt + Shift + P. This is the global Microsoft Word shortcut to insert a dynamic page number field instantly at your cursor location.
3. Your screen reader won't say anything but we can review it by pressing the left and right arrow keys. You should hear the current page number (which should be "2").

###Step 5: Verify and Exit

1. Press Up Arrow or Home to read the line with your screen reader. It should read exactly like this: YourLastName / Your Book Title / 2
2. Press Page Up to check the first-page header. Ensure your screen reader says it is completely blank.
3. Press Escape to exit the header view and return to editing your main document template.

## Conclusion.

Now be sure to save it! You are done! YAY!

You can name it, reference.docx, if you want Pandoc to use this template by default.

## Commands to use the templates.

Regardless of which method you picked, [downloading my templates](https://github.com/rkingett/writertools/archive/refs/heads/main.zip) or making your own via styles, now you need to use them.

If you haven't done so already, make your life a billion times easier by [putting all the templates in your Pandoc data directory](https://pandoc.org/MANUAL.html#option--data-dir)

[After the templates are in the Pandoc data directory,](https://pandoc.org/MANUAL.html#option--data-dir) now it's time to use them!

### How to specify reference templates.

If you changed the name of your reference document, you will need to tell Pandoc what reference document to use every time.

We would do this by directing Pandoc to it with this addition.

```
--reference-doc=ChangeName.docx
```

Since I am on Windows, I always just specify the Pandoc data directory anyway, like this in Powershell.

```
--reference-doc=$env:APPDATA\pandoc\novel.docx
```

### Conversion commands.

After you've written something in Markdown, open Powershell.

There's two ways to tell Pandoc what to convert, where to convert. The easiest way is to provide the full input file and output files along with paths.

Let's say you keep everything in your My Documents folder. The below command will tell Pandoc to go into your documents folder and convert the file.

```
pandoc -s "$home/documents/Draft.md" --reference-doc=$env:APPDATA\pandoc\novel.docx -o "$home/documents/Book.docx"
```

If you renamed a reference document as, reference.docx, the command doesn't need to tell Pandoc what reference document to use. Pandoc will use the 'reference.docx' template by default.

```
pandoc -s "$home/documents/Draft.md" -o "$home/documents/Book.docx"
```

But what if you wanted to navigate to the directory first.

We can change directories in Powershell with, CD.

The easiest way is to find your folder, hit your applications key, and then click, copy as path.

Then, now that path is copied to the clipboard, just type, CD, in Powershell, then hit paste, then enter.

Now we are in your directory, you would use a command like the below because we are already in our desired directory, so no need to specify the full file paths

```
pandoc -s Draft.md --reference-doc=$env:APPDATA\pandoc\novel.docx -o Book.docx
```

If you renamed your template file, reference.docx, you don't have to tell Pandoc what reference template to use. We can just use a command like the below, excluding the, reference doc = portion.

```
pandoc -s Draft.md -o Book.docx
``` 

## Extra tutorials and optional enhancements.

## Editing styles in LibreOffice Writer.

I am a Word user more than a LibreOffice user but the below should be a decent guide on editing the style in the reference document.

To edit your [LibreOffice styles for writer,](https://help.libreoffice.org/6.2/en-US/text/swriter/01/05130000.html?&DbPAR=WRITER&System=WIN) do the following with the keyboard.

[Learn about styles in Writer here.](https://help.libreoffice.org/6.2/en-US/text/swriter/01/05130000.html?&DbPAR=WRITER&System=WIN) the important style types are the paragraph styles.

After your ODT reference file is created, open the reference file in LibreOffice Writer.

Press, Alt, P, Papa, to open the edit style dialog box.

At the top, you should see tabs. Pressing Control Tab to cycle through these should work but if it doesn’t work for you, shift tab until your screen reader focus lands on the tab row at the top.

Switch to the, indents and spacing, tab.

tab until you hear, `First line: 0.00″`

Change the numeral to 0.50. It should now say, `First line: 0.50″`

Tab until you hear, line spacing option pane ComboBox. Change it to double.

Apply the changes, and then save your reference document.

The font style and font size are already where they should be, but if you wanted to edit other styles to match your newly edited style, you can edit all styles by pressing F11.

If editing other styles, I’d change the, first line, style to match the edited paragraph style. If you don’t want to edit other styles, you can save the reference document and close LibreOffice.

## Creating new Chapter files.

I often times split longer projects up into separate files. I am a lazy person though so I always have the computer make me a batch of files at one time.

```
1..10 | ForEach-Object { New-Item ('Chapter{0:D2}.md' -f $_) }
```

## Sorting and renaming multiple files for Pandoc.

If you made your files by hand, instead of having the PC make new files for you, sometimes they can get out of hand and if we try to convert stuff without the order correct, Pandoc won't know what chapter comes first in the sequence so we need to make it easier for Pandoc to know what comes before what.

The below command will sort all Markdown files.

```
Get-ChildItem *.md | Sort-Object CreationTime | ForEach-Object -Begin { $i = 1 } -Process { Rename-Item $_.FullName -NewName (("{0:D3} - {1}" -f $i, $_.Name)) ; $i++ }
```

The below will change all text documents to .MD files and then sort them.

```
Get-ChildItem *.txt | Sort-Object CreationTime | ForEach-Object -Begin { $i = 1 } -Process { $newName = "{0:D3} - {1}" -f $i, ($_.BaseName + ".md") ; Rename-Item $_.FullName -NewName $newName ; $i++ }
```

The below sorts your Markdown files if you did not use any numbering at all.

```
Get-ChildItem *.md | Sort-Object CreationTime | ForEach-Object -Begin { $i = 1 } -Process { $cleanName = $_.Name -replace '^\d+\s*-\s*\d+\s*-\s*|^\d+\s*-\s*', ''; $newName = "{0:D3} - {1}" -f $i, $cleanName; Rename-Item $_.FullName -NewName $newName; $i++ }
```

## Merging multiple files into one book with your Shun template.

Before reading the below, make sure that *nothing else* is located in the chapter hub, the place where all your chapter files will go.

The easiest way I’ve found of merging multiple files into one book is to [put your custom reference document in the User data directory](https://pandoc.org/MANUAL.html#option--data-dir) so that Pandoc uses the document every time it converts to Docx.

If you want to split your chapters up into separate files, you need to specify each input file name, in order, so that it will merge all the files into one document in order.

The easiest way of making sure multiple files stays in order for Pandoc is to name all your files something like,

'''
01Prologue.md
```

Make sure files start with a numbered sequence, like...

01

001

0001

00001

Let’s say you have a folder called Book. Inside of that folder, you have Markdown files. The below command works well if all files are in the same folder, named and sorted correctly.

```
pandoc -s (Get-ChildItem *.md).FullName --reference-doc=$env:APPDATA\pandoc\novel.docx -o Book.docx
```

If you have a directory of other file types that you want to merge into one Markdown file, use the below command.

```
pandoc (Get-ChildItem _._).FullName --wrap=none -o final.md
```

Alternatively, you can use the below command to rename all files in a directory sequentially by date, then concatenate, or merge, all the reorderd files in a directory. The below Powershell command will rename all files in a directory sequentially by date created and then merge them with Pandoc.

```
Get-ChildItem _._ | %{Rename-Item $ _-NewName ('{0}{1}' -f $_.LastWriteTime.toString("yyyyMMdd-hhmmss"), $_.Extension)}; pandoc (Get-ChildItem _._).FullName --reference-doc=$env:APPDATA\pandoc\novel.docx -o final.docx
```

The semicolon in the above is intentional. The above command performs two commands one after the other.

Finally, alternatively, you can also list them one at a time. To list them all one at a time, make sure you specify each text file in the command. For example,

```
pandoc -s -o Book.docx ch1.md ch2.md ch3.md ch4.md ch5.md
```

## Using a manifest to convert multiple files.

I like manifests because if you have a lot of folders inside of a chapters folder, as an example, a manifest is the easiest way to keep all of that clean and in order.

I typically have a project folder, and then have characters in 1 folder, chapters in another, and notes in a notes folder inside of that project folder.

The below will check for all files in a Chapters folder, make the manifest, then compile based off that manifest.

To one command one at a time, run the command before the, &&

```
(Get-ChildItem -Path .\chapters -Recurse -File -Filter *.md | Sort-Object DirectoryName, Name).ForEach({ "/chapters/$($_.FullName -replace '^.*\\chapters\\', '' -replace '\\', '/')" }) | Out-File -FilePath .\manifest.txt -Encoding utf8 && pandoc @manifest.txt -s --file-scope --reference-doc=$env:APPDATA\pandoc\novel.docx -o "Book.docx"
```

## Converting multiple DOCX files into Markdown.

Just in case you wanted to convert any directory of Docx files to Markdown, and the order doesn’t matter, use the below command after navigating to the directory containing the files in power shell.

```
gci -r -i *.docx |foreach{$md=$_.directoryname+"\"+$_.basename+".md";pandoc -f docx --wrap=none -s $_.name -o $md}
```

The above will make Markdown versions of your Docx files. It won’t merge all of them though, only make an MD version of your Docx files in the folder.

If you wanted to merge, or concatenate, all files in a directory with Powershell, make sure the files are named in sequential order.

If you want to rearrange and rename all files in a directory then merge them with Pandoc, use the below command, including the semicolon.

```
Get-ChildItem _._ | %{Rename-Item $ _-NewName ('{0}{1}' -f $_.LastWriteTime.toString("yyyyMMdd-hhmmss"), $_.Extension)} && pandoc (get-item _._).FullName --wrap=none -o final.md
```

I personally prefix all of mine like this, 00.

It reads like this.

001

002

003

After all files are where you need them to be, merge all files in powershell with this command.

```
pandoc (get-item _._).FullName --wrap=none -o final.md
```

## Using prosegrinder's scripts on Windows.

[This directory of prosegrinder's scripts does some extra things, such as splitting chapters and otherwise.](https://github.com/prosegrinder/pandoc-templates)

[First, download the latest zipped script directory from this page.](https://github.com/prosegrinder/pandoc-templates/archive/refs/heads/main.zip)

Extract the folder to a folder where you’ll remember it.

Open up powershell and then navigate to this folder, the unzipped script folder.

Alternatively, you can navigate there using Windows Explorer. Navigate to the folder and then type, powershell, in the address bar.

Inside this folder, you can change the test folder to work, or BookDraft, all one word, or anything you want. The simplest thing to do is just use the test folder to store your manuscripts and short stories.

Inside the test folder, you’ll find a short folder and long folder.

Go into each folder, open up each first MD file in notepad, and edit the YAML data at the top. You’ll only need to do this once. Change all contact information to your own contact information.

After you change your contact information and delete the sample text below the YAML data, save the documents and then close the files after deleting all the sample text below the YAML data.

Now, all you need is the below commands. You can even split your book up into separate documents and merge them all with one command.

All of the below commands will output your output files to your desktop.

To convert single files, you’d use the command below, making sure to tell Pandoc where your manuscript file is.

If you wrote everything in one long file, use the below command, replacing name’s as needed.

```
.\bin\md2short.ps1 -overwrite -modern -output $env:USERPROFILE/Desktop/Book.docx './test/long/Book.md'
```

If you created a short story, use the below command, replacing name’s as needed.

```
.\bin\md2short.ps1 -overwrite -modern -output $env:USERPROFILE/Desktop/ShortStory.docx './test/short/story.md'
```

With this script, you can merge all files in a folder in order. When saving files to a folder, or renaming files, make sure to save the files with sequential numbers. Like this,

0010 intro.

0020 Start.

0030 END.

The important thing is to have the numbers at the beginning the same length, and make sure they are in sequential order.

For longer projects with multiple chapters, after all chapters have name’s in sequential order, use the below code.

```
.\bin\md2long.ps1 -overwrite -modern -output $env:USERPROFILE/Desktop/Book.docx './test/long/*.md'
```

## Convert DOCX to Markdown.

If you wanted to convert a file to plain text and or markdown, use the below command. Even if you type Markdown syntax into a plain text file without the MD extension, Pandoc will still convert it correctly later.

```
pandoc -s draft.docx --output draft.md --wrap=none
```

## Working with track changes in plain text.

There might be cases where you need to work with track changes but you want track changes to work in your text editor.

I explain in greater detail about this [in my plain text workflow explanation](/posts/6121) but if you just want some commands to use, use the below.

`pandoc -s draft.docx --output draft.md --wrap=none --track-changes=all`

The above command prints all suggestions and comments, but does not accept or reject anything.

If I want to accept everything and just read the changed output as plain text, I use,

`pandoc -s draft.docx --output draft.md --wrap=none --track-changes=accept`

The above accept command doesn’t include comments in the output so if I want to read comments as plain text but exclude all the suggestions, I accept all suggested changes in Microsoft Word by pressing, accept all and stop tracking, in the document. I then save and close the document. With Pandoc, I then put,

```
pandoc -s draft.docx --output draft.md --wrap=none --track-changes=all
```

## Other resources.

* [You can also find other Shun Manuscript templates on this website](https://pandoc-templates.org/)
* [This other tutorial has reference files for LibreOffice](https://www.autodidacts.io/convert-markdown-to-standard-manuscript-format-odts-docs-and-pdfs-with-pandoc/)

## Some notes about writing manuscripts in Markdown.

Your chapters are going to be headings, so, if you want to make a new chapter heading, you’d just write, either of the below depending on your preference.

If you want to make all chapters a heading level 1, use one `#`

If you want chapters to be heading level 2, use two `##`

For example, if you wanted all chapters to be level 1 headings, you’d write,

`# Chapter 1.`

If you wanted all chapters to be heading 2, you would write it like this,

`## chapter 1.`

To automatically convert "dumb" quotes into "smart" quotes, as well as turning fake em-dashes — the kind made with two hyphens — into real em-dashes (—), and turning three periods (…) into ellipse, add the below to any of the above commands for outputting books and other documents,

`--smart`

I hope this helped someone! It can take a lot to set up, but when you do get it set up, you can just write in plain text, and convert it to a beautiful, formatted, document in seconds!
