---
title: Site Map
eleventyNavigation:
  key: Site Map
  order: 2
---

TODO

Pages, not posts, and tags

{%- for page in collections.all %}
{% set absoluteUrl %}{{ page.url | htmlBaseUrl(metadata.url) }}{% endset %}

- [{{ page.data.title }}]({{ absoluteUrl }})
  {%- endfor %}

<h2>All tags and categories.</h2>

<ul>
{% for tag in collections | getKeys | filterTagList %}
	{% set tagUrl %}/posts/tags/{{ tag | slugify }}/{% endset %}
	<li><a href="{{ tagUrl }}" class="post-tag">{{ tag }}</a></li>
{% endfor %}
</ul>