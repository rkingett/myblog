@echo off
setlocal enabledelayedexpansion

:: Set the path to the Eleventy project directory
set "userProfile=%USERPROFILE%"
set "documentsFolder=Documents"
set "eleventyProjectFolder=EleventyProject"
set "projectDirectory=%userProfile%\%documentsFolder%\%eleventyProjectFolder%"

:: Set the path to the template file
set "templateFolder=template"
set "templateFile=blog-post.md"
set "templateFilePath=%projectDirectory%\%templateFolder%\%templateFile%"

:: Set the path to the drafts folder
set "draftsFolder=drafts"
set "draftsFolderPath=%projectDirectory%\%draftsFolder%"

:: Check if the drafts folder exists, if not create it
if not exist "%draftsFolderPath%" mkdir "%draftsFolderPath%"

:: Ask the user for the title of the post
set /p title=Please enter the title of your Eleventy post: 

:: Get the current date
for /f "tokens=2 delims==" %%a in ('wmic os get localdatetime /value') do set "dt=%%a"
set "YYYYMMDD=%dt:~0,8%"
set "dateForYaml=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%"

:: Read the content of the template file
set "content="
for /f "delims=" %%i in (%templateFilePath%) do set "content=!content!%%i\n"

:: Replace the placeholders with the user input and current date
set "content=!content:{{TITLE}}=%title%!"
set "content=!content:{{DATE}}=%dateForYaml%!"

:: Define the path to the destination file based on the current date
set "destinationFile=%draftsFolderPath%\%YYYYMMDD%.md"

:: Write the modified content to the destination file
(
    echo !content!
) > "%destinationFile%"

echo File created successfully: %destinationFile%
