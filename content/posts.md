---
title: Recent posts
eleventyNavigation:
  key: Updates
  order: 3
---

<h1>Post Archive</h1>

{% set postslist = collections.posts %}
{% include "postslist.njk" %}
