---
title: Archive by last updated.
---

<h1>Posts and pages, last modified.<h1>

<ul>
{%- for post in collections.all | reverse -%}
<li><a href="{{ post.url }}">{{ post.data.title }}</a></li>
{%- endfor -%}
</ul>