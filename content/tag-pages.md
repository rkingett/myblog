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

<a href="/posts/tags/{{ tag | slugify }}/feed.xml">Follow the {{ tag }} tag via RSS feed</a> or <a href="/feed.xml">Follow the main RSS feed</a>

[Or follow via email here.](/follow)

{% set postslist = collections[ tag ] %}
{% include "postslist.njk" %}

<h1>Other tags and feeds.</h1>

See <a href="/posts/tags">all tags</a>.

<a href="/posts/tags/{{ tag | slugify }}/feed.xml">Follow the {{ tag }} tag via RSS feed</a> or <a href="/feed.xml">Follow the main RSS feed</a>