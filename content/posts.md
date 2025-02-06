---
title: Recent posts
eleventyNavigation:
  key: Updates
  order: 1
---

<h1>Post Archive</h1>

{% set postslist = collections.posts %}
{% include "postslist.njk" %}
