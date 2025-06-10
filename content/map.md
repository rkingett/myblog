---
title: Site Map
eleventyNavigation:
  key: Site Map
  order: 5
---

<a href="/feed.xml">Follow the main RSS feed</a> or find posts, pages, and categories/tags below.

<h2>All tags and categories.</h2>

{% include 'tags.njk' %}

<h2>All posts and pages</h2>

This section is organized by last modified. The latest modified post or page will appear at the top.

<ul>
{%- for post in collections.all | reverse -%}
<li><a href="{{ post.url }}">{{ post.data.title }}</a></li>
{%- endfor -%}
</ul>