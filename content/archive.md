---
title: Archive by last updated.
---

# New page notice.

[The site map is more updated than this page is,](/map) so you may want to check there before looking here.

<h2>Posts and pages, last modified.</h2>

<ul>
{%- for post in collections.all | reverse -%}
  <li{% if page.url == post.url %} aria-current="page"{% endif %}><li><a href="{{ post.url }}">{{ post.data.title }}</a></li>
{%- endfor -%}
</ul>

<h2>Backup list<h2>

<ul>
{%- for post in collections.all | reverse -%}
<li><a href="{{ post.url }}">{{ post.data.title }}</a></li>
{%- endfor -%}
</ul>