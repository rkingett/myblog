---
title: Tags
redirect_from: tags
permalink: /posts/tags/
---

<ul>
{% for tag in collections | getKeys | filterTagList %}
	{% set tagUrl %}/posts/tags/{{ tag | slugify }}/{% endset %}
	<li><a href="{{ tagUrl }}" class="post-tag">{{ tag }}</a></li>
{% endfor %}
</ul>
