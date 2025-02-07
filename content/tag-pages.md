---
pagination:
  data: collections
  size: 1
  alias: tag
  filters: ["all", "posts"]
eleventyExcludeFromCollections: true
eleventyComputed:
  title: "Tagged '{{ tag }}"
  permalink: "/posts/tags/{{ tag | slugify }}/"
---

<h1>Tagged “{{ tag }}”</h1>

{% set postslist = collections[ tag ] %}
{% include "postslist.njk" %}

<p>See <a href="tags.njk">all tags</a>.</p>
