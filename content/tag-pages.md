---
pagination:
  data: collections
  size: 1
  alias: tag
  filters: ["all", "posts"]
eleventyExcludeFromCollections: true
eleventyComputed:
  title: "Tagged “{{ tag }}”"
  permalink: "/posts/tags/{{ tag | slugify }}/"
  tagFeed: "/posts/tags/{{ tag | slugify }}/feed.xml"
---

{% set postslist = collections[ tag ] %}
{% include "postslist.njk" %}

See <a href="/posts/tags">all tags</a>.

Subscribe to <a href="/posts/tags/{{ tag | slugify }}/feed.xml">this tag's RSS feed</a>.
