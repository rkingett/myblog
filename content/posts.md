---
title: All posts.
eleventyNavigation:
  key: Updates
  order: 3
---

My post archive is below, from newest to oldest! I'd encourage you to <a href="/feed.xml">Follow the main RSS feed</a>

<a href="/follow">Other ways to follow me</a>

<h1>Post Archive</h1>

{% set postslist = collections.posts %}
{% include "postslist.njk" %}