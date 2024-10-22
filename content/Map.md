---
permalink: map.html
eleventyExcludeFromCollections: false
---
# Tag archive.

<ul>
{% for tag in collections | getKeys | filterTagList %}
	{% set tagUrl %}/tags/{{ tag | slugify }}/{% endset %}
	<li><a href="{{ tagUrl }}" class="post-tag">{{ tag }}</a></li>
{% endfor %}
</ul>

<h1>Pages.</h1>

<ul>
	{%- for entry in collections.all %}
	<li><a href="{{ entry.url }}"><code>{{ entry.url }}</code></a></li>
	{%- endfor %}
</ul>