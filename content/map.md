---
title: Site Map
permalink: /map/
redirect_from: archive
eleventyNavigation:
  key: Site Map
  order: 1
---

<a href="/feed.xml">Follow the main RSS feed</a> or find posts, pages, and categories/tags below.

<h2>All tags and categories.</h2>

{% include 'tags.njk' %}

<h2>All Pages</h2>

<ul>
{%- for item in collections.page -%}
	<li>
		<a href="{{ item.url }}">
			{%- if item.data.title -%}
				{{ item.data.title }}
			{%- else -%}
				{{ item.url }}
			{%- endif -%}
		</a>
	</li>
{%- endfor -%}
</ul>

<h2>All Posts</h2>

<ul>
{%- for item in collections.posts | reverse -%}
	<li>
		<a href="{{ item.url }}">
			{%- if item.data.title -%}
				{{ item.data.title }}
			{%- else -%}
				{{ item.url }}
			{%- endif -%}
		</a>
	</li>
{%- endfor -%}
</ul>