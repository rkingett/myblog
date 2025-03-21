---
title: Site Map
eleventyNavigation:
  key: Site Map
  order: 2
---

<a href="/feed.xml">Follow the main RSS feed</a> or find posts, pages, and categories/tags below.

<h2>All tags and categories.</h2>

<ul>
{% for tag in collections | getKeys | filterTagList %}
	{% set tagUrl %}/posts/tags/{{ tag | slugify }}/{% endset %}
	<li><a href="{{ tagUrl }}" class="post-tag">{{ tag }}</a> ({{ collections[tag].length }})</li>
{% endfor %}
</ul>

<h2>All posts and pages</h2>

This section is organized by last modified. The latest modified post or page will appear at the top.

<ul>
{%- for post in collections.all | reverse -%}
<li><a href="{{ post.url }}">{{ post.data.title }}</a></li>
{%- endfor -%}
</ul>