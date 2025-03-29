---
title: All posts.
eleventyNavigation:
  key: Updates
  order: 3
---

My post archive is below, from newest to oldest! I'd encourage you to <a href="/feed.xml">Follow the main RSS feed</a>

<h1>Post Archive</h1>

{% set postslist = collections.posts %}
{% include "postslist.njk" %}