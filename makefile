# makefile for Robert Kingett's website
# © 2025 Matthew Graybosch <contact@starbreaker.org>
# available under the GNU General Public License v3.0


# we'll want these variables for the rsync command in the "install" target
DST_DIR=_site
SSH_OPTS=-o StrictHostKeyChecking=no
SSH_USER=CHANGE_ME
SSH_HOST=ssh.nyc1.nearlyfreespeech.net
SSH_PATH=/home/public


#
# DEFAULT ACTION
# make always treats the first target as the default
#
build: dep  ## build website with eleventy
	npx @11ty/eleventy


#
# ALTERNATE BUILDS
# I pulled these out of package.json
#
build-nocolor: dep  ## build using eleventy, without color
	npm run build-nocolor

build-ghpages: dep  ## build using eleventy for GitHub Pages
	npx @11ty/eleventy --pathprefix=/myblog/


#
# LOCAL SERVER
# You can run one of these to test against a local version
#
start: dep ## preview your website on http://localhost:8080
	npx @11ty/eleventy --serve --quiet

start-ghpages: dep ## local preview for GitHub Pages
	npx @11ty/eleventy --pathprefix=/myblog/ --serve --quiet


#
# DEBUGGING
# Need to troubleshoot a broken build? Try these make targets
#
debug: dep  ## run Eleventy in debugging mode
	npm run debug

debugstart: dep  ## run Eleventy in debugging mode with local preview
	npm run debugstart

benchmark: dep  ## run Eleventy in benchmarking mode
	npm run benchmark


#
# DEPLOYMENT
# If we're going to deploy this website to Nearly Free Speech,
# we can do the job with rsync over SSH.
#
install:  ## build and deploy the site to your hosting provider
	rsync --rsh="ssh ${SSH_OPTS}" \
		  --delete-delay \
		  -acvz $(DST_DIR)/ ${SSH_USER}@${SSH_HOST}:${SSH_PATH}


#
# PREREQUISITES
# #Every website building tool built on Node.js
# has lots of dependencies. This make target handles them.
#
dep: package.json  ## install Node.js project dependencies
	npm install


help:  ## show help for make targets
	@clear
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[34m%-15s\033[0m %s\n", $$1, $$2}'
