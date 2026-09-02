---
title: Site Map
redirect_from: archive
eleventyNavigation:
  key: Site Map
  order: 5
---

<a href="/feed.xml">Follow the main RSS feed</a> or find posts, pages, and categories/tags below.

<h2>All tags and categories.</h2>

{% include 'tags.njk' %}

<h2>All posts and pages</h2>

The below list will list all the pages first, then it will list the posts.

<ul>
{%- for post in collections.all | reverse -%}
<li><a href="{{ post.url }}">{{ post.data.title }}</a></li>
{%- endfor -%}
</ul>

<h2>Backup list</h2>

This is just in case the above breaks, and is orgonized from earliest to latest.

<ul>
{%- for post in collections.all -%}
 <li><a href="{{ post.url }}">{{ post.data.title }}</a></li>
{%- endfor -%}
</ul>